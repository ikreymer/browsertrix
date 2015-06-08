from handlers import WebRecorderHandler, SavePageNowHandler
from collections import OrderedDict

def get_config():
    config = {}

    handlers = OrderedDict()
    handlers['webrecorder'] = WebRecorderHandler()
    handlers['test'] = WebRecorderHandler('https://webrecorder.io/preview/', desc='Dry Run with <a href="https://webrecorder.io">webrecorder.io</a> (Not Recording)')
    handlers['ia-save'] = SavePageNowHandler()

    config['handlers'] = handlers

    config['default_handler'] = 'test'

    config['redis_url'] = 'redis://redis_1/'
    config['chrome_url_log'] = True

    config['archive_cache_secs'] = 600
    config['err_cache_secs'] = 10

    config['wait_timeout_secs'] = 30
    return config
