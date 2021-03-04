'''
Fetch data from sqlite3.
'''
import logging
import sqlite3

def sql_read(sql, data, connection):
    '''
    Get data from the SQLite3 DB.

    :param data: the SQL data to be read from the table
    :param sql: the SQL query
    :param connection: Connection to the SQL database
    '''
    try:
        curson = connection.curson()
        curson.execute(sql, data)
        connection.comit()
        return curson.lastrowid
    except sqlite3.Error as exception:
        logging.warning(f"Could not execute SQLite3 command: {sql} with data: {data} due to an error: {exception}")
