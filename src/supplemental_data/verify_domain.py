'''
Validate domain, UNL status, and other info for keys stored in an exiting database.
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

    async def db_write_keys(self):
        '''
        Write the supplemental data into the database.

        :param connection: SQLite3 connection
        '''
        logging.info(f"Preparing to write: {len(self.keys_new)} keys to the master_key DB.")
        sql_data = []
        for i in self.keys_new:
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
            sql_data
        )

        self.db_connection.commit()
    #    connection.close()
        logging.info("Updated master_key table with supplemental data.")
        self.db_connection.close()
        logging.info("Database connection successfully closed.")

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
        logging.info(f"Database connection established to {self.settings.DATABASE_LOCATION}")

    async def get_master_keys(self):
        '''
        Retrieve master keys from the database.

        '''
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM master_keys",)
        self.master_keys = cursor.fetchall()
        logging.info(f"Retrieved: {len(self.master_keys)} master keys from the database.")

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
                            key['toml_verified'] = True
                            key['network'] = i['network'].lower()
                            key['owner_country'] = i['owner_country'].lower()
                            key['server_country'] = i['server_country'].lower()
                            logging.info(f"Successfully retrieved and parsed the TOML for: {key['domain']}.")
                        else:
                            # To-do: There could be a check to see if keys we don't know about are listed in the TOML.
                            # The manifest for those keys could be used to verify the domain.
                            logging.info(f"An additional validator key was detected while querying {key['domain']}.")
                    except KeyError as error:
                        continue
        except requests.exceptions.RequestException as error:
            logging.warning(f"Unable to retrieve xrp-ledger.toml for: {url}. Error {error}.")
        return key

    async def get_domain(self, key):
        '''
        Retrieve domains from a manifest and verify them via TOML.

        :param dict key: key, domain, dunl
        '''
        manifest = await self.get_manifest(key['key'])
        domain = manifest['details']['domain']

        if domain:
            key['domain'] = domain.lower()
            logging.info(f"Preparing to retrieve the TOML for {key}.")
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
                    await self.db_write_keys()
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

