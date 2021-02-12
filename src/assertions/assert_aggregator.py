def check_aggregator_settings(settings):
    '''
    Ensure the aggregator has the necessary settings to run.

    :param settings: Configuration file
    '''
    for i in settings.URLS:
        assert (isinstance(i['ssl_verify'], bool)), "ssl_verify type must be a boolean."
        assert (isinstance(i['url'], str)), "URLs must be strings."
