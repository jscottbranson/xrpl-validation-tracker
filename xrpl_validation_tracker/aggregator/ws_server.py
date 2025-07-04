'''
Listen for messages in the queue, then dispatch them to connected websocket clients.
'''
import asyncio
import logging
import json
import time
import websockets
from websockets.protocol import State

class WsServer:
    '''
    Websocket server.
    '''
    def __init__(self):
        self.clients = set()
        self.disconnected_clients = []
        self.queue_send = None

    async def remove_clients(self):
        '''
        Remove clients who are no longer connected from the self.clients set.

        :param list client: Client(s) that are disconnected
        '''
        try:
            logging.info(f"Attempting to remove: {len(self.disconnected_clients)} disconnected clients from the list of connected clients.")
            self.clients = set(self.clients) - set(self.disconnected_clients)
            logging.info(f"There are: {len(self.clients)} clients in the WS server connected clients list.")
        except KeyError as error:
            logging.warning(f"Error removing disconnected WS client: {error}.")
        self.disconnected_clients = []

    async def outgoing_server(self, ws_client):
        '''
        Listen for messages in the outgoing queue, then dispatch
        them to connected clients.

        :param ws_client: Websocket client connection
        '''
        try:
            self.clients.add(ws_client)
            logging.info(f"A new user with IP: {ws_client.remote_address[0]} connected to the WS server.")
            logging.info(f"There are: {len(self.clients)} clients connected to the WS server.")
            while True:
                outgoing_message = json.dumps(await self.queue_send.get())
                if self.clients:
                    for client in self.clients:
                        if client.state == State.OPEN:
                            await client.send(outgoing_message)
                        elif client.state != State.OPEN:
                            self.disconnected_clients.append(client)
                if self.disconnected_clients:
                        await self.remove_clients()
        except (
                AttributeError,
                ConnectionResetError,
                websockets.exceptions.ConnectionClosedError,
        ) as error:
            logging.info(f"WS connection with client address: {ws_client.remote_address[0]} and connection object {ws_client} closed with: {error}.")
        finally:
            self.disconnected_clients.append(ws_client)

    async def start_outgoing_server(self, queue_send, settings):
        '''
        Start listening for client connections.

        :param asyncio.queues.Queue queue_send: Queue for outgoing websocket messages
        '''
        self.queue_send = queue_send
        logging.info(f"Starting the websocket server on IP: {settings.SERVER_IP}:{settings.SERVER_PORT}.")
        await websockets.serve(self.outgoing_server, settings.SERVER_IP, settings.SERVER_PORT)
