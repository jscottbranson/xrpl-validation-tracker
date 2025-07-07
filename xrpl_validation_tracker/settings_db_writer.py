'''
Variables
'''
import logging

#### ------------------ General Settings #### ------------------
LOG_FILE = "../database_writer.log"
LOG_LEVEL = logging.WARNING
DATABASE_LOCATION = "../validations.sqlite3"
ASYNCIO_DEBUG = False

SENT_MESSAGES_MAX_LENGTH = 20000 # n messages to retain to avoid duplicate DB queries
#### ------------------ Websocket Client Settings #### ------------------
WS_RETRY = 5 # Time in seconds to wait before trying to respawn a websocket connection
MAX_CONNECT_ATTEMPTS = 50000 # Max numbers of tries to attempt to call a remote websocket server
WS_SUBSCRIPTION_COMMAND = {} # Command to send to websocket servers upon connection

URLS = [
    {'url': "ws://127.0.0.1:8000", "ssl_verify": False},
]
