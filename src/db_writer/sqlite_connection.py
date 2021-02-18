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
    '''
    try:
        connection = sqlite3.connect(db_location)
        if connection is not None:
            try:
                connection.cursor().execute("""CREATE TABLE IF NOT EXISTS validation_stream (
                            id text PRIMARY KEY,
                            ledger_hash text NOT NULL,
                            ephemeral_key text NOT NULL,
                            master_key text NOT NULL,
                            signing_time integer NOT NULL,
                            partial_validation text NOT NULL
                            );"""
                                            )

                connection.cursor().execute("""CREATE TABLE IF NOT EXISTS ephemeral_keys (
                            ephemeral_key text PRIMARY KEY UNIQUE
                            );"""
                                            )

                connection.cursor().execute("""CREATE TABLE IF NOT EXISTS master_keys (
                            master_key text PRIMARY KEY UNIQUE,
                            domain text,
                            dunl boolea,
                            network text,
                            server_country text,
                            owner_country text,
                            toml_verified boolean
                            );"""
                                            )

                connection.cursor().execute("""CREATE TABLE IF NOT EXISTS ledgers(
                            hash text PRIMARY KEY UNIQUE,
                            sequence integer NOT NULL,
                            signing_time integer
                            );"""
                                            )

                return connection
            except sqlite3.Error as message:
                logging.critical(f"Error creating the database: {message}.")
                return None

    except sqlite3.Error as message:
        logging.critical(f"Error creating the database: {message}.")
