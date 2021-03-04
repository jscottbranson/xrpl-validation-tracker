'''
Validate domain, UNL status, and other info for keys stored in an exiting database.
'''

import asyncio
import json
import logging
import socket
import sqlite3
import time

import aiohttp
import pytomlpp
import websockets

from supplemental_data.sqlite3_connection import create_db_connection
from db_writer.sqlite_writer import sql_write
from ws_client.ws_listen import create_ws_object
from xrpl_unl_parser.parse_unl import unl_parser

class DomainVerification:
    '''
    Query the manifests and TOML files to find and verify domains.
    '''
    def __init__(self):
        self.db_connection = None
        self.keys_new = []
        self.master_keys = None
        self.dunl_keys = None
        self.settings = None

    async def write_ma_keys(self, data):
        '''
        Write the supplemental data for the master keys into the database.

        :param list data: Aggregated SQL data to write
        '''
        logging.info(f"Preparing to write: {len(data)} keys to the master_key DB.")
        self.db_connection.executemany(
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
            data
        )
        logging.info(f"Wrote: {len(data)} keys to the master_key DB.")

    async def write_eph_keys(self, data):
        '''
        Write the supplemental data for ephemeral keys into the database.

        :param list data: Aggregated SQL data to write
        '''
        logging.info(f"Preparing to write: {len(data)} keys to the ephemeral_key DB.")
        self.db_connection.executemany(
            '''
            INSERT OR REPLACE INTO ephemeral_keys (
                ephemeral_key,
                master_key,
                sequence
            )
            SELECT ?, rowid, ? FROM master_keys WHERE master_key=?
            ''',
            data
        )
        logging.info(f"Wrote: {len(data)} keys to the ephemeral_key DB.")

    async def write_to_db(self):
        '''
        Write the supplemental data for the master keys into the database.
        '''
        data_m = []
        data_e = []

        for i in self.keys_new:
            data_m.append(
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
            data_e.append(
                (
                    i['ephemeral_key'],
                    i['sequence'],
                    i['key']
                )
            )

        await self.write_ma_keys(data_m)
        await self.write_eph_keys(data_e)

        self.db_connection.commit()
        self.db_connection.close()
        logging.info("Database connection closed.")

    async def get_manifest(self, key):
        '''
        Query the manifest for a given key.

        :param str key: Master key to query
        '''
        manifest = None
        query_attempt = 1
        query = json.dumps(
            {
                "command": "manifest",
                "public_key": key
            })

        for url in self.settings.MANIFEST_QUERY_WS:
            if not manifest:
                try:
                    websocket_connection = await create_ws_object(url)
                    if websocket_connection:
                        async with websocket_connection as wsocket:
                            await wsocket.send(query)
                            manifest = await wsocket.recv()
                    manifest = json.loads(manifest)['result']
                    #logging.info(f"Successfully retrieved the manifest for {key}.")
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
                #logging.info(f"Retrieved manifest for validator {key} using server: {url}.")
                pass

            return manifest

    async def get_db_connection(self):
        '''
        Create the database connection.
        '''
        self.db_connection = create_db_connection(self.settings.DATABASE_LOCATION)

    async def get_master_keys(self):
        '''
        Retrieve master keys from the database.

        '''
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM master_keys",)
        self.master_keys = cursor.fetchall()
        logging.info(f"Retrieved: {len(self.master_keys)} master keys from the database.")
        self.db_connection.close()
        logging.info("Database connection closed.")

    async def get_dunl_keys(self):
        '''
        Retrieve the dUNL from a remote site.
        '''
        logging.info(f"Preparing to retrieve the dUNL from {self.settings.DUNL_ADDRESS}.")
        self.dunl_keys = json.loads(
            unl_parser(
                self.settings.DUNL_ADDRESS
            )
        )['public_validation_keys']
        logging.info(f"Retrieved the dUNL, which contains: {len(self.dunl_keys)} keys.")

    async def make_keys_list(self):
        '''
        Verify if a node is in the dUNL then make an initial list of keys.
        '''
        for key in self.master_keys:
            if key[0] in self.dunl_keys:
                dunl = True
            elif key[0] not in self.dunl_keys:
                dunl = False
            self.keys_new.append(
                {
                    'key': key[0],
                    'ephemeral_key': '',
                    'sequence': int(),
                    'domain': key[1],
                    'dunl': dunl,
                    'network': '',
                    'server_country': '',
                    'owner_country': '',
                    'toml_verified': False
                }
            )

    async def check_toml(self, key):
        '''
        Attempt to retrieve and parse a TOML file for a domain provided through a manifest query.

        :param dict key: Validation public key, domain, and other info
        '''
        url = "https://" + key['domain'] + "/.well-known/xrp-ledger.toml"
        validators = []
        logging.info(f"Preparing to retrieve TOML for: {key['domain']}.")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        response_content = await response.text()
                        validators = pytomlpp.loads(response_content)['VALIDATORS']
                        for i in validators:
                            if i['public_key'] == key['key']:
                                try:
                                    key['toml_verified'] = True
                                    key['network'] = i['network'].lower()
                                    key['owner_country'] = i['owner_country'].lower()
                                    key['server_country'] = i['server_country'].lower()
                                    logging.info(f"Successfully retrieved and parsed the TOML for: {key['domain']}.")
                                except (KeyError) as error:
                                    logging.info(f"TOML file for: {key['domain']} was missing one or more keys: {error}.")
                                    continue
                            else:
                                # To-do: Check to see if novel keys are listed in the TOML.
                                # Then use the manifest verify their domains.
                                logging.info(f"An additional validator key was detected while querying {key['domain']}.")
        except (
                pytomlpp._impl.DecodeError,
                aiohttp.client_exceptions.ClientError,
                aiohttp.client_exceptions.ClientResponseError,
                aiohttp.client_exceptions.ClientConnectionError,
                aiohttp.client_exceptions.ClientConnectorError,
                aiohttp.client_exceptions.ClientConnectorCertificateError,
        ) as error:
            logging.info(f"Unable to retrieve xrp-ledger.toml for: {key['domain']}. Error: {error}.")

        return key

    async def get_domain(self, key):
        '''
        Retrieve domains from a manifest and verify them via TOML.

        :param dict key: key, domain, dunl
        '''
        manifest = await self.get_manifest(key['key'])
        manifest = manifest['details']
        domain = manifest['domain']
        key['ephemeral_key'] = manifest['ephemeral_key']
        key['sequence'] = manifest['seq']

        if domain:
            key['domain'] = domain.lower()
            key = await self.check_toml(key)
        return key

    async def run_verification(self, settings):
        '''
        Run the script.

        :param settings: Configuration file.
        '''
        self.settings = settings
        while True:
            self.keys_new = []
            try:
                logging.info(f"Sleeping for {self.settings.SLEEP_CYCLE} seconds.")
                time_start = time.time()
                await asyncio.sleep(self.settings.SLEEP_CYCLE)
                logging.info("Preparing to get supplemental data.")
                await self.get_db_connection()
                await self.get_master_keys()
                await self.get_dunl_keys()
                if self.dunl_keys and self.master_keys:
                    await self.make_keys_list()
                if self.keys_new:
                    domain_tasks = [self.get_domain(key) for key in self.keys_new]
                    self.keys_new = await asyncio.gather(*domain_tasks)
                    await self.get_db_connection()
                    await self.write_to_db()
                    logging.info(f"Supplemental data cycle completed in {round(time.time() - time_start, 2)} seconds.")
            except (
                    KeyError,
                    AttributeError,
                    NameError,
                    TypeError,
                    ConnectionError,
            ) as error:
                logging.warning(f"A general error: {error} was encountered Continuing.")
                continue
            except sqlite3.OperationalError as error:
                logging.warning(f"SQLite3 error: {error}.")
                continue
            except KeyboardInterrupt:
                break

