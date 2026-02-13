#!/usr/bin/env python3


if __name__ == "__main__":
    from jinja2 import (Environment, Template, FileSystemLoader)

    env = Environment(loader=FileSystemLoader("templates/"))
    # TODO: replace fixed list with "find *.jsql"
    for template in [
        'DEPLOY_SF_DESCRIBE.sql',
        'DEPLOY_SF_SELECT.sql',
        'DEPLOY_SF_ADAPTER.sql',
        'DEPLOY_SF_QUERY.sql',
        'DEPLOY_SF_LIST.sql',
        'test_basic.py'
    ]:
        print(f"Processing {template}...")
        res = env.get_template(template).render()
        target_file: str = template.removeprefix('DEPLOY_')

        with open(f'sql/deploy/{target_file}', mode='wt') as out_file:
            out_file.write(res)

    # TODO: add another loop for python templates (adding exasol-toolbox wrapper to python snippets)
