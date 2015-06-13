from redis import StrictRedis
from redis.utils import pipeline

from browser import ChromeBrowser

import json
import sys
import logging
import socket
import os

from config import get_config


def get_avail_browser(config, rc):
    key = os.environ['NODE_KEY']
    while True:
        try:
            host = rc.blpop(key, 10)
            if not host:
                continue

            host = host[1]

            logging.debug('Got host ' + host)

            browser = create_browser(host, config)
            logging.debug('Mapped to ' + host)
            return browser
        except:
            logging.debug('Failed to map to ' + host)



def create_browser(host, config):
    browser = ChromeBrowser(host, config.get('chrome_url_log', False))
    return browser


def get_cache_key(name, url):
    """ Return redis key for given url and cache"""
    return 'r:' + name + ':' + url


def get_wait_key(name, url):
    """ Redis key for pending operation"""
    return 'w:' + name + ':' + url


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


def init():
    """ Initialize the uwsgi worker which will read urls to archive from redis queue
    and use associated web driver to connect to remote web browser
    """
    logging.basicConfig(format='%(asctime)s: [%(levelname)s]: %(message)s',
                        level=logging.DEBUG)
    logging.debug('WebDriver Worker Started')

    config = get_config()

    handlers = config['handlers']

    rc = init_redis(config)
    browser = None

 #   browser = map_to_browser(config)
    browser = get_avail_browser(config, rc)
    run(rc, browser, handlers, config)

def run(rc, browser, handlers, config):
    """ Read from redis queue in a loop and use associated web driver
    to load page on demand
    """
    url = None
    while True:
        import time
        time.sleep(25)
        cmd = rc.blpop('q:urls', 10)

        if not cmd:
            continue

        val= json.loads(cmd[1])
        name = val['handler']
        url = val['url']

        result_key = get_cache_key(name, url)
        wait_key = get_wait_key(name, url)

        try:
            result = handlers[name](browser, url)
            cache_time = config['archive_cache_secs']
        except Exception as e:
            import traceback
            traceback.print_exc()

            result = {'archived': False, 'error': {'other': str(e) }}
            cache_time = config['err_cache_secs']

        json_result = json.dumps(result)
        actual_url = result.get('actual_url')

        with pipeline(rc) as pi:
            if actual_url and actual_url != url:
                actual_key = get_cache_key(name, actual_url)
                pi.setex(actual_key, cache_time, json_result)

            pi.setex(result_key, cache_time, json_result)

            pi.rpush(wait_key, 1)
            pi.expire(wait_key, cache_time)


if __name__ == "__main__":
    init()

