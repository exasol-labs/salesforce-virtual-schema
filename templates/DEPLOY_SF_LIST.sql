/**
    simple function to get a list of all salesforce objects

    Development Status: EXPERIMENTAL
*/

--/
create or replace python3 scalar script SF_LIST (
    connection_name varchar(128) -- name of the Exasol connection object
) emits (
        object_name varchar(1000),
        searchable boolean,
        updateable boolean,
        object_label varchar(1000)
    ) 
AS

{% include 'exa_py_list.py' %}

/

-- example call
-- select SF_LIST('SF_TOKEN');
