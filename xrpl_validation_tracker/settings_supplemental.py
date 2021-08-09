'''
Variables
'''
#### ------------------ General Settings #### ------------------
LOG_FILE = "../supplemental_data.log"
DATABASE_LOCATION = "../validations.sqlite3"
ASYNCIO_DEBUG = False

SLEEP_CYCLE = 600 # Time (seconds) to sleep between runs

HTTP_TIMEOUT = 20 # Time (seconds) to wait for HTTP responses

DUNL_ADDRESS = "https://vl.xrplf.org" # Address where the dUNL is served
#DUNL_ADDRESS = "https://vl.ripple.com" # Address where the dUNL is served

#List of URLs to query for manifests
MANIFEST_QUERY_WS = [
    {'url': 'wss://marvin.alloy.ee', 'ssl_verify': False},
]
