'''
This module interfaces with a SQL database by writing data extracted
from websocket messages to the database.
'''

import sqlite3
from sqlite3 import Error
import settings_database as settings

def create_db_connection():
    '''
    Connect to the SQL database.
    :param format: structure for the table that is being written to.
    '''
    try:
        connection = sqlite3.connect(settings.DATABASE)
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
                            master_key text PRIMARY KEY UNIQUE
                            );"""
                                            )

                connection.cursor().execute("""CREATE TABLE IF NOT EXISTS ledgers(
                            hash text PRIMARY KEY UNIQUE,
                            sequence integer NOT NULL,
                            signing_time integer
                            );"""
                                            )

                return connection
            except Error as message:
                print("EXCEPTION: ", message)

    except Error as message:
        print(message)
