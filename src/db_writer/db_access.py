import asyncio
import logging
from sys import exit

from .sqlite_connection import create_db_connection
from .sqlite_writer import validations as db_validation_writer

async def process_db_data(queue, settings):
    '''
    Process data websocket connections place into the queue.

    :param asyncio.queues.Queue queue: Validation stream queue
    :param settings: Configuration file
    '''
    queue_size_max = 0
    # Create an object for the database connection.
    database = create_db_connection(settings.DATABASE_LOCATION)
    # Listen for validations
    while True:
        message = await queue.get()
        try:
            if message['type'] == 'validationReceived' and 'master_key' in message:
                db_validation_writer(message, database)
            elif message['type'] == 'ledgerClosed':
                print(f"{message}")
        except KeyError:
            # Ignore messages that don't contain 'type' key
            pass
        except KeyboardInterrupt:
            break

        queue_size = queue.qsize()
        if queue_size > queue_size_max:
            queue_size_max = queue_size
            logging.info(f"New record high for DB write queue size: {queue_size_max}.")
