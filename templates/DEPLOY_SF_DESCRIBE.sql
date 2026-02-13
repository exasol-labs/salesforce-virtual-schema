/**
    simple describe function to get column definitions from a salesforce object

    Development Status: EXPERIMENTAL
*/

--/
create or replace python3 scalar script SF_DESCRIBE (
    object_name varchar(100), -- name of the salesforce object type, internal notation
    connection_name varchar(128) -- name of the Exasol connection object containing 
) emits (
        column_name varchar(1000),
        column_type varchar(1000),
        column_size int,
        column_label varchar(1000)
    ) 
AS

{% include 'exa_py_describe.py' %}

/

-- example call
-- select SF_DESCRIBE('WorkLog__c', 'SF_TOKEN');
