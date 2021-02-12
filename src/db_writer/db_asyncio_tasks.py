'''
Compile and run asyncio tasks.
'''
import asyncio
import logging
from sys import exit as sys_exit

from ws_client import ws_listen
from ws_client import ws_minder
from .db_access import process_data

async def spawn_workers(settings):
    '''
    Add tasks to the asyncio loop.

    :param settings: Configuration file
    '''
    ws_servers = []

    # Create queues for websocket messages
    queue = asyncio.Queue(maxsize=0)
    logging.info("Adding initial asyncio tasks to the loop.")
    for url in settings.URLS:
        ws_servers.append(
            {
                'task': asyncio.create_task(
                    ws_listen.websocket_subscribe(url, settings.WS_SUBSCRIPTION_COMMAND, queue)
                ),
                'url': url,
                'retry_count': 0,
            }
        )

    # subscribe to a websocket server
    asyncio.create_task(
        ws_minder.mind_tasks(
            ws_servers,
            queue,
            settings
        )
    )
    # write into the db
    asyncio.create_task(process_data(queue, settings))

def start_loop(settings):
    '''
    Run the asyncio event loop.

    :param settings: Configuration file
    '''
    try:
        loop = asyncio.get_event_loop()
        # Debug asyncio
        if settings.ASYNCIO_DEBUG is True:
            loop.set_debug(True)
            logging.info("asyncio debugging enabled.")

        loop.run_until_complete(spawn_workers(settings))
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt detected. Exiting.")
        sys_exit(0)
