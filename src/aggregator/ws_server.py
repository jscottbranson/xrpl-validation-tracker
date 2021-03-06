'''
Listen for messages in the queue, then dispatch them to connected websocket clients.
'''
import asyncio
import logging
import json
import time
import websockets

class WsServer:
    '''
    Websocket server.
    '''
    def __init__(self):
        self.clients = set()
        self.queue_send = None

    async def remove_client(self, client):
        '''
        Remove clients who are no longer connected from the self.clients set.

        :param client: Client that has disconnected
        '''
        logging.info(f"Client: {client.remote_address[0]} disconnected from WS server.")
        try:
            self.clients.remove(client)
        except KeyError:
            logging.warning(f"Error removing {client.remote_address[0]} from list of clients connected to the WS server.")

    async def outgoing_server(self, websocket, path):
        '''
        Listen for messages in the outgoing queue, then dispatch
        them to connected clients.

        :param websocket: Websocket client connection
        '''
        self.clients.add(websocket)
        logging.info(f"A new user with IP: {websocket.remote_address[0]} connected to the WS server.")
        while True:
            try:
                outgoing_message = json.dumps(await self.queue_send.get())
                if self.clients:
                    for client in self.clients:
                        if client.open:
                            await client.send(outgoing_message)
            except (
                    AttributeError,
                    ConnectionResetError,
                    websockets.exceptions.ConnectionClosedError,
            ) as error:
                logging.warning(f"Error with outgoing websocket server: {error}.")
                await self.remove_client(websocket)

            except (websockets.exceptions.ConnectionClosedOK,) as error:
                logging.info(f"WS connection with client: {websocket.remote_address[0]} closed OK.")
                await self.remove_client(websocket)

    async def start_outgoing_server(self, queue_send, settings):
        '''
        Start listening for client connections.

        :param asyncio.queues.Queue queue_send: Queue for outgoing websocket messages
        '''
        self.queue_send = queue_send
        logging.info(f"Starting the websocket server on IP: {settings.SERVER_IP}:{settings.SERVER_PORT}.")
        await websockets.serve(self.outgoing_server, settings.SERVER_IP, settings.SERVER_PORT)
