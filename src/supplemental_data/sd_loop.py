'''
asyncio task loop to validate ledger close time and UNL status
using keys stored in an exiting database.
'''

import asyncio
import json
import logging
import socket
import sqlite3

import requests
import pytomlpp
import websockets

from supplemental_data.sqlite3_connection import create_db_connection
from db_writer.sqlite_writer import sql_write
from ws_client.ws_listen import create_ws_object
from xrpl_unl_parser.parse_unl import unl_parser

async def db_write_keys(keys_new, connection):
    '''
    Write the supplemental data into the database.

    :param list keys_new: Data to be written
    :param connection: SQLite3 connection
    '''
    sql_data = []
    for i in keys_new:
        sql_data.append(
            (
                i['key'],
                i['domain'],
                i['dunl'],
                i['network'],
                i['server_country'],
                i['owner_country'],
                i['toml_verified']
            )
        )
    connection.executemany(
        '''
        INSERT OR REPLACE INTO master_keys (
        master_key,
        domain,
        dunl,
        network,
        server_country,
        owner_country,
        toml_verified
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        ''',
        sql_data
    )

    connection.commit()
#    connection.close()
    logging.info("Updated master_key table with supplemental data.")

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
                    async with websocket_connection as wsocket:
                        await wsocket.send(query)
                        manifest = await wsocket.recv()
                manifest = json.loads(manifest)['result']
                logging.info(f"Successfully retrieved the manifest for {key}.")
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
    return master_keys

async def check_toml(key):
    '''
    :param dict key: Validation public key, domain, and other info
    '''
    url = "https://" + key['domain'] + "/.well-known/xrp-ledger.toml"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            response_content = response.content.decode()
            try:
                validators = pytomlpp.loads(response_content)['VALIDATORS']
            except () as error:
                logging.warning(f"Error: {error} parsing TOML file for domain: {key['domain']}. TOML contents: {response_content}.")
            for i in validators:
                try:
                    if i['public_key'] == key['key']:
                        logging.info(f"Successfully retrieved and parsed the TOML for: {key}.")
                        key['toml_verified'] = True
                        key['network'] = i['network'].lower()
                        key['owner_country'] = i['owner_country'].lower()
                        key['server_country'] = i['server_country'].lower()
                except KeyError as error:
                    continue
    except requests.exceptions.RequestException as error:
        logging.warning(f"Unable to retrieve xrp-ledger.toml for: {url}. Error {error}.")
    return key

async def get_domain(settings, key):
    '''
    Retrieve domains from a manifest and verify them via TOML.

    :param settings: Configuration file
    :param dict key: key, domain, dunl
    '''
    manifest = await get_manifest(settings, key['key'])
    domain = manifest['details']['domain'].lower()

    if domain:
        key['domain'] = domain
        logging.info(f"Preparing to retrieve the TOML for {key}.")
        key = await check_toml(key)
    return key

async def _workers(settings):
    '''
    Add tasks to the asyncio loop.

    :param settings: Configuration file
    '''
    connection = create_db_connection(settings.DATABASE_LOCATION)
    logging.info(f"Database connection established to {settings.DATABASE_LOCATION}.")
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
            for key in db_master_keys:
                if key[0] in dunl_keys:
                    dunl = True
                elif key[0] not in dunl_keys:
                    dunl = False
                keys_new.append(
                    {'key': key[0],
                     'domain': key[1],
                     'dunl': dunl,
                     'network': '',
                     'server_country': '',
                     'owner_country': '',
                     'toml_verified': False}
                )

            # Get the domains
            domain_tasks = [get_domain(settings, key) for key in keys_new]
            keys_new = await asyncio.gather(*domain_tasks)

            # Write the supplemental data into the DB
            logging.info(f"Preparing to write supplemental data to the DB.")
            await db_write_keys(keys_new, connection)
        except KeyboardInterrupt:
            break
        except sqlite3.OperationalError as error:
            logging.warning(f"SQLite3 error: {error}.")

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
