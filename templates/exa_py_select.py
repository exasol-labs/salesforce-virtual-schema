import requests
import json

def get_typed_entry(entry: dict, column_def) -> Any:
    from datetime import date, datetime

    value: Any = entry[column_def.name]
    if value is None:
        return None

    try:
        out_type: str = column_def.sql_type
        base_type: str = out_type.split('(')[0]
        if base_type in ('CHAR', 'VARCHAR'):
            return str(value)
        if base_type == 'DOUBLE':
            return float(value)
        if base_type == 'BOOLEAN':
            # probably broken
            return True if value else False
        if base_type == 'DATE':
            return date.fromisoformat(value)
        if base_type == 'TIMESTAMP':
            return datetime.fromisoformat(value.split('+')[0])
        if base_type == 'DECIMAL':
            if column_def.scale == 0:
                return int(value)
            return decimal.Decimal(value)
    except:
        raise RuntimeError(f"Incomplete type: {column_def.__dict__}")

    raise RuntimeError(f"Unsupported output type: {json.dumps(column_def)}")


def build_where(filter_in: str) -> str:
    if not filter_in:
        return ''

    filters: dict = json.loads(filter_in)
    if len(filters) == 0:
        return ''

    ## testing: expect preformatted condition
    return f"+WHERE+" + "+AND+".join(
        f'{field}={filters[field]}'
        for field
        in filters
    )


def raise_error(container: dict|list) -> None:
    if 'message' in container:
        raise RuntimeError(f'SF API error: {container["message"]}')

    if isinstance(container, list):
        raise_error(container[0])

    raise RuntimeError(f'SF API error: {container}')


def run(ctx):
    salesforce_conn = exa.get_connection(ctx.connection_name)
 
    cols: str = ",".join( [ x.name for x in exa.meta.output_columns ] ) 

    where_condition: str = ctx.filter_string or ''

    query: str = f'{salesforce_conn.address}/services/data/v60.0/query/' + f'?q=SELECT {cols} from {ctx.object_name} {where_condition}'

    ## query syntax: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select.htm

    while query:
        res = requests.get(
            query,
            headers = { "authorization": f"Bearer {salesforce_conn.password}" }
        )

        data = res.json()

        if res.status_code > 200:
            raise_error(data)

        for entry in data["records"]:
            collated = [
                get_typed_entry(entry, x)
                for x in exa.meta.output_columns 
            ]
            ctx.emit(*collated)

        ## while res contains 'nextRecordsUrl', fetch that url and loop again
        query = f'{salesforce_conn.address}{data["nextRecordsUrl"]}' if 'nextRecordsUrl' in data else None
