'''
asyncio task loop to validate ledger close time and UNL status
using keys stored in an exiting database.
'''

import asyncio
import json
import logging
import socket

import requests
import websockets

from supplemental_data.sqlite3_connection import create_db_connection
from db_writer.sqlite_writer import sql_write
from ws_client.ws_listen import create_ws_object
from xrpl_unl_parser.parse_unl import unl_parser

async def get_manifest(settings, key):
    '''
    Query the manifest for a given key.

    :param settings: Configuration file
    :param str key: Master key to query
    '''
    manifest = None
    query_attempt = 1
    query = json.dumps(
        {
            "command": "manifest",
            "public_key": key
        })

    for url in settings.MANIFEST_QUERY_WS:
        if not manifest:
            try:
                websocket_connection = await create_ws_object(url)
                if websocket_connection:
                    async with websocket_connection as ws:
                        await ws.send(query)
                        manifest = await ws.recv()
                manifest = json.loads(manifest)['result']
            except (
                    TimeoutError,
                    ConnectionResetError,
                    ConnectionRefusedError,
                    websockets.exceptions.InvalidStatusCode,
                    websockets.exceptions.ConnectionClosedError,
                    websockets.exceptions.InvalidMessage,
                    socket.gaierror,
            ) as error:
                logging.warning(f"Error:( {error}) querying manifest for key {key} from server: {url}.")
            query_attempt += 1
        elif manifest:
            logging.info(f"Retrieved manifest for validator {key} using server: {url}.")

        return manifest

def get_master_keys(connection):
    '''
    Retrieve master keys from the database.

    :param settings: Configuration file
    '''
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM master_keys",)
    master_keys = cursor.fetchall()
    logging.info("Retrieved the master keys from the database.")
    return master_keys

async def check_toml(domain):
    '''
    :param str domain: Domain to check
    '''
    url = "https://" + domain + "/.well-known/xrp-ledger.toml"
    try:
        toml = requests.get(url)
        print(toml)
    except requests.exceptions.RequestException:
        logging.warning(f"Unable to retrieve xrp-ledger.toml for: {url}.")

async def get_domain(settings, key):
    '''
    Retrieve domains from a manifest and verify them via TOML.

    :param settings: Configuration file
    :param set key: (key, domain, dunl)
    '''
    manifest = await get_manifest(settings, key[0])
    domain = manifest['details']['domain']

    if domain:
        # Check each domain for a TOML file
        await check_toml(domain)
        key = (key[0], domain, key[2])
    return key

async def _workers(settings):
    '''
    Add tasks to the asyncio loop.

    :param settings: Configuration file
    '''
    connection = create_db_connection(settings.DATABASE_LOCATION)
    logging.info("Database connection established to {settings.DATABASE_LOCATION}.")
    while True:
        try:
            keys_new = []
            await asyncio.sleep(settings.SLEEP_CYCLE)
            dunl_keys = json.loads(unl_parser(settings.DUNL_ADDRESS))['public_validation_keys']
            logging.info(f"Retrieved the dUNL, which contains: {len(dunl_keys)} keys.")

            # Establish the database connection & query the master keys
            db_master_keys = get_master_keys(connection)
            logging.info(f"Retrieved: {len(db_master_keys)} master keys from the database.")

            # Check for dUNL validators
            # Make the set into dictionaries for each validator
            for key in db_master_keys:
                if key[0] in dunl_keys:
                    dunl = True
                elif key[0] not in dunl_keys:
                    dunl = False
                keys_new.append((key[0], key[1], dunl))

            # Get the domains
            domain_tasks = [get_domain(settings, key) for key in keys_new]
            keys_new = await asyncio.gather(*domain_tasks)
        except KeyboardInterrupt:
            break

def sup_data_loop(settings):
    '''
    Run the .asyncio event loop.

    :param settings: Configuration file
    '''
    loop = asyncio.get_event_loop()

    if settings.ASYNCIO_DEBUG is True:
        loop.set_debug(True)
        logging.info("asyncio debugging enabled.")

    while True:
        try:
            loop.run_until_complete(_workers(settings))
            loop.run_forever()
        except KeyboardInterrupt:
            logging.critical("Keyboard interrupt detected. Exiting supplemental data logging.")
            break
