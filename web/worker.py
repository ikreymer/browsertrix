from redis import StrictRedis
from redis.utils import pipeline

from browser import ChromeBrowser, FirefoxBrowser

import json
import sys
import logging
import socket
import os

from config import get_config


def get_avail_browser(config, rc, browser_type):
    key = os.environ['NODE_KEY']
    while True:
        try:
            host = rc.blpop(key, 10)
            if not host:
                continue

            host = host[1]

            logging.debug('Got host ' + host)

            browser = create_browser(host, config, browser_type)
            logging.debug('Mapped to ' + host)
            return browser
        except Exception as e:
            logging.debug(e)
            logging.debug('Failed to map to ' + host)



def create_browser(host, config, browser_type):
    if browser_type == 'chrome':
        browser = ChromeBrowser(host, config.get('chrome_url_log', False))
    elif browser_type == 'firefox':
        browser = FirefoxBrowser(host, False)
    else:
        raise Exception('Invalid Browser Type: ' + str(browser_type))

    return browser


def get_cache_key(archive, browser_type, url):
    """ Return redis key for given url and cache"""
    return 'r:' + browser_type + ':' + archive + ':' + url


def get_wait_key(archive, browser_type, url):
    """ Redis key for pending operation"""
    return 'w:' + browser_type + ':' + archive + ':' + url


def get_queue_key(browser_type):
    return 'q:urls:' + browser_type


def init_redis(config):
    """ Init redis from config, with fallback to localhost
    """
    try:
        rc = StrictRedis.from_url(config['redis_url'])
        rc.ping()
    except:
        rc = StrictRedis.from_url('redis://localhost/')
        rc.ping()

    return rc


def init(browser_type):
    """ Initialize the uwsgi worker which will read urls to archive from redis queue
    and use associated web driver to connect to remote web browser
    """
    logging.basicConfig(format='%(asctime)s: [%(levelname)s]: %(message)s',
                        level=logging.DEBUG)
    logging.debug('WebDriver Worker Started')

    config = get_config()

    archives = config['archives']

    rc = init_redis(config)

    browser = get_avail_browser(config, rc, browser_type)

    run(rc, browser, archives, config, browser_type)


def run(rc, browser, archives, config, browser_type):
    """ Read from redis queue in a loop and use associated web driver
    to load page on demand
    """
    url = None
    queue_key = get_queue_key(browser_type)
    logging.debug(queue_key)

    while True:
        cmd = rc.blpop(queue_key, 10)

        if not cmd:
            continue

        val= json.loads(cmd[1])
        archive = val['archive']
        url = val['url']

        result_key = get_cache_key(archive, browser_type, url)
        wait_key = get_wait_key(archive, browser_type, url)

        try:
            result = archives[archive](browser, url)
            cache_time = config['archive_cache_secs']
        except Exception as e:
            import traceback
            traceback.print_exc()

            result = {'archived': False, 'error': {'msg': str(e) }}
            cache_time = config['err_cache_secs']

        json_result = json.dumps(result)
        actual_url = result.get('actual_url')

        with pipeline(rc) as pi:
            if actual_url and actual_url != url:
                actual_key = get_cache_key(archive, browser_type, actual_url)
                pi.setex(actual_key, cache_time, json_result)

            pi.setex(result_key, cache_time, json_result)

            pi.rpush(wait_key, 1)
            pi.expire(wait_key, cache_time)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        browser = 'chrome'
    else:
        browser = sys.argv[1]

    init(browser)

