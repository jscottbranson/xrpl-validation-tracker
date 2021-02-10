import asyncio
import json
import logging
import ssl

import websockets

SUBSCRIPTION_COMMAND = {"command": "subscribe", "streams": ["validations"]}

async def create_ws_object(url):
    '''
    Check if SSL certificate verification is enabled, then create a ws accordingly.

    :param dict url: URL and SSL certificate verification settings
    :return: A websocket connection
    '''
    if url['ssl_verify'] is False and url['url'][0:4].lower() == 'wss:':
        ssl_context = ssl.SSLContext()
        ssl_context.verify_mode = ssl.CERT_NONE
        return websockets.connect(url['url'], ssl=ssl_context)
    elif url['ssl_verify'] is True or url['url'][0:3].lower() == 'ws:':
        return websockets.connect(url['url'])
    else:
        logging.error(f"Error determining SSL/TLS settings for URL: {url}")
        return

async def websocket_subscribe(url, queue_receive):
    '''
    Connect to a websocket address using TLS settings specified in 'url'.
    Keep the socket open, and add unique validation subscription response messages to
    the queue.

    :param dict url: URL and SSL certificate verification settings
    :param asyncio.queues.Queue queue_receive: Queue for incoming websocket messages
    '''
    logging.info(f"Attempting to connect to: {url['url']}")

    # Check to see if a custom SSLContext is needed to ignore cert verification
    websocket_connection = await create_ws_object(url)

    if websocket_connection:
        try:
            async with websocket_connection as ws:
                # Subscribe to the validation stream
                await ws.send(json.dumps(SUBSCRIPTION_COMMAND))
                logging.info(f"Subscribed to: {url['url']}")
                while True:
                    # Listen for response messages
                    data = await ws.recv()
                    try:
                        data = json.loads(data)
                        # Discard validations without 'master_key', as they were sent from a node
                        # that is running outdated software.
                        if data['type'] == "validationReceived" and 'master_key' in data:
                            await queue_receive.put(data)
                    except KeyError as error:
                        # Ignore messages that don't contain 'type' key.
                        pass
                    except (
                            json.JSONDecodeError,
                    ) as error:
                        logging.warning(f"{url['url']}. Unable to decode JSON: {data}. Error: {error}")
                        break
        except (
                TimeoutError,
                ConnectionResetError,
                ConnectionRefusedError,
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK,
                websockets.exceptions.InvalidMessage,
        ) as error:
            logging.warning(f"An exception: ({error}) resulted in the websocket connection to: {url['url']} being closed.")
        except () as error:
            logging.warning(f"Connection to {url['url']} refused with error: {error}.")
