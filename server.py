from bottle import *
import os
import hitcon
import datetime
from bottle_cache.plugin import cache_for, CachePlugin

app = Bottle()

cache = CachePlugin('url_cache', 'redis', host='localhost', port=6379, db=1)
app.install(cache)
cache['by_route'] = lambda req, ctx: str(ctx.rule)

@app.get('/')
def index():
    return static_file('index.html', os.path.dirname(__file__))

@app.get('/sessions.json')
@cache_for(90, cache_key_func='by_route')
def sessions():
    print('Update: %r' % datetime.datetime.now())
    return hitcon.get_sessions(True)

@app.get('/<fn:path>')
def root(fn):
    return static_file(fn, os.path.dirname(__file__))

if __name__ == '__main__':
    run(app, port=8000, debug=True, reload=True)
