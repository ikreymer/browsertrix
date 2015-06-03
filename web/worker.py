from redis import StrictRedis
from redis.utils import pipeline

from browser import ChromeBrowser

import json
import sys
import uwsgi
import logging

from config import get_config


def init_browser(config):
    """ Initialize the webdriver browser driver
    Currently, supporting chrome only
    TODO: add firefox as well
    """
    mule_id = uwsgi.mule_id()
    host = config.get('chrome_host').format(mule_id)
    browser = ChromeBrowser(host, config.get('chrome_url_log', False))
    return browser


def get_cache_key(name, url):
    """ Return redis key for given url and cache"""
    return 'r:' + name + ':' + url


def init_redis(config):
    """ Init redis from config, with fallback to localhost
    """
    try:
        rc = StrictRedis.from_url(config['redis_url'])
        rc.ping()
    except:
        rc = StrictRedis.from_url('redis://localhost/2')
        rc.ping()

    return rc


def init():
    """ Initialize the uwsgi worker which will read urls to archive from redis queue
    and use associated web driver to connect to remote web browser
    """
    logging.basicConfig(level=logging.DEBUG)
    logging.debug('WebDriver Worker Started')

    config = get_config()

    handlers = config['handlers']

    rc = init_redis(config)
    browser = None

    try:
        browser = init_browser(config)
        run(rc, browser, handlers, config)
    finally:
        if browser:
            try:
                browser.close()
            except:
                pass


def run(rc, browser, handlers, config):
    """ Read from redis queue in a loop and use associated web driver
    to load page on demand
    """
    url = None
    while True:
        try:
            cmd = rc.brpop('q:urls', 10)

            if not cmd:
                continue

            name, url = cmd[1].split(' ')

            result = handlers[name](browser, url)

            json_result = json.dumps(result)
            actual_url = result.get('actual_url')

            with pipeline(rc) as pi:
                if actual_url and actual_url != url:
                    actual_key = get_cache_key(name, actual_url)
                    pi.lpush(actual_key, json_result)
                    pi.expire(actual_key, config['archive_cache_secs'])

                url_key = get_cache_key(name, url)
                pi.lpush(url_key, json_result)
                pi.expire(url_key, config['archive_cache_secs'])
        except Exception as e:
            import traceback
            traceback.print_exc()
            if url:
                rc.delete('r:' + url)


if __name__ == "__main__":
    init()

