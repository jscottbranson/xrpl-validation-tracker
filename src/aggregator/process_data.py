'''Listen for incoming websocket messages. When messages are received in the queue,
verify they haven't already been sent out to clients connected to the outbound server.
Novel messages are transferred to the outbound queue.
'''
import asyncio
import logging

async def process_data(queue_receive, queue_send, settings):
    '''
    Process data fed from websocket connections into the queue.

    :param asyncio.queues.Queue queue_receive: Queue for incoming websocket messages
    :param asyncio.queues.Queue queue_send: Queue for outgoing websocket messages
    '''
    # To-do: clean out queue_send, in case a client isn't connected
    queue_r_max = 0
    queue_s_max = 0
    sent_message_tracking = []
    unique_key = 'message'

    for i in settings.UNIQUE_MESSAGE_KEY:
        unique_key = unique_key + "['" + i + "']"

    # Listen for messages
    while True:
        message = await queue_receive.get()

        # The below lines are just for debugging
        queue_r_size = queue_receive.qsize()
        if queue_r_size > queue_r_max:
            queue_r_max = queue_r_size
            logging.info(f"New record high for the incoming message queue size: {queue_r_size}")
        queue_s_size = queue_send.qsize()
        if queue_s_size > queue_s_max:
            queue_s_max = queue_s_size
            logging.info(f"New record high for the outgoing message queue size: {queue_s_size}")

        # Remove validated_ledgers field from ledger subscription messages, as
        # that field is node specific and thus not aggregation-friendly
        if message['type'] == 'ledgerClosed' and 'validated_ledgers' in message:
            del message['validated_ledgers']

        try:
            # Add unique messages to the queue
            if eval(unique_key) not in sent_message_tracking:
                await queue_send.put(message)
                sent_message_tracking.append(eval(unique_key))
        except KeyError:
            # Ignore unexpected response messages
            continue
        except KeyboardInterrupt:
            break

        # Cull the sent_message_tracking list
        if len(sent_message_tracking) >= settings.SENT_MESSAGES_MAX_LENGTH:
            half_list = settings.SENT_MESSAGES_MAX_LENGTH / 2
            logging.info(f"Sent message list >= {settings.SENT_MESSAGES_MAX_LENGTH} items. Deleting {half_list} items.")
            del sent_message_tracking[0:int(half_list)]
            logging.info(f"Sent message list pruned. Current length: {len(sent_message_tracking)}.")
