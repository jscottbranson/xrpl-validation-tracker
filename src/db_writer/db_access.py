import asyncio
import logging
from sys import exit

import settings_database as settings
from .sqlite_connection import create_db_connection
from .sqlite_writer import validations as db_validation_writer

async def process_data(queue):
    '''
    Process data websocket connections place into the queue.
    :param asyncio.queues.Queue queue: Validation stream queue
    '''
    queue_size_max = 0
    # Create an object for the database connection.
    database = create_db_connection()
    # Listen for validations
    while True:
        validation = await queue.get()
        db_validation_writer(validation, database)
        queue_size = queue.qsize()
        if queue_size > queue_size_max:
            queue_size_max = queue_size
            logging.info(f"New record high queue size: {queue_size_max}.")
        print(f"Current queue length: {queue_size}. Max queue length: {queue_size_max}.")
