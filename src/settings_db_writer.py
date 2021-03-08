'''
Variables
'''
#### ------------------ General Settings #### ------------------
LOG_FILE = "../database_writer.log"
DATABASE_LOCATION = "../validations.sqlite3"
ASYNCIO_DEBUG = False

# The unique key is used to avoid processing duplicate messages. Specific JSON objects can be targeted by
# adding items to the UNIQUE_MESSAGE_KEY list. For example, ['results', 'item_a'] would target
# json_response['results']['item_a']
# I would imagine this could be solved more eloquently than using `eval`...
UNIQUE_MESSAGE_KEY = []

SENT_MESSAGES_MAX_LENGTH = 50000 # n messages to retain to avoid duplicate DB queries
#### ------------------ Websocket Client Settings #### ------------------
WS_RETRY = 5 # Time in seconds to wait before trying to respawn a websocket connection
MAX_CONNECT_ATTEMPTS = 10000 # Max numbers of tries to attempt to call a remote websocket server
WS_SUBSCRIPTION_COMMAND = {} # Command to send to websocket servers upon connection

URLS = [
    {'url': "ws://127.0.0.1:8000", "ssl_verify": False},
]
