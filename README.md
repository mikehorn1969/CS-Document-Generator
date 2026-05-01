CS Document Generator (DG) is one component of the business process automation solution for Change Specialists.

All content of this repository is Copyright Change Specialists 2025

It validates data against Companies House, and uses the NAME API for director name matching.

Documents currently generated are as follows:
Service Provider NDA - SharePoint & Docusign
Service Provider MSA - SharePoint & Docusign
Service Provider statement of services - SharePoint
Client MSA - SharePoint & Docusign
Client statement of services - SharePoint

DG holds service descriptions and various other contract level agreements in an Azure SQL database. The database a single source of truth for Client and Service Provider contracts, augmenting Colleague 7.

## Database Access Pattern (Required)

All application-level database reads and writes should go through the shared helpers in app/helper.py.

Use these helpers:

- Reads:
	- db_query_scalars(stmt, operation_name=...)
	- db_query_scalar(stmt, operation_name=...)
	- db_query_one_or_none(stmt, operation_name=...)
	- db_get_by_pk(Model, key, operation_name=...)
- Writes:
	- db_add(instance)
	- db_delete(instance)
	- db_commit(operation_name=...)

Why:

- Enforces a single connection check path (db_connected)
- Applies retry and backoff for transient database failures
- Ensures rollback on failed operations
- Gives consistent logging with operation_name labels

Do not add direct db.session.* calls in views or query modules unless there is a startup/engine-management reason.

Examples:

- Instead of db.session.scalar(stmt), use db_query_scalar(stmt, operation_name="my_operation").
- Instead of db.session.add(...) + db.session.commit(), use db_add(...) and db_commit("my_operation").

