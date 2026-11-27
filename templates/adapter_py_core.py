import json
from re import Pattern, compile

_EMPTY_JSON: str = "{}"


def _usage() -> None:
    raise SyntaxError("Mandatory: WITH CONNECTION_NAME = <string>")


def adapter_call(jsonRequest: str) -> str:
    requestObject: dict = json.loads(jsonRequest)
    requestType: str = requestObject["type"]

    if requestType == "createVirtualSchema":
        return call_create_schema(requestObject)
    elif requestType == "dropVirtualSchema":
        return jsonRequest
    elif requestType == "refresh":
        return call_refresh(requestObject)
    elif requestType == "getCapabilities":
        return call_capabilities(requestObject)
    elif requestType == "pushdown":
        return call_pushdown(requestObject)
    else:
        raise RuntimeError(f"Unsupported request type '{requestType}'")

    raise RuntimeError(jsonRequest)
    # return "Hello World"    

from collections import namedtuple

ObjectDescriptor = namedtuple('ObjectDescriptor', 'name searchable updateable')
FieldDescriptor = namedtuple('FieldDescriptor', 'name type length label')

def list_salesforce_objects(url: str, token: str) -> list[ObjectDescriptor]:
    from requests import get
    query: str = f'{url}/services/data/v60.0/sobjects/'
    res = get(
        query,
        headers = { "authorization": f"Bearer {token}" }
    )
    
    res.raise_for_status()
    data = res.json()
    return [
        ObjectDescriptor(
            # TODO: clarify if we can rely on those fields being there for every object type and column in API version 60.0
            e["name"], e["searchable"], e["updateable"]
        )
        for e in data["sobjects"]
        if e["queryable"] == True
    ]


def describe_salesforce_object(url: str, token: str, object: str) -> list[FieldDescriptor]:
    from requests import get
    query: str = f'{url}/services/data/v60.0/sobjects/{object}/describe'
    res = get(
        query,
        headers = { "authorization": f"Bearer {token}" }
    )
    
    res.raise_for_status()
    data = res.json()
    return [
        FieldDescriptor(
            e["name"],
            e["type"],
            e["length"],
            e["label"]
        )
        for e in data["fields"]
    ]


def get_exa_type_dict(field: FieldDescriptor) -> dict:
    if field.type in ('id', 'reference'):
        return { "type": "CHAR", "size": field.length }
    if field.type == 'boolean':
        return { "type": "BOOLEAN" }
    if field.type in ('string', 'textarea', 'email', 'phone' ):
        return { "type": "VARCHAR", "size": field.length}
    if field.type == 'url':
        return { "type": "VARCHAR", "size": field.length}
    if field.type in ('double', 'percent'):
        return { "type": "DOUBLE" }
    if field.type == 'int':
        return { "type": "DECIMAL", "precision": 18, "scale": 0 }
    if field.type == 'date':
        return { "type": "DATE" }
    if field.type == 'datetime':
        return { "type": "TIMESTAMP", "precision": 3 }
    if field.type == 'currency':
        return { "type": "DECIMAL", "precision": 18, "scale": 2}

    # fallback for now
    return { "type": "VARCHAR", "size": 20000}


def get_exa_type_sql(type_desc: dict) -> str:
    try:
        base_type: str = type_desc["type"]
        if base_type in ('CHAR', 'VARCHAR'):
            return f'{base_type}({type_desc["size"]})'
        if base_type in ('DOUBLE', 'BOOLEAN', 'DATE'):
            return base_type
        if base_type == 'DECIMAL':
            return f'DECIMAL({type_desc["precision"]}, {type_desc["scale"]})'
        if base_type == 'TIMESTAMP':
            ## TODO -- 3 is only the database's default, but 3 is also the only one we 'create' in get_exa_type_dict above
            return f'TIMESTAMP(3)'

    except KeyError:
        raise RuntimeError(f"Incomplete data type: {json.dumps(type_desc)}")
    
    raise RuntimeError(f"Unsupported data type: {base_type}")


def get_column_def(field: FieldDescriptor) -> dict:
    return {
        "name": field.name,
        "dataType": get_exa_type_dict
    (field)
    }


def get_whitelist_pattern(options: dict) -> Pattern:
    if 'OBJECT_WHITELIST' in options:
        return compile(f'^{options["OBJECT_WHITELIST"]}$')
    return compile('.*')


def get_blacklist_pattern(options: dict) -> Pattern:
    if 'OBJECT_BLACKLIST' in options:
        return compile(f'^{options["OBJECT_BLACKLIST"]}$')
    return compile(r'matches nothing')


