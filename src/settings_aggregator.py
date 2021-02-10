'''
Variables
'''
#### ------------------- General Settings ------------------- ####
LOG_FILE = "../aggregator.log" # Log file location
ASYNCIO_DEBUG = False # Debug the asyncio loop

#### ------------------- WS Client Settings ------------------- ####
WS_RETRY = 10 # Time in seconds to wait before trying to reconnect to a websocket server
MAX_CONNECT_ATTEMPTS = 500 # Max number of tries to attempt to call a remote websocket server

UNIQUE_MESSAGE_KEY = 'signature' # Key in JSON WS response used to identify duplicate messages

URLS = [
    {"url": "wss://xrpl.ws:443", "ssl_verify": True},
    {"url": "wss://s1.ripple.com:443", "ssl_verify": True},
    {"url": "wss://lco-xrpl-hub1.cabbit.tech:443", "ssl_verify": True},
]

#### ------------------- WS Server Settings ------------------- ####
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8000

SENT_MESSAGES_MAX_LENGTH = 50000 # n outbound validations to store to avoid sending duplicates
