'''
Variables
'''
#### ------------------ General Settings #### ------------------
LOG_FILE = "../database_writer.log"
DATABASE = "../validation_database.db"
ASYNCIO_DEBUG = False

#### ------------------ General Settings #### ------------------
WS_RETRY = 5 # Time in seconds to wait before trying to respawn a websocket connection
MAX_CONNECT_ATTEMPTS = 10000 # Max numbers of tries to attempt to call a remote websocket server
UNIQUE_MESSAGE_KEY = 'signature' # Key in JSON WS response used to identify duplicate messages

URLS = [
    {'url': "ws://127.0.0.1:8000", "ssl_verify": False}
]
