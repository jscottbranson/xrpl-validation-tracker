'''
Listen for incoming websocket messages. When messages are received in the queue,
verify they haven't already been sent out to clients connected to the outbound server.
Novel messages are transferred to the outbound queue.
'''
import asyncio
import logging

class DataProcessor:
    '''
    Pass unique messages from the receiving queue into the send queue.

    :param asyncio.queues.Queue queue_receive: Queue for incoming websocket messages
    :param asyncio.queues.Queue queue_send: Queue for outgoing websocket messages
    :param settings: settings file
    '''
    def __init__(self, queue_receive, queue_send, settings):
        self.queue_receive = queue_receive
        self.queue_send = queue_send
        self.settings = settings
        self.queue_r_max = 0
        self.queue_s_max = 0
        # Change sent_message_tracking to a set?
        self.sent_message_tracking = []

    async def prune_sent_tracking(self):
        '''
        Cull the sent message tracking lists.
        '''
        if len(self.sent_message_tracking) >= self.settings.SENT_MESSAGES_MAX_LENGTH:
            half_list = self.settings.SENT_MESSAGES_MAX_LENGTH / 2
            logging.info(f"Sent message list >= {self.settings.SENT_MESSAGES_MAX_LENGTH} items. Deleting {half_list} items.")
            del self.sent_message_tracking[0:int(half_list)]

    async def add_message_to_queue(self, message, unique_key):
        '''
        Pass unique messages to queue_send.

        :param dict message: Message from a remote websocket server
        :param str unique_key: Unique key used to avoid adding duplicate messages to the outbound queue.
        '''
        if message[unique_key] not in set(self.sent_message_tracking):
            await self.queue_send.put(message)
            self.sent_message_tracking.append(message[unique_key])

    async def send_outgoing_messages(self, message):
        '''
        Evaluate unique messages & move them from queue_receive to queue_send.

        :param dict message: Message from a remote websocket server
        '''
        if message['type'] == 'validationReceived':
            await self.add_message_to_queue(message, 'signature')
        elif message['type'] == 'ledgerClosed':
            await self.add_message_to_queue(message, 'ledger_hash')
        elif message['type'] == "response":
            pass

    async def remove_node_specific_fields(self, message):
        '''
        Removed fields that are specific to individual nodes, rather than the ledger generally.
        For example, `validated_ledgers` in the ledger subscription messages refer to the number of
        ledgers on the remote websocket server. Subscribing to multiple WS servers makes it
        difficult to track unique messages if messages contain node specific info.
        '''
        if message['type'] == 'ledgerClosed' and 'validated_ledgers' in message:
            del message['validated_ledgers']
        return message

    async def log_record_queue_size(self):
        '''
        Track queue size and log when the send or receive queue size sets a new record.

        :param int queue_r_size: Number of items in the receiving queue
        :param int queue_s_size: Number of items in the sending queue
        '''
        if self.queue_receive.qsize() > self.queue_r_max:
            self.queue_r_max = self.queue_receive.qsize()
            logging.info(f"New record high for the incoming message queue size: {self.queue_receive.qsize()}")
        if self.queue_send.qsize() > self.queue_s_max:
            self.queue_s_max = self.queue_send.qsize()
            logging.info(f"New record high for the outgoing message queue size: {self.queue_send.qsize()}")

    async def process_data(self):
        '''
        Process data fed from websocket connections into the queue.
        '''
        # To-do: clean out queue_send, in case a client isn't connected

        while True:
            try:
                message = await self.queue_receive.get()
                await self.log_record_queue_size()
                message = await self.remove_node_specific_fields(message)
                if 'type' in message:
                    await self.send_outgoing_messages(message)
                await self.prune_sent_tracking()
            except KeyError:
                # Ignore unexpected response messages
                continue
            except KeyboardInterrupt:
                break
