'''
This module interfaces with a SQL database by writing data extracted
from websocket messages to the database.
'''
import logging
import sqlite3

def create_db_connection(db_location):
    '''
    Connect to the SQL database.

    :param db_location: Location to store the database
    :returns: Database connection
    '''
    connection = None
    try:
        connection = sqlite3.connect(db_location)
        if connection is not None:
            connection.cursor().execute(
                """CREATE TABLE IF NOT EXISTS validation_stream (
                    id TEXT PRIMARY KEY UNIQUE,
                    ledger_hash TEXT NOT NULL,
                    ephemeral_key TEXT NOT NULL,
                    master_key TEXT NOT NULL,
                    signing_time INT NOT NULL,
                    partial_validation BOOLEAN NOT NULL
                );"""
            )

            connection.cursor().execute(
                """CREATE TABLE IF NOT EXISTS ephemeral_keys (
                    ephemeral_key TEXT PRIMARY KEY UNIQUE,
                    master_key INT
                );"""
            )

            connection.cursor().execute(
                """CREATE TABLE IF NOT EXISTS master_keys (
                    master_key TEXT PRIMARY KEY UNIQUE,
                    domain TEXT,
                    dunl BOOLEAN,
                    network TEXT,
                    server_country TEXT,
                    owner_country TEXT,
                    toml_verified BOOLEAN
                );"""
            )

            connection.cursor().execute(
                """CREATE TABLE IF NOT EXISTS ledgers (
                    hash TEXT PRIMARY KEY UNIQUE,
                    sequence INT NOT NULL,
                    signing_time INT,
                    txn_count INT,
                    fee_base INT,
                    fee_ref INT,
                    reserve_base INT,
                    reserve_inc INT,
                    chain TEXT
                );"""
            )

            connection.cursor().execute(
                """CREATE TABLE IF NOT EXISTS manifests (
                    manifest TEXT PRIMARY KEY UNIQUE,
                    master_key INT,
                    ephemeral_key INT,
                    manifest_sig_master TEXT,
                    manifest_sig_eph TEXT,
                    sequence INT
                );"""
            )
        return connection

    except sqlite3.Error as message:
        logging.critical(f"Error creating the database: {message}.")
