# Database and backup changes

1. Keep `plate_info` / `wash_records` compatible with old versions (only ADD
   columns/indexes/tables, guarded by `PRAGMA table_info`). Old apps must still
   open a new backup; new app must open every old database and backup.
2. Migrations go in `_create_schema` (runs on open AND after restore); bump
   `SCHEMA_VERSION`. `executescript` commits first — put `BEGIN;` inside scripts
   that must be atomic.
3. Never delete a database file. Rename in place; move a db with its `-journal`.
4. Restore must accept: `.db` from any version, `.sql` dumps (load with the
   authorizer in `_open_backup_source`), and reject anything without
   `plate_info(part1, part2, phone_number)`. Test each with a hand-built old file.
5. Writes touching several rows: `with self.conn:`.
6. New queries: `EXPLAIN QUERY PLAN` should show the covering indexes; run `tools/bench.py`.
