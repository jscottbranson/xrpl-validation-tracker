'''
Add tasks to the asycnio loop.
'''
import asyncio
import logging

from ws_client import ws_listen
from ws_client import ws_minder
from .process_data import process_data
from .ws_server import WsServer

async def spawn_workers(settings):
    '''
    Add tasks to the asyncio loop.

    :param settings: Configuration file
    '''
    ws_servers = []

    # Create queues for websocket messages
    queue_receive = asyncio.Queue(maxsize=0)
    queue_send = asyncio.Queue(maxsize=0)
    logging.info("Adding initial asyncio tasks to the loop.")
    for url in settings.URLS:
        ws_servers.append(
            {
                'task': asyncio.create_task(
                    ws_listen.websocket_subscribe(
                        url, settings.WS_SUBSCRIPTION_COMMAND, queue_receive
                    )
                ),
                'url': url,
                'retry_count': 0,
            }
        )
    asyncio.create_task(
        process_data(queue_receive, queue_send, settings)
    )
    asyncio.create_task(
        WsServer().start_outgoing_server(queue_send, settings)
    )
    asyncio.create_task(
        ws_minder.mind_tasks(ws_servers, queue_receive, settings)
    )
    logging.info("Initial asyncio task list is running.")

def start_loop(settings):
    '''
    Run the asyncio event loop.

    :param settings: Configuration file
    '''
    # Debug asyncio
    if settings.ASYNCIO_DEBUG is True:
        asyncio.get_event_loop().set_debug(True)
        logging.info("asyncio debugging enabled.")

    while True:
        try:
            asyncio.get_event_loop().run_until_complete(spawn_workers(settings))
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            logging.critical("Keyboard interrupt detected. Exiting the aggregator.")
            break