def call_capabilities(request: dict) -> str:
    # hardcoded, very short list for now
    return json.dumps(
        {
            "type": "getCapabilities",
            "capabilities": [
                "SELECTLIST_PROJECTION",
                "FILTER_EXPRESSIONS",
                "LIMIT",
                "LIMIT_WITH_OFFSET",
                "ORDER_BY_COLUMN",
                ## filter complexity
                "FN_PRED_AND",
                "FN_PRED_BETWEEN",
                "FN_PRED_EQUAL",
                "FN_PRED_IS_NOT_NULL",
                "FN_PRED_IS_NULL",
                "FN_PRED_LESS",
                "FN_PRED_LESSEQUAL",
                "FN_PRED_NOT",
                "FN_PRED_NOTEQUAL",
                ## filter elements
                "LITERAL_BOOL",
                "LITERAL_DATE",
                "LITERAL_DOUBLE",
                "LITERAL_EXACTNUMERIC",
                "LITERAL_STRING",
                "LITERAL_TIMESTAMP"
                # TODO: In-literal-list is also supported by salesforce
            ]
        }
    )

def call_create_schema(request: dict) -> str:
    meta_in: dict = request["schemaMetadataInfo"]
    if 'properties' not in meta_in:
        _usage()
    # properties are provided with every call, not only in create/refresh
    if 'CONNECTION_NAME' not in meta_in['properties']:
        _usage()

    whitelist: Pattern = get_whitelist_pattern(meta_in['properties'])
    blacklist: Pattern = get_blacklist_pattern(meta_in['properties'])

    connection: dict = exa.get_connection(meta_in['properties']['CONNECTION_NAME'])

    reply: dict = {}
    reply["type"] = "createVirtualSchema"
    metaData: dict = {}
    reply["schemaMetadata"] = metaData

    tables: list = []
    metaData["tables"] = tables

    for object_desc in list_salesforce_objects(connection.address, connection.password):
        if not whitelist.match(object_desc.name):
            # skip entries not in whitelist
            continue
        if blacklist.match(object_desc.name):
            # skip entries present in blacklist
            continue

        table_entry: dict = {
            "type": "table",
            "name": object_desc.name
        }
        tables.append(table_entry)
        columns: list = []
        table_entry["columns"] = columns

        for field_desc in describe_salesforce_object(connection.address, connection.password, object_desc.name):
            columns.append( get_column_def(field_desc) )

    return json.dumps(reply)


def call_refresh(request: dict) -> str:
    meta_in: dict = request["schemaMetadataInfo"]
    if 'properties' not in meta_in:
        _usage()
    # properties are provided with every call, not only in create/refresh
    if 'CONNECTION_NAME' not in meta_in['properties']:
        _usage()

    whitelist: Pattern = get_whitelist_pattern(meta_in['properties'])
    blacklist: Pattern = get_blacklist_pattern(meta_in['properties'])

    connection: dict = exa.get_connection(meta_in['properties']['CONNECTION_NAME'])
    requestedTables = request["requestedTables"] if 'requestedTables' in request else None
        

    ## TODO -- make this and CREATE the same code base

    reply: dict = {}
    reply["type"] = "refresh"
    if requestedTables:
        reply["requestedTables"] = requestedTables

    metaData: dict = {}
    reply["schemaMetadata"] = metaData

    tables: list = []
    metaData["tables"] = tables

    for object_desc in list_salesforce_objects(connection.address, connection.password):
        # skip entries not in whitelist
        if not whitelist.match(object_desc.name):
            continue

        # skip entries present in blacklist
        if blacklist.match(object_desc.name):
            continue

        # limit to requested tables (if so)
        if requestedTables and not object_desc.name in requestedTables:
            continue

        table_entry: dict = {
            "type": "table",
            "name": object_desc.name
        }
        tables.append(table_entry)
        columns: list = []
        table_entry["columns"] = columns

        for field_desc in describe_salesforce_object(connection.address, connection.password, object_desc.name):
            columns.append( get_column_def(field_desc) )

    return json.dumps(reply)


def escaped_string(s: str) -> str:
    if s is None:
        return ''
    return f"""'{s.replace("'", "''").replace("&", "%26").replace("#", "%23")}'"""


def operand_to_sql(operand: dict) -> str:
    t: str = operand["type"]

    if t == 'column':
        return operand["name"]
    if t in ('literal_exactnumeric', 'literal_double', 'literal_bool'):
        return operand["value"]
    if t == 'literal_string':
        return escaped_string(operand["value"])
    if t == 'literal_date':
        return operand["value"]
    if t == 'literal_timestamp':
        # value of filter criterion for field '...' must be of type dateTime and should not be enclosed in quotes
        # ugly hack to convert standard SQL timestamp format into the zulu-iso format
        return operand["value"].replace(" ", "T") + "Z"
    
    raise RuntimeError(f'Not Implemented: operand {json.dumps(operand)}')


def get_ordered_operands(filter: dict) -> (bool, dict, dict):
    if 'left' in filter and filter['left']['type'] == 'column':
        return (
            False,
            filter['left'],
            filter['right'] if 'right' in filter else None
        )

    if 'right' in filter and filter ['right']['type'] == 'column':
        return (
            True,
            filter['right'],
            filter['left'] if 'left' in filter else None
        )

    raise RuntimeError(f'Unsupported filter condition: {json.dumps(filter)}')


