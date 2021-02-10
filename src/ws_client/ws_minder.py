import asyncio
import logging

from .ws_listen import websocket_subscribe

async def resubscribe_client(ws_servers, server, queue_receive):
    '''
    Attempt to reconnect dropped websocket connections to remote servers.

    :param list ws_servers: Connections to websocket servers
    :param dict server: Info on the server that the reconnection attempt will be made to
    :param asyncio.queues.Queue queue_receive: Queue for incoming websocket messages
    :return: Connections to websocket servers
    :rtype: list
    '''
    logging.warning(f"WS connection to {server['url']['url']} closed. Attempting to reconnect. Retry counter: {server['retry_count']}")
    ws_servers.append(
        {
            'task': asyncio.create_task(
                websocket_subscribe(server['url'], queue_receive), name=str("WS_LISTEN: " + server['url']['url'])
            ),
            'url': server['url'],
            'retry_count': server['retry_count'] + 1,
        }
    )
    ws_servers.remove(server)
    return ws_servers

async def mind_tasks(ws_servers, queue_receive, settings):
    '''
    Check task loop & restart websocket clients if needed.

    :param list ws_servers: Connections to websocket servers
    :param asyncio.queues.Queue queue_receive: Queue for incoming websocket messages
    :param settings: File with necessary variables defined
    '''
    while True:
        await asyncio.sleep(settings.WS_RETRY)
        for server in ws_servers:
            if server['task'].done() and server['retry_count'] <= settings.MAX_CONNECT_ATTEMPTS:
                ws_servers = await resubscribe_client(ws_servers, server, queue_receive)
