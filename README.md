# XRPL Validation Tracker
Three modules are provided:
1. The `aggregator` combines multiple websocket subscription streams into a single outgoing websocket stream.
2. `db_writer` stores XRP Ledger data in relational databases. Since this code is in testing, only sqlite3 is supported now. Better database support is needed for production.
3. `ws_client` is used to connect to remote websocket servers and is used by both the `aggregator` and `db_writer` modules.

The `aggregator` is designed for more flexible use with a wide range of streams. The `db_writer` is currently specific to the validation stream, though support for additional streams would be beneficial (e.g., the ledger stream).

The `aggregator` code is structured to provide multiple layers of redundancy. For example, four servers could use the `aggregator` code to subscribe to 5-10 XRP Ledger nodes. Two additional servers could then use the `db_writer`, which already depends on the `aggregator` to subscribe to the previously mentioned four servers. This schema provides redundancy at both the data aggregation and database ingestion stages.

## Installing & Running the Software
After installing dependencies, adjust the settings in `settings_aggregator.py` and/or `settings_db_writer.py`, then run `run_tracker.py` using either an '-a' or '-d' flag to specify which module to run. Both modules can be run on the same system, though they must be started separately.

All modules depend on the python `websockets` module. `db_writer` also requires sqlite3.

The `supplemental_data` depends on the `xrpl_unl_parser`, `pytomlpp`, and `aiohttp`.

This has been tested on Python 3.7 and 3.8.

### Querying the database
The database can be queried using standard sqlite3.

Query validators whose TOML files are verified:
`sqlite3 validations.sqlite3 'SELECT * FROM master_keys WHERE toml_verified IS 1 ORDER BY domain ASC;' | cat >> keys_toml.txt`

Query validators with verified domains:
`sqlite3 validations.sqlite3 'SELECT * FROM master_keys WHERE domain IS NOT NULL ORDER BY domain ASC;' | cat >> keys_domain.txt`

Query the transaction count in ledger(s) matching a given sequence:
`sqlite3 validations.sqlite3 'SELECT txn_count from ledgers WHERE sequence is 61809888;'`

Query for missing main net ledgers:
`sqlite3 validations.sqlite3 'SELECT min(sequence) + 1 FROM (SELECT ledgers.*, lead(sequence) OVER (order by sequence) AS next_id FROM ledgers) ledgers WHERE next_id <> sequence + 1 AND txn_count IS NOT NULL;' | cat >> missing_ledgers.txt`

Given that sqlite3 is not ideal for production, there is a need for additional scripts that interface with more robust databases.

## To Do Items
1. Transition to Postgres or another production database
2. Improve database structure, consolidate queries, & index the database
3. Improve the websocket server `ws_server` in the `aggregator` - accept headers, subscribe messages, etc.
4. API access - mimic Data API v2 + live validation stream subscription (notify missing) - consider developing a `db_reader` package to retrieve requests.
5. Multiple "To-do" items are noted in comments throughout the code.
6. Change logging to % format
7. Daemonize
8. Fix errors with multiprocessing when exiting using keyboard interrupt
9. Support multiple UNLs
10. Verify UNLs authenticity against a provided signature (this has more to do w/ updating the [`xrpl_unl_parser` package].)
11. Check attestations in TOMLs
12. Write ledgerClosed stream data to DB
13. Move this list to [Issues]
14. Add ephemeral_key column to validation_stream DB
15. Add 'first_seen' columns to master and ephemeral key DBs

## Thoughts
1. Identify main chain through an aggregated ledger subscription stream - use this to verify hash, index, and time
2. Trie or rrdtool?

[`xrpl_unl_parser` package]:https://github.com/crypticrabbit/xrpl_unl_parser
[Issues]:https://github.com/crypticrabbit/xrpl-validation-tracker/issues
