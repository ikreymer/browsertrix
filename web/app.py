from bottle import route, request, default_app
from io import StringIO
from redis import StrictRedis

import json
import uwsgi

application = None

def init():
    app = default_app()
    return app


WAITING_STR = json.dumps({'queued': True, 'archived': False})

@route('/:arc/<:re:.+>')
def archive_url(arc):
    request.path_shift()
    url = request.environ.get('PATH_INFO')[1:]
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    url_res = 'r:' + url
    result = None

    if not rc.exists(url_res):
        rc.rpush('q:urls', url)

        result = rc.brpoplpush(url_res, url_res, 30)

    if not result:
        result = rc.lindex(url_res, 0)

    if result:
        result = json.loads(result)
        result['ttl'] = rc.ttl(url_res)
    else:
        result = {'archived': False, 'error': 'unknown'}

    return result



#def add_archive_route(app, path, handler):
#    rule = '/{0}/<:re:.+>'.format(path)

       #return handler(app.browser, url)

#    route = Route(app, rule, 'GET', callback)
#    app.add_route(route)

application = init()

redis_host = 'redis_1'

#add_archive_route(application, 'test', SavePageNowHandler())

rc = StrictRedis.from_url('redis://{0}/2'.format(redis_host))

#init_browser()
#uwsgi.post_fork_hook = init_browser

#@mulefunc
#def mule_hook():
#    print('MULE HOOK')


#mule_hook()
