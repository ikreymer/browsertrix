from bottle import route, Route, request, default_app, view, HTTPError

from redis import StrictRedis
from redis.utils import pipeline

import json
import uwsgi
import os
import logging

from config import get_config
from worker import get_cache_key, get_pending_key, init_redis

application = None


WAITING_STR = json.dumps({'queued': True, 'archived': False})

ERROR_RESP = {'archived': False, 'queued': False, 'error': 'unknown'}


def init():
    """ Init the application and add routes """

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


@route('/archivepage')
def archive_page():
    url = request.query.get('url')

    handler = request.query.get('handler')

    return do_archive(url, handler)


#@route('/<:re:.+>')
#def archive_default():
#    return do_archive(request.environ['PATH_INFO'][1:], theconfig['default_handler'])


def do_archive(url, handler):
    if not url:
        raise HTTPError(status=400, body='No url= specified')

    if handler not in theconfig['handlers']:
        raise HTTPError(status=400, body='No archiving handler {0}'.format(handler))

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    response_key = get_cache_key(handler, url)
    pending_key = get_pending_key(handler, url)

    result = None

    if not rc.exists(response_key):
        cmd = handler + ' ' + url

        with pipeline(rc) as pi:
            pi.rpush(response_key, WAITING_STR)
            pi.rpush('q:urls', cmd)

        result = rc.brpoplpush(pending_key, response_key, theconfig['wait_timeout_secs'])

    if not result:
        result = rc.lindex(response_key, 0)

    if result:
        result = json.loads(result)
        result['ttl'] = rc.ttl(response_key)
    else:
        result = ERROR_RESP

    return result


application = init()

