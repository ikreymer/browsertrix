from handlers import WebRecorderHandler, SavePageNowHandler

def get_config():
    config = {}
    config['handlers'] = {
     'ia-save': SavePageNowHandler(),
     'webrecorder': WebRecorderHandler(),
     'test': WebRecorderHandler('https://webrecorder.io/preview/', desc='WebRecorder Test Preview (Not Recording)')
    }

    config['default_handler'] = 'ia-save'

    config['redis_url'] = 'redis://redis_1/2'
    config['chrome_host'] = 'chrome{0}_1'
    config['chrome_url_log'] = True

    config['archive_cache_secs'] = 600

    config['archive_page_url_template'] = '/{0}/archivepage'
    config['wait_timeout_secs'] = 30
    return config
