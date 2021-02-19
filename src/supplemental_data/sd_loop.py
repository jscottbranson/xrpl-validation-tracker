'''
asyncio task loop to validate ledger close time and UNL status
using keys stored in an exiting database.
'''

import asyncio
import logging
import supplemental_data.verify_domain as verify_domain

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
            loop.run_until_complete(
                verify_domain.DomainVerification().run_verification(settings)
            )
            loop.run_forever()
        except KeyboardInterrupt:
            logging.critical("Keyboard interrupt detected. Exiting supplemental data logging.")
            break