def convert_between(column: str, lower_bound: dict, upper_bound: dict) -> str:
    return f'{column} >= {operand_to_sql(lower_bound)} and {column} <= {operand_to_sql(upper_bound)}'


# TODO -- Salesforce is really very strict about data types; cannot compare a date to string or datetime etc,
#         so this method should actually take into account the source data type and convert where possible
def create_where(filter: dict) -> str:
    ####
    ## unary operators
    ####
    if filter['type'] == 'literal_bool':
        if filter['value'] == True:
            return 'Id != null'
        return 'Id = null'

    if filter['type'] == 'predicate_not':
        return f'(NOT {create_where(filter["expression"])})'

    if filter['type'] == 'predicate_is_null' and filter['expression']['type'] == 'column':
        return f'{operand_to_sql(filter["expression"])} = null'
        
    if filter['type'] == 'predicate_is_not_null' and filter['expression']['type'] == 'column':
        return f'{operand_to_sql(filter["expression"])} != null'

    ####
    ## multinary operators
    ####
    if filter["type"] == 'predicate_and':
        return ' AND '.join([
                create_where(expr)
                for expr in filter["expressions"]
        ])

    ####
    ## binary operators
    ####

    ## special case
    if filter["type"] == 'predicate_between' and filter['expression']['type'] == 'column':
        # let it pass through to error message if not
        return convert_between(filter['expression']['name'], filter['left'], filter['right'])



    elements_switched, left_elem, right_elem = get_ordered_operands(filter)

    op: str = ""
    if filter["type"] == 'predicate_equal':
        op = '='

    if filter["type"] == 'predicate_less':
        op = '>' if elements_switched else '<'

    if filter["type"] == 'predicate_lessequal':
        op = '>=' if elements_switched else '<='

    if filter["type"] == 'predicate_notequal':
        op = '<>'

    if op == '':
        raise RuntimeError(f'Not Implemented: filter type {json.dumps(filter)}')
    
    return f'{operand_to_sql(left_elem)} {op} {operand_to_sql(right_elem)}'


def single_order(clause: dict) -> str:
    if clause['type'] != 'order_by_element':
        raise RuntimeError(f'Unsupported ORDER BY type: {json.dumps(clause)}')

    return f'{clause["expression"]["name"]} {"ASC" if clause["isAscending"] else "DESC"} NULLS {"LAST" if clause["nullsLast"] else "FIRST"}'


def create_order_by(orders: list) -> str:
    return 'ORDER BY ' + ', '.join([
        single_order(x)
        for x in orders
    ])


def create_limit(clause: dict) -> str:
    return f'LIMIT {clause["numElements"]} {"OFFSET " + str(clause["offset"]) if "offset" in clause else ""}' 


def call_pushdown(request: dict) -> str:
    """Very simplicistic approach here..."""
    assert('pushdownRequest' in request)
    pdr: dict = request['pushdownRequest']

    assert('involvedTables' in request)
    assert(len(request['involvedTables'])==1)
    table: dict = request['involvedTables'][0]

    assert('schemaMetadataInfo' in request)
    assert('properties' in request['schemaMetadataInfo'])

    script_schema: str = exa.meta.script_schema
    source_object: str = pdr["from"]["name"]
    connection_name: str = request['schemaMetadataInfo']['properties']['CONNECTION_NAME']

    ## TODO: selectList might be
    # - not there --> select all columns
    # - empty --> select a random column (or constant)

    emit_names: list = [
        x["name"]
        for x in (pdr["selectList"] if 'selectList' in pdr else request['involvedTables'][0]['columns'])
    ]

    emit_types: list = [ get_exa_type_sql(x) for x in pdr['selectListDataTypes'] ]



    emit_list = ', '.join(
        [ f'"{n}" {t}' for n, t in zip(emit_names, emit_types)]
    )

    where_text: str = ('WHERE ' + create_where(pdr["filter"])) if "filter" in pdr else ''
    order_text: str = (create_order_by(pdr["orderBy"])) if "orderBy" in pdr else ''
    limit_text: str = (create_limit(pdr["limit"])) if "limit" in pdr else ''

    extra_text: str = f'{where_text} {order_text} {limit_text}'

    sql_text: str = f"""
        select "{script_schema}".SF_SELECT(
            {escaped_string(source_object)}
            , {escaped_string(connection_name)}
            , {escaped_string(extra_text)}
        ) emits( {emit_list} )
        """
        
    return json.dumps(
        {
            "type": "pushdown",
            "sql": sql_text
        }
    )


if __name__ == '__main__':
    print(
        adapter_call(
            """
            {
                "schemaMetadataInfo" : 
                {
                    "name" : "SALESFORCE",
                    "properties": {
                        "CONNECTION_NAME": "hello"
                    }
                },
                "type" : "createVirtualSchema"
            }
            """
        )
    )
