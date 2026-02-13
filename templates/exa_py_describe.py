import requests

def run(ctx):
    salesforce_conn = exa.get_connection(ctx.connection_name)

    # cols: str = ",".join( [ x.name for x in exa.meta.output_columns ] )

    query: str = f'{salesforce_conn.address}/services/data/v60.0/sobjects/{ctx.object_name}/describe'
    res = requests.get(
        query,
        headers = { "authorization": f"Bearer {salesforce_conn.password}" }
    )
    
    res.raise_for_status()
    data = res.json()
    for entry in data["fields"]:
        ctx.emit(
            entry["name"] if 'name' in entry else None,
            entry["type"] if 'type' in entry else None,
            entry["length"] if 'length' in entry else None,
            entry["label"] if 'label' in entry else None
         )

if __name__ == "__main__":
    raise RuntimeError("Not Implemented")
