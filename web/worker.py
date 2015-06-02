from redis import StrictRedis
from browser import ChromeBrowser

import json

from handlers import WebRecorderHandler, SavePageNowHandler

def init_browser():
    print('WebDriver Started')
    browser = ChromeBrowser()

#    handler = SavePageNowHandler()
    handler = WebRecorderHandler()

    rc = StrictRedis.from_url('redis://redis_1/2')
    while True:
        cmd = rc.brpop('q:urls', 10)
        if not cmd:
            continue

        try:
            url = cmd[1]
            result = handler(browser, url)
            json_result = json.dumps(result)
            actual_url = result.get('actual_url')

            if actual_url and actual_url != url:
                rc.lpush('r:' + actual_url, json_result)
                rc.expire('r:' + actual_url, 600)

            rc.lpush('r:' + url, json_result)
            rc.expire('r:' + url, 600)
        except Exception as e:
            print(e)
            rc.delete('r:' + url)

if __name__ == "__main__":
    init_browser()

