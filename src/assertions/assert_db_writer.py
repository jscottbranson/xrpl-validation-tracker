def check_db_writer_settings(settings):
    '''
    Ensure the proper settings are available to run the db_writer module.

    :param settings: Configuration file
    '''
    for i in settings.URLS:
        assert (isinstance(i['ssl_verify'], bool)), "ssl_verify type must be a boolean."
        assert (isinstance(i['url'], str)), "URLs must be strings."
