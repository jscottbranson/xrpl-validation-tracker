'''
select which modules to run based on user input, and pass the relevant settings into the asyncio loop.
'''

import argparse
import logging

PARSER = argparse.ArgumentParser(description="Select which module to run.")
PARSER.add_argument("-a", "--aggregator", help="Run the aggregator.", action="store_true")
PARSER.add_argument("-d", "--db_writer", help="Run the db_writer.", action="store_true")
ARGS = PARSER.parse_args()

def config_logging(settings):
    '''
    Configure logging settings.

    :param settings: Configuration file
    '''
    # To-do: Configure log level in settings files.
    logging.basicConfig(
        filename=settings.LOG_FILE,
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format='%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s',
    )
    logging.info(f"Running with arguments: {ARGS}.\nLogging configured successfully.")

def run_db_writer():
    '''
    Run the db_writer module.
    '''
    import settings_db_writer as settings_db_w
    from assertions.assert_db_writer import check_db_writer_settings
    from db_writer.db_asyncio_tasks import start_loop as start_loop_db_w

    config_logging(settings_db_w)
    check_db_writer_settings(settings_db_w)
    start_loop_db_w(settings_db_w)

def run_aggregator():
    '''
    Run the aggregator module.
    '''
    import settings_aggregator as settings_ag
    from assertions.assert_aggregator import check_aggregator_settings
    from aggregator.asyncio_tasks import start_loop as start_loop_ag

    config_logging(settings_ag)
    check_aggregator_settings(settings_ag)
    start_loop_ag(settings_ag)

if __name__ == '__main__':
    if ARGS.aggregator:
        run_aggregator()
    # The following is 'elif', since two modules can't be run at once yet
    elif ARGS.db_writer:
        run_db_writer()
