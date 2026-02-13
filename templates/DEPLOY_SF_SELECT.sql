/**
    Simple script to select information for one specific object type.
    Think of an object type as a table, and all the object properties as columns.
    Each object is one entry in that table.

    Development Status: EXPERIMENTAL
*/

--/
create or replace python3 scalar script SF_SELECT (
        object_name varchar(100), -- object type in salesforce
        connection_name varchar(128), -- name of Exasol connection defining salesforce access
        filter_string varchar(2000000) -- optional query string after the table name (WHERE condition)
) emits (...) 
AS

{% include 'exa_py_select.py' %}

/

/** example queries (TODO: add filter examples)
select SF_QUERY_OBJECT('Asset', 'SF_TOKEN', '') emits (
    -- list of fields we want to read from salesforce Asset
    "Id" varchar(64), "Name" varchar(1000), "ServiceTag__c" varchar(100)
);
select SF_QUERY_OBJECT('WorkLog__c', 'SF_TOKEN', '') emits (
    -- list of fields we want to read from salesforce Work Log (custom object)
    "Case__c" varchar(100), "Agent__c" varchar(64), "TotalTime__c" varchar(1000), "WorkDescription__c" varchar(32768)
);
*/
