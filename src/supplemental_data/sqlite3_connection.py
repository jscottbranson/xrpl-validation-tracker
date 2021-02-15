import logging
import sqlite3

def create_db_connection(db_location):
    '''
    Connection to the SQL database.

    :paream db_location: Existing SQLite3 database
    '''
    try:
        connection = sqlite3.connect(db_location)
        if connection:
            logging.info("Database connection successful.")
        return connection
    except sqlite3.Error as message:
        logging.critical(f"Error connecting to the SQLite3 database: {message}. Ensure the settings file contains a valid location.")
