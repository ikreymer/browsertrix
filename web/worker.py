from redis import StrictRedis
from redis.utils import pipeline

from browser import ChromeBrowser

import json
import sys
import logging
import socket
import os

from config import get_config


def map_to_browser(config):
    """ Initialize the webdriver browser driver
    Currently, supporting chrome only
    TODO: add firefox as well
    """

    seen = set()

    with open('/etc/hosts') as fh:
        for line in fh:
            if 'chrome' in line:
                ip = line.split('\t')[0]
                if ip not in seen:
                    seen.add(ip)
                    try:
                        browser = create_browser(ip, config)
                        logging.debug('Mapped {0} -> {1}'.format(socket.gethostname(), ip))
                        return browser
                    except Exception as e:
                        logging.debug(e)
                        logging.debug('Failed ' + ip)

    logging.debug('NO BROWSER FOUND')
    return None


def get_avail_browser(config, rc):
    key = os.environ['NODE_KEY']
    logging.debug(key)
    while True:
        try:
            host = rc.brpop(key, 10)
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


def get_pending_key(name, url):
    """ Redis key for pending operation"""
    return 'p:' + name + ':' + url


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
    logging.basicConfig(level=logging.DEBUG)
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
        try:
            cmd = rc.brpop('q:urls', 10)

            if not cmd:
                continue

            val = cmd[1].decode('utf-8')

            name, url = val.split(' ')

            result = handlers[name](browser, url)

            json_result = json.dumps(result)
            actual_url = result.get('actual_url')

            with pipeline(rc) as pi:
                if actual_url and actual_url != url:
                    actual_key = get_cache_key(name, actual_url)
                    pi.lpush(actual_key, json_result)
                    pi.expire(actual_key, config['archive_cache_secs'])

                pending_key = get_pending_key(name, url)
                pi.lpush(pending_key, json_result)
                pi.expire(pending_key, config['archive_cache_secs'])
        except Exception as e:
            logging.debug(e)
            import traceback
            traceback.print_exc()
            if url:
                rc.delete('r:' + url)


if __name__ == "__main__":
    #import time
    #while True:
    #    time.sleep(10)
    init()

