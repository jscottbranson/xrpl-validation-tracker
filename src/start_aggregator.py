'''Run the validation stream aggregator.'''
import logging

import settings_aggregator as settings
from aggregator.asyncio_tasks import start_loop

def config_logging():
    '''Configure logging.'''
    logging.basicConfig(
        filename=settings.LOG_FILE,
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format='%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s',
    )

def check_assertions():
    '''Ensure the requisite settings are present.'''
    for i in settings.URLS:
        assert (isinstance(i['ssl_verify'], bool)), "ssl_verify type must be a boolean."
        assert (isinstance(i['url'], str)), "URLs must be strings."

if __name__ == "__main__":
    config_logging()
    check_assertions()
    print("Aggregator started")
    print("Server listening on ws://" + settings.SERVER_IP + ":" + str(settings.SERVER_PORT))
    start_loop()
