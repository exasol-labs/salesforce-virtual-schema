# Virtual Schema Adapter for Salesforce

## First Things First

> [!CAUTION]
> 
> This virtual schema adapter is **not** an "officially Exasol supported" project.
> See [DISCLAIMER](DISCLAIMER.md) for more details
 

* This project uses a python/jinja **build process** to create *python* and *SQL* files that can be deployed. If you are looking for ready-to-use files, go to releases/assets in github.
* The project is very much **Work in Progress**, especially the build/test part and lack of modularization / code reuse.
* See [docs/INSTALL](docs/INSTALL.md) for installation instructions
* See [docs/BUILD](docs/BUILD.md) for building / testing instructions

## Supported Options

| Option           | Default           | Description                                                                                           |
|------------------|-------------------|-------------------------------------------------------------------------------------------------------|
| CONNECTION_NAME  | (mandatory)       | Name of the Exasol Connection defining the salesforce base URL and the API authentiction token        |
| OBJECT_WHITELIST | `.*`              | A regular expression defining a whitelist of Salesforce object names (`^` and `$` applied internally) |
| OBJECT_BLACKLIST | `matches nothing` | A regular expression defining a blacklist of Salesforce object names (`^` and `$` applied internally) |

Note: whitelist is applied before blacklist

## Supported Capabilities

- Basics
  - `SELECTLIST_PROJECTION`: will only request required fields from Salesforce
  - `FILTER_EXPRESSIONS`: will push WHERE condition to Salesforce
  - `LIMIT`: passes down any limit to the Salesforce engine
  - `LIMIT_WITH_OFFSET`: does also support limit with offset
  - `ORDER_BY_COLUMN`: supports pushing down sorting to Salesforce
- Filter predicates
  - `FN_PRED_AND`: (condition) `AND` (condition)
  - `FN_PRED_BETWEEN`: (column) BETWEEN (value) and (value)
  - `FN_PRED_EQUAL`: (column) = (value)
  - `FN_PRED_IS_NOT_NULL`: (column) IS NOT NULL
  - `FN_PRED_IS_NULL`: (column) IS NULL
  - `FN_PRED_LESS`: (column) &lt; (value)
  - `FN_PRED_LESSEQUAL`: (column) &lt;= (value)
  - `FN_PRED_NOT`: NOT (condition)
  - `FN_PRED_NOTEQUAL`: (column) <> (value)
- types of (value):
  - `LITERAL_BOOL`
  - `LITERAL_DATE`
  - `LITERAL_DOUBLE`
  - `LITERAL_EXACTNUMERIC`
  - `LITERAL_STRING`
  - `LITERAL_TIMESTAMP`

## Good Things

- For Salesforce, the order of "(column) (operator) (value)" is non-negotiable! The adapter rearranges the incoming arguments accordingly.
- It is unexpected fast and stable enough for playing around with it.

## Bad Things

- Salesforce does not support "(column) (operator) (column)", and there is no way for the adapter to refuse that kind of pushdown request.
  TODO: The adapter could simply create the required select-wrapper in its pushdown answer.
- Salesforce does not support any kind of `LIKE`; so we had to exclude that capability
- Salesforce is very strict / stupid regarding filters, especially for `date` and `datetime` fields: It will not accept a date or string for a datetime filter.
  TODO: The adapter will have to convert incoming filter predicates to a (string) value accepted by the actual saleforce field type.
- The adapter needs a **valid Access Token** to work; it is not an authenticated app that could use a refresh token.
  Create access tokens using the Salesforce CLI[^1] utility. When the token expires, you have to create a new one manually and update the connection definition in Exasol.
- Salesforce SOQL does not support `JOIN`, so the adapter does not. They do support some kind of drill-through referencing in the select list, but converting Exasol joins into such a drilldown would require the adapter to have the full relationship model at pushdown time.

[^1]: <https://developer.salesforce.com/tools/salesforcecli>

## TODO

- condition (X) and (NOT X) --> X = true / X = false
