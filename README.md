# XRPL Validation Tracker
Four modules are provided:
1. The `aggregator` combines multiple websocket subscription streams into a single outgoing websocket stream.
2. `db_writer` stores XRP Ledger data in relational databases. Since this code is in testing, only sqlite3 is supported now. Better database support is needed for production.
3. `supplemental_data` provides data from manifests, TOML files, and published UNL(s).
4. `ws_client` is used to connect to remote websocket servers and is used by both the `aggregator` and `db_writer` modules.

The `aggregator` is designed for more flexible use with a wide range of streams. The `db_writer` is currently specific to 'validation' and 'ledger' subscription streams, and support for additional streams can be easily added as needed.

The `aggregator` code is structured to provide multiple layers of redundancy. For example, four servers could use the `aggregator` code to subscribe to 5-10 XRP Ledger nodes. Two additional servers could then use the `db_writer`, which already depends on the `aggregator`, to subscribe to the previously mentioned four servers. This schema provides redundancy at both the data aggregation and database ingestion stages.

## Installing & Requirements
* All modules require `websockets`
* `db_writer` and `supplemental_data` require sqlite3

  * `supplemental_data` also requires `pytomlpp`, and `aiohttp`
* `supplemental_data` requires [`xrpl-unl-manager`], which must be manually downloaded.
* `pip install -r requirements.txt` automatically installs the required packages

  * [`xrpl-unl-manager`] must be downloaded manually
  * The requirements.txt is generated using `pip freeze` in Python 3.8
  * It is possible older package versions will also work

At this time, all dependencies can be installed inside a Python3 virtual environment using:
`pip install -r requirements.txt && git clone https://github.com/antIggl/xrpl-unl-manager.git && mv xrpl-unl-manager ./xrpl_validation_tracker/xrpl_unl_manager`

Development is tested on Python 3.8.

## Running the Software
1. Install dependencies
2. Navigate to the xrpl_validation_tracker directory
3. Adjust the settings in `settings_aggregator.py`, `settings_db_writer.py`, and `settings_supplemental.py`
4. Run `python3 run_tracker.py` using the '-a', '-d', and/or 's' flags to specify which module(s) to run (there is not a flag to run `ws_client`, as it is a dependency for other modules).

All three modules modules can be run on the same system and started simultaneously. A Python multiprocessing bug can inhibit clean shutdown via keyboard interrupt, and users are encouraged to check for orphaned processes if keyboard interrupt must be invoked multiple times.

### Querying the database
The database can be queried using standard sqlite3.

Query validators whose TOML files are verified:
`sqlite3 validations.sqlite3 'SELECT * FROM master_keys WHERE toml_verified IS 1 ORDER BY domain ASC;'`

Query validators with verified domains:
`sqlite3 validations.sqlite3 'SELECT * FROM master_keys WHERE domain IS NOT NULL ORDER BY domain ASC;' | cat >> keys_domain.txt`

Query the transaction count in ledger(s) matching a given sequence:
`sqlite3 validations.sqlite3 'SELECT txn_count from ledgers WHERE sequence is 61809888;'`

Query the number of entries in the validation_stream table:
`sqlite3 validations.sqlite3 'select Count(*) FROM validation_stream;'`

Given that sqlite3 is not ideal for production, there is a need for additional scripts that interface with more robust databases.

## To Do Items
1. Add support (translate queries) for Postgres or another production database
2. Improve database structure, consolidate queries, & index the tables
3. Improve the websocket server `ws_server` in the `aggregator` - accept headers, subscribe messages, etc.
4. API access - mimic Data API v2 + live validation stream subscription (notify missing) - consider developing a `db_reader` package to retrieve requests.
5. Multiple "To-do" items are noted in comments throughout the code.
6. Change logging to % format
7. Daemonize
8. Fix errors with multiprocessing when exiting using keyboard interrupt
9. Support multiple published UNLs & verify published UNL signatures
10. Check attestations in TOMLs
13. Move this list to [Issues]
14. Add ephemeral_key column to validation_stream DB
15. Add 'first_seen' columns to master and ephemeral key DBs
16. Verify manifest signatures
17. Find & deal with blocking in ws_server, process_data, & others
18. Write a setup.py script for [`xrpl-unl-manager`]?

## Thoughts
1. Identify main chain through an aggregated ledger subscription stream - use this to verify hash, index, and time
2. Trie or rrdtool?

[`xrpl-unl-manager`]:https://github.com/antIggl/xrpl-unl-manager
[Issues]:https://github.com/crypticrabbit/xrpl-validation-tracker/issues
