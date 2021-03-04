'''
Variables
'''
#### ------------------ General Settings #### ------------------
LOG_FILE = "../supplemental_data.log"
DATABASE_LOCATION = "../validation_database.db"
ASYNCIO_DEBUG = False

SLEEP_CYCLE = 20 # Time (seconds) to sleep between runs

DUNL_ADDRESS = "https://vl.ripple.com" # Address where the dUNL is served

#List of URLs to query for manifests
MANIFEST_QUERY_WS = [
    {'url': 'wss://marvin.alloy.ee', 'ssl_verify': False},
]
