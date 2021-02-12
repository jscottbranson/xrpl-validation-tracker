'''Listen for incoming websocket messages. When messages are received in the queue,
verify they haven't already been sent out to clients connected to the outbound server.
Novel messages are transferred to the outbound queue.
'''
import asyncio
import logging

import settings_aggregator as settings

async def prune_sent_list(sent_message_tracking):
    '''
    Chop the sent message tracking list in half, so it doesn't grow infinitely.

    :param list sent_message_tracking: Identify messages already sent to subscribed clients
    :return: Half size list
    :rtype: list
    '''
    # To-do: add an assert that SENT_MESSAGES_MAX_LENGTH is an int

    half_list = settings.SENT_MESSAGES_MAX_LENGTH / 2
    logging.info(f"Sent message list >= {settings.SENT_MESSAGES_MAX_LENGTH} items. Deleting {half_list} items.")
    del sent_message_tracking[0:int(half_list)]
    logging.info(f"Sent message list pruned. Current length: {len(sent_message_tracking)}.")
    return sent_message_tracking

async def process_data(queue_receive, queue_send):
    '''
    Process data fed from websocket connections into the queue.

    :param asyncio.queues.Queue queue_receive: Queue for incoming websocket messages
    :param asyncio.queues.Queue queue_send: Queue for outgoing websocket messages
    '''
    # To-do: clean out queue_send, in case a client isn't connected
    queue_max = 0
    sent_message_tracking = []

    # Listen for messages
    while True:
        message = await queue_receive.get()

        # The below lines are just for debugging
        queue_size = queue_receive.qsize()
        if queue_size > queue_max:
            queue_max = queue_size
            logging.info(f"New record high for the incoming message queue size: {queue_size}")

        try:
            if message[settings.UNIQUE_MESSAGE_KEY] not in sent_message_tracking:
                await queue_send.put(message)
                sent_message_tracking.append(message[settings.UNIQUE_MESSAGE_KEY])
                if settings.VERBOSE == True:
                    print(
                         "Incoming queue length:",
                         queue_size,
                         "Outgoing queue length:",
                         queue_send.qsize(),
                         "Sent message duplicate tracking list length:",
                         len(sent_message_tracking),
                     )
        except KeyError:
            # Ignore unexpected response messages
            pass

        # Cull the sent_message_tracking list
        if len(sent_message_tracking) >= settings.SENT_MESSAGES_MAX_LENGTH:
            sent_message_tracking = await prune_sent_list(sent_message_tracking)
