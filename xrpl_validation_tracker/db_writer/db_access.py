import asyncio
import logging
import sqlite3
from sys import exit

from .sqlite_connection import create_db_connection
from .sqlite_writer import validations as db_validation_writer
from .sqlite_writer import ledgers as db_ledger_writer

async def process_db_data(queue, settings):
    '''
    Process data websocket connections place into the queue.

    :param asyncio.queues.Queue queue: Validation stream queue
    :param settings: Configuration file
    '''
    # Create an object for the database connection.
    database = create_db_connection(settings.DATABASE_LOCATION)
    # Listen for validations
    while True:
        message = await queue.get()
        try:
            if not database:
                database = sqlite3.connect(settings.DATABASE_LOCATION)
            if message['type'] == 'validationReceived' and 'master_key' in message:
                db_validation_writer(message, database)
            elif message['type'] == 'ledgerClosed':
                db_ledger_writer(message, database)
        except sqlite3.Error as error:
            logging.warning(f"Unable to connect to the database: {error}.")
        except KeyError:
            # Ignore messages that don't contain 'type' key
            pass
        except KeyboardInterrupt:
            break
