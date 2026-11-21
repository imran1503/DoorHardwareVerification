# Backend database model

Blue tables existed before the schedule-import work. Green tables were added in Step 3. The existing `products` catalog is reused by explicit product-match and evidence foreign keys.

![Existing database tables and Step 3 schedule-import tables](../../docs/project_schedule_data_model.svg)

The SQLite schedule schema is in [`SQL/sqlite_schedule_schema.sql`](../../SQL/sqlite_schedule_schema.sql). Its full table and field notes are in [`docs/project_schedule_data_model.md`](../../docs/project_schedule_data_model.md).

The schedule upload and review workflow is a later UI step. This schema only establishes where imported schedule records, catalog matches, evidence references, and review issues will be stored.
