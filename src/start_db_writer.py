'''Write incoming validation stream websocket messages to a database.'''
import logging

import settings_database as settings
from db_writer.db_asyncio_tasks import start_loop

def config_logging():
    '''
    Configure logging.
    '''
    logging.basicConfig(
        filename=settings.LOG_FILE,
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format='%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s',
    )

def check_assertions():
    '''
    Ensure the requisite settings are present.
    '''
    pass


if __name__ == "__main__":
    config_logging()
    check_assertions()
    start_loop()
