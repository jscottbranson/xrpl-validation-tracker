'''
This module interfaces with a SQL database by writing data extracted
from websocket messages to the database.
'''

import sqlite3

RIPPLED_TIME_OFFSET = 946684800

def sql_write(sql, data, connection):
    '''
    :param data: the SQL data to be inserted into the table
    :param sql: the SQL query
    :param connection: Connection to the SQL database
    '''
    try:
        cursor = connection.cursor()
        cursor.execute(sql, data)
        connection.commit()
        return cursor.lastrowid
    except sqlite3.Error as exception:
        print("Could not write data to database.", exception)

def ledger_id_check(message, connection):
    '''
    Query the ledger database to see if the hash already exists. If it does not, then
    insert the hash and sequence.
    '''
    # signing_time might be incorrect (i.e., if one node misreports it for some reason)
    # Double check signing time against an aggregated 'ledger' subscription stream or another source
    cursor = connection.cursor()
    cursor.execute("SELECT rowid FROM ledgers WHERE hash=?", (message['ledger_hash'],))
    ledger_id = cursor.fetchall()

    if ledger_id:
        ledger_id = ledger_id[0][0]
    elif not ledger_id:
        sql = ''' INSERT INTO ledgers(
                    hash,
                    sequence,
                    signing_time)
                    VALUES(?,?,?) '''

        data = (
            message['ledger_hash'],
            message['ledger_index'],
            message['signing_time'],
        )

        ledger_id = sql_write(sql, data, connection)

    return ledger_id

def get_validator_key(key, column, table, connection):
    '''
    Query the ephemeral_keys database to see if the ephemeral key already exists.
    If it does not, then insert the key.

    :param str key: Database will return an index ID for the key.
    :param str column: Column in the table to search. For example, 'ephemeral_key'
    :param str table: Table to query in the DB. For example, 'ephemeral_keys'
    :returns: Database id for the key.
    '''
    cursor = connection.cursor()
    cursor.execute(f"SELECT rowid FROM {table} WHERE {column}=?",
                   (key,))
    key_id = cursor.fetchall()

    if key_id:
        key_id = key_id[0][0]
    elif not key_id:
        sql = ''' INSERT INTO {}(
                    {})
                    VALUES(?) '''.format(table, column)

        data = (key,)

        key_id = sql_write(sql, data, connection)

    return key_id

def ledger(message, connection):
    '''
    Append number of transactions to the ledger table.
    :param message: a websocket message
    :param connection: connection to the SQL database
    '''

    data = (
        message['txn_count'],
        message['ledger_hash'],
    )

    sql = ''' UPDATE ledgers SET tx_count = ? WHERE hash = ? '''

    sql_write(sql, data, connection)


def validations(message, connection):
    '''
    Parse validations subscription messages into SQL.
    :param message: a websocket validation stream subscription response message
    :param connection: connection to the SQL database
    '''
    ledger_id = ledger_id_check(message, connection)
    ephemeral_key_id = get_validator_key(
        message['validation_public_key'],
        'ephemeral_key',
        'ephemeral_keys',
        connection
    )
    master_key_id = get_validator_key(
        message['master_key'],
        'master_key',
        'master_keys',
        connection
    )

    identifier = str(ephemeral_key_id) + '+' + str(ledger_id)

    cursor = connection.cursor()
    cursor.execute("SELECT rowid FROM validation_stream WHERE id=?",
                   (identifier,))
    validation_id = cursor.fetchall()

    if not validation_id:
        data = (
            identifier,
            ledger_id,
            ephemeral_key_id,
            master_key_id,
            message['signing_time'] + RIPPLED_TIME_OFFSET,
            str(not message['full']),
        )

        sql = ''' INSERT INTO validation_stream(
                id,
                ledger_hash,
                ephemeral_key,
                master_key,
                signing_time,
                partial_validation
                )
                VALUES(?,?,?,?,?,?)'''

        sql_write(sql, data, connection)
