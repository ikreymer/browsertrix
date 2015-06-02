from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import Chrome, Remote
from selenium.webdriver.chrome.options import Options

import json


# ============================================================================
class ChromeBrowser(object):
    def __init__(self):
        caps = DesiredCapabilities.CHROME
        #caps['loggingPrefs'] = {'performance': 'ALL'}
        #caps['chromeOptions'] = {'perfLoggingPrefs': {'enableTimeline': False, 'enablePage': False}}
        self.caps = caps

        #self.driver = Chrome(chrome_options=Options(), desired_capabilities=caps)
        self.driver = Remote(command_executor='http://{0}:4444/wd/hub'.format('hub_1'),
                             desired_capabilities=caps)

    def visit(self, url):
        self.driver.start_session(self.caps)
        self.driver.get(url)

        results = {}

        try:
            log = self.driver.get_log('performance')
        except:
            return results

        for entry in log:
            message = entry.get('message')
            try:
                message = json.loads(message)
                message = message['message']
                if message['method'].startswith('Network'):
                    resp = message['params'].get('response')
                    if not resp:
                        continue

                    resp_url = resp.get('url', '')
                    if resp_url and resp_url.startswith('http'):
                        results[resp_url] = {'status': resp.get('status')}
            except:
                continue

        return results


if __name__ == "__main__":
    global browser
    browser = ChromeBrowser()
