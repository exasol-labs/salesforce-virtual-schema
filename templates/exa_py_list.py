import requests

def run(ctx):
    salesforce_conn = exa.get_connection(ctx.connection_name)

    query: str = f'{salesforce_conn.address}/services/data/v60.0/sobjects/'
    res = requests.get(
        query,
        headers = { "authorization": f"Bearer {salesforce_conn.password}" }
    )
    
    res.raise_for_status()
    data = res.json()
    for entry in data["sobjects"]:
        ctx.emit(
            # TODO: clarify if we can rely on those fields being there for every object type and column in API version 60.0
            entry["name"] if 'name' in entry else None,
            entry["searchable"] if 'searchable' in entry else False,
            entry["updateable"] if 'updateable' in entry else False,
            entry["label"] if 'label' in entry else None
        )

if __name__ == "__main__":
    raise RuntimeError("Not Implemented")
