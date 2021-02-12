# XRPL Validation Tracker
Three modules are provided:
1. The `aggregator` combines multiple websocket subscription streams into a single outgoing websocket stream.
2. `db_writer` stores XRP Ledger data in relational databases. Since this code is in testing, only sqlite3 is supported now. Better database support is needed for production.
3. `ws_client` is used to connect to remote websocket servers and is used by both the `aggregator` and `db_writer` modules.

The `aggregator` is designed for more flexible use with a wide range of streams. The `db_writer` is currently specific to the validation stream, though support for additional streams would be beneficial (e.g., the ledger stream).

The `aggregator` code is structured to provide multiple layers of redundancy. For example, four servers could use the `aggregator` code to subscribe to 5-10 XRP Ledger nodes. Two additional servers could then use the `db_writer`, which already depends on the `aggregator` to subscribe to the previously mentioned four servers. This schema provides redundancy at both the data aggregation and database ingestion stages.

## Installing & Running the Software
After installing dependencies, adjust the settings in `settings_aggregator.py` and/or `settings_db_writer.py`, then run `start_aggregator.py` and/or `start_db_writer.py`. Both modules can be run on the same system.

All modules depend on the python `websockets` module.
`db_writer` requires sqlite3

This has been tested on Python 3.7 and 3.8

## To Do Items
1. Transition to Postgres or another production database
2. Improve database structure & index the database
3. Improve the websocket server `ws_server` in the `aggregator` - accept headers, subscribe messages, etc.
4. API access - mimic Data API v2 + live validation stream subscription (notify missing) - consider developing a `db_reader` package to retrieve requests.
5. Multiple "To-do" items are noted in comments throughout the code.
6. Change logging to % format
7. Daemonize
8. Add threading to the startup script, so a user can start multiple modules at once
9. Fetch manifest, verify domain, and store domain in DB
10. Retrieve and store UNL(s) & flag validator keys in the DB that belong to a specified UNL

## Thoughts
1. Identify main chain through an aggregated ledger subscription stream - use this to verify hash, index, and time
2. Trie or rrdtool?
