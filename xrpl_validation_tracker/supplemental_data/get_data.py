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
import xrpl_unl_manager.utils as unl_utils

class DomainVerification:
    '''
    Query the manifests and TOML files to find and verify domains.
    '''
    def __init__(self):
        self.db_connection = None
        self.keys_new = []
        self.master_keys = None
        self.dunl_keys = set()
        self.settings = None

    async def write_ma_keys(self, data):
        '''
        Write the supplemental data for the master keys into the database.

        :param list data: Aggregated SQL data to write
        '''
        logging.info(f"Preparing to write: {len(data)} keys to the master_key DB.")
        self.db_connection.executemany(
            '''
            UPDATE master_keys
            SET
                domain = ?,
                dunl = ?,
                network = ?,
                server_country = ?,
                owner_country = ?,
                toml_verified = ?
            WHERE master_key = ?
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
            UPDATE ephemeral_keys
            SET
                master_key = (SELECT rowid FROM master_keys WHERE master_key = ?)
            WHERE ephemeral_key = ?
            ''',
            data
        )
        logging.info(f"Wrote: {len(data)} keys to the ephemeral_key DB.")

    async def write_manifests(self, data):
        '''
        Write manifests into the database.

        :param list data: Aggregated SQL data to write
        '''
        logging.info(f"Preparing to write: {len(data)} manifests to the DB.")
        self.db_connection.executemany(
            '''
            INSERT OR IGNORE INTO manifests (
                manifest,
                manifest_sig_master,
                manifest_sig_eph,
                sequence,
                master_key,
                ephemeral_key
            )
            VALUES (?, ?, ?, ?,
                (SELECT rowid FROM master_keys WHERE master_key is ?),
                (SELECT rowid FROM ephemeral_keys WHERE ephemeral_key is ?)
            )
            ''',
            data
        )
        logging.info(f"Wrote: {len(data)} manifests to the DB.")

    async def write_to_db(self):
        '''
        Write the supplemental data for the master keys into the database.
        '''
        data_master = []
        data_ephemeral = []
        data_manifest = []

        for i in self.keys_new:
            data_master.append(
                (
                    i['domain'],
                    i['dunl'],
                    i['network'],
                    i['server_country'],
                    i['owner_country'],
                    i['toml_verified'],
                    i['key']
                )
            )
            data_ephemeral.append(
                (
                    i['key'],
                    i['ephemeral_key']
                )
            )

            data_manifest.append(
                (
                    i['manifest'],
                    i['manifest_sig_master'],
                    i['manifest_sig_eph'],
                    i['sequence'],
                    i['key'],
                    i['ephemeral_key']
                )
            )

        await self.write_ma_keys(data_master)
        await self.write_eph_keys(data_ephemeral)
        await self.write_manifests(data_manifest)

        self.db_connection.commit()
        self.db_connection.close()
        logging.info("Database connection closed.")

    async def get_db_connection(self):
        '''
        Create the database connection.
        '''
        self.db_connection = create_db_connection(self.settings.DATABASE_LOCATION)

    async def http_request(self, url):
        '''
        Return the results from a http request.

        :param str url: Address to connect to
        '''
        response = ''
        session_timeout = aiohttp.ClientTimeout(
            total=None,
            sock_connect=self.settings.HTTP_TIMEOUT,
            sock_read=self.settings.HTTP_TIMEOUT
        )
        try:
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                response = await session.get(url)
                if response.status == 200:
                    return await response.text()

        except (
                aiohttp.client_exceptions.ClientError,
                aiohttp.client_exceptions.ClientResponseError,
                aiohttp.client_exceptions.ClientConnectionError,
                #aiohttp.client_exceptions.ClientConnectorError,
                #aiohttp.client_exceptions.ClientConnectorCertificateError,
        ) as error:
            logging.info(f"Unable to complete HTTP request to URL: {url}. Error: {error}.")

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
                    manifest = json.loads(manifest)
                    # logging.info(f"Successfully retrieved the manifest for {key}.")
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
        self.dunl_keys = set()
        logging.info(f"Preparing to retrieve the dUNL from {self.settings.DUNL_ADDRESS}.")
        dunl = await self.http_request(self.settings.DUNL_ADDRESS)
        #To-do: catch json.loads exceptions
        dunl_keys = unl_utils.decodeValList(json.loads(dunl))
        for i in dunl_keys:
            self.dunl_keys.add(i.decode())
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
                    'domain': key[1],
                    'dunl': dunl,
                    'network': key[3],
                    'server_country': key[4],
                    'owner_country': key[5],
                    'toml_verified': False,
                    'manifest_sig_master': '',
                    'manifest_sig_eph': '',
                    'manifest': '',
                    'sequence': int(),
                }
            )

    async def check_toml(self, key):
        '''
        Attempt to retrieve and parse a TOML file for a domain provided through a manifest query.

        :param dict key: Validation public key, domain, and other info
        '''
        url = "https://" + key['domain'] + "/.well-known/xrp-ledger.toml"
        validators = []
        #logging.info(f"Preparing to retrieve TOML for: {key['domain']}.")
        try:
            response_content = await self.http_request(url)
            validators = pytomlpp.loads(str(response_content))['VALIDATORS']
            for i in validators:
                if i['public_key'] == key['key']:
                    try:
                        key['toml_verified'] = True
                        key['network'] = i['network'].lower()
                        key['owner_country'] = i['owner_country'].lower()
                        key['server_country'] = i['server_country'].lower()
                        #logging.info(f"Successfully retrieved and parsed the TOML for: {key['domain']}.")
                    except (KeyError) as error:
                        logging.info(f"TOML file for: {key['domain']} was missing one or more keys: {error}.")
                        continue
                else:
                    # To-do: Check to see if novel keys are listed in the TOML.
                    # Then use the manifest verify their domains.
                    logging.info(f"An additional validator key was detected while querying {key['domain']}.")
        except (pytomlpp._impl.DecodeError,) as error:
            logging.info(f"Unable to decode the TOML for: {key['domain']}. Error: {error}.")

        return key

    async def get_domain(self, key):
        '''
        Retrieve domains from a manifest and verify them via TOML.

        :param dict key: key, domain, dunl
        '''
        manifest = await self.get_manifest(key['key'])
        manifest_blob = manifest['result']['manifest']
        manifest = manifest['result']['details']
        key['ephemeral_key'] = manifest['ephemeral_key']
        key['sequence'] = manifest['seq']
        decoded_manifest = unl_utils.decodeManifest(manifest_blob)
        key['manifest_sig_master'] = decoded_manifest['master_signature']
        key['manifest_sig_eph'] = decoded_manifest['signature']
        key['manifest'] = manifest_blob

        if manifest['domain']:
            key['domain'] = manifest['domain'].lower()
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
                time_start = time.time()
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
