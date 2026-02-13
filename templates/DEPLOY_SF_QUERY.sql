--/
create or replace python3 scalar script SF_QUERY(
    connection_name varchar(128),
    query_text varchar(2000000)
) returns varchar(2000000)
as

{%include 'exa_py_query.py' %}

/
