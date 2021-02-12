import asyncio
import logging
from sys import exit

from .sqlite_connection import create_db_connection
from .sqlite_writer import validations as db_validation_writer

async def process_data(queue, settings):
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
        validation = await queue.get()
        try:
            if validation['type'] == 'validationReceived' and 'master_key' in validation:
                db_validation_writer(validation, database)
        except KeyError as error:
            # Ignore messages that don't contain 'type' key
            pass

        queue_size = queue.qsize()
        if queue_size > queue_size_max:
            queue_size_max = queue_size
            logging.info(f"New record high queue size: {queue_size_max}.")
        print(f"Current queue length: {queue_size}. Max queue length: {queue_size_max}.")
