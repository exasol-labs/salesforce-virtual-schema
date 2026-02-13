# Installation Procedure

## Prerequisites

- Database privileges to create scripts and virtual schemas
- A valid access token to the salesforce API
  - generated with the `sf` commandline tool
  - sandbox instances supported

## Adapter Deployment

### 1 - have or create a schema for the adapter script(s)

```sql
CREATE SCHEMA IF NOT EXISTS salesforce_scripts;
OPEN SCHEMA salesforce_scripts;
```

### 2 - create the scripts in Exasol using the files from sql/ folder

```sql
create or replace python3 adapter script salesforce_adapter
...
/

create or replace python3 scalar script SF_SELECT (
...
/
```

> [!INFO]
> 
> All you need for the virtual schema are the `SF_ADAPTER.sql` and `SF_SELECT.sql` files. The others are
> for exploration and debugging.

## Virtual Schema Creation

### 3 - create a CONNECTION with the salesforce URL and access token.

Make sure that either

- the virtual schema adapter owner (==schema owner)
- or the adapter script itself

is allowed to use the CONNECTION

```sql
create or replace connection SF_TOKEN
  to 'https://your-org.my.salesforce.com' -- or sandbox URL
  identified by 'aaxuzw7...asdad' -- your access token
  ;
```

### 4 - create virtual schema using adapter and token

```sql
create virtual schema VS_SALESFORCE
  using SALESFORCE_SCRIPTS.SALESFORCE_ADAPTER
  with CONNECTION_NAME = 'SF_TOKEN'

  -- optional, default '.*'
  OBJECT_WHITELIST = 'Account.*'

  -- optional, default 'matches nothing'   
  OBJECT_BLACKLIST = '.*ChangeEvent'
  ;
```

If there is no error, congratulations.... you should now be able to see a new virtual schema `VS_SALESFORCE` with some tables ready to use.

```sql
select count(*) from VS_SALESFORCE."Account";
select * from VS_SALESFORCE."Account" where "Id" = 'basjdzzehjajsdi';
```

### 5 - Adapt blacklist and whitelist

Once you are satisfied with the basic workings and want to go big,
you can change the object filters to get more visible tables:

```sql
alter virtual schema VS_SALESFORCE
SET OBJECT_WHITELIST = '(Account|Asset.*|Calendar|Case.*|Contact)'
-- or OBJECT_WHITELIST = '.*'
;
```

> [!NOTE]
> 
> Collecting object structure information takes time per object.
> Be prepared to wait a few minutes at this step when you pull in 
> has many object types here...

> [!INFO]
> 
> The `SF_LIST` script (if deployed) can be used to get a list of valid/accessible salesforce objects:
> ```sql
> select SALESFORCE_SCRIPTS.SF_LIST('SF_TOKEN');
> ```

## Debugging

- use provided script (TBD)  for verbose connection testing
