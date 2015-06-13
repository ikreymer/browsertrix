from bottle import route, Route, request, default_app, view, HTTPError, response

from redis import StrictRedis
from redis.utils import pipeline

import json
import uwsgi
import os
import logging
import requests

from config import get_config
from worker import get_cache_key, get_wait_key, init_redis

application = None

ERROR_RESP = {'archived': False, 'queued': False, 'error': {'other': 'unknown'}}


def init():
    """ Init the application and add routes """

    logging.basicConfig(format='%(asctime)s: [%(levelname)s]: %(message)s',
                        level=logging.DEBUG)

    global theconfig
    theconfig = get_config()

    global rc
    rc = init_redis(theconfig)

    app = default_app()

    return app



@route(['/', '/index.html', '/index.htm'])
@view('index')
def home():
    return {'handlers': theconfig['handlers'],
            'default_handler': theconfig.get('default_handler')}



def get_url_and_handler():
    url = request.query.get('url')

    handler = request.query.get('handler')

    if not url:
        raise HTTPError(status=400, body='No url= specified')

    if handler not in theconfig['handlers']:
        raise HTTPError(status=400, body='No archiving handler {0}'.format(handler))

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    return url, handler


@route('/archivepage')
def archive_page():
    url, handler = get_url_and_handler()

    response_key = get_cache_key(handler, url)
    wait_key = get_wait_key(handler, url)

    result = None

    if not rc.exists(response_key):
        cmd = dict(request.query)
        cmd['url'] = url

        num = rc.incr('total_urls')
        cmd['num'] = num

        cmd = json.dumps(cmd)

        with pipeline(rc) as pi:
            waiting_str = {'archived': False,
                           'queued': True,
                           'num': num}

            pi.set(response_key, json.dumps(waiting_str))
            pi.rpush('q:urls', cmd)

        rc.blpop(wait_key, theconfig['wait_timeout_secs'])

    result = rc.get(response_key)

    if result:
        result = json.loads(result)

        if 'queued' in result:
            result['queue_pos'] = 0
            front = rc.lindex('q:urls', 0)
            if front:
                front = json.loads(front)
                front_num = front.get('num', 0)

                # pos == 1 implies this url is next up
                # pos <= 0 implies this url was removed from queue and is being processed
                pos = result['num'] - front_num + 1
                result['queue_pos'] = pos
        else:
            result['ttl'] = rc.ttl(response_key)
    else:
        result = ERROR_RESP

    return result


@route('/download')
def download():
    url, handler = get_url_and_handler()

    response_key = get_cache_key(handler, url)

    result = rc.get(response_key)
    if not result:
        raise HTTPError(status=404, body='Url Not Archived')

    result = json.loads(result)
    if not 'download_url' in result:
        raise HTTPError(status=404, body='Download Not Available')

    headers = {}
    session = result.get('download_session')

    if session:
        headers['Cookie'] = session

    r = requests.get(result['download_url'],
                     headers=headers,
                     stream=True)

    if r.status_code != 200:
        raise HTTPError(status=400, body='Invalid Download Result: {0} {1}'.format(r.status_code, r.reason))

    pass_headers = ('Content-Disposition', 'Content-Length', 'Content-Type')

    for h in pass_headers:
        response.set_header(h, r.headers.get(h))

    response.body = r.iter_content()
    return response


application = init()
