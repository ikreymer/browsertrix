from bottle import route, Route, request, default_app, view, HTTPError
from io import StringIO
from redis import StrictRedis

import json
import uwsgi
import os
import logging

from config import get_config
from worker import get_cache_key, init_redis

application = None


WAITING_STR = json.dumps({'queued': True, 'archived': False})


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


@route('/<:re:.+>')
def archive_default():
    return do_archive(request.environ['PATH_INFO'][1:], theconfig['default_handler'])


def do_archive(url, handler):
    if not url:
        raise HTTPError(status=400, body='No url= specified')

    if handler not in theconfig['handlers']:
        raise HTTPError(status=400, body='No archiving handler {0}'.format(handler))

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    url_res = get_cache_key(handler, url)
    result = None

    if not rc.exists(url_res):
        cmd = handler + ' ' + url
        rc.rpush('q:urls', cmd)

        result = rc.brpoplpush(url_res, url_res, theconfig['wait_timeout_secs'])

    if not result:
        result = rc.lindex(url_res, 0)

    if result:
        result = json.loads(result)
        result['ttl'] = rc.ttl(url_res)
    else:
        result = {'archived': False, 'error': 'unknown'}

    return result


application = init()

