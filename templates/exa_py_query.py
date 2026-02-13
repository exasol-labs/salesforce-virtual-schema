import requests


def raise_error(container: dict|list) -> None:
    if 'message' in container:
        raise RuntimeError(f'SF API error: {container["message"]}')

    if isinstance(container, list):
        raise_error(container[0])

    raise RuntimeError(f'SF API error: {container}')


def run(ctx):
    salesforce_conn = exa.get_connection(ctx.connection_name)
 
    ## query syntax: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select.htm
    query: str = f'{salesforce_conn.address}/services/data/v60.0/query/' + f'?q={ctx.query_text}'

    res = requests.get(
        query,
        headers = { "authorization": f"Bearer {salesforce_conn.password}" }
    )

    if res.status_code > 200:
        raise_error(res.json())

    return res.text


"""Examples:

select count() from Asset;
-- {"totalSize":2983,"done":true,"records":[]}

select Count() from Account where NumberOfEmployees < 1000
-- {"totalSize":2276,"done":true,"records":[]}

### NOT SUPPORTED:
- LIKE
- BETWEEN
- <literal> <op> <field>    -- must be <field> <op> <literal>
- <field> <op> <field>      --- ?? data type mismatch ??


### OUT OF SCOPE: GROUP BY and aggregates

select BillingCountry, Count(Name) from Account group by BillingCountry
-- {"totalSize":81,"done":true,"records":[
-- {"attributes":{"type":"AggregateResult"},"BillingCountry":null,"expr0":369},
-- {"attributes":{"type":"AggregateResult"},"BillingCountry":"Poland","expr0":29},
-- {"attributes":{"type":"AggregateResult"},"BillingCountry":"Canada","expr0":25},
-- ...
-- unnamed expressions are numbered 'expr0', 'expr1'

"""