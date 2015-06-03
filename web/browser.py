from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import Chrome, Remote
from selenium.webdriver.chrome.options import Options

import json


# ============================================================================
class ChromeBrowser(object):
    def __init__(self, host_name=None, readlog=False):
        caps = DesiredCapabilities.CHROME

        if readlog:
            caps['loggingPrefs'] = {'performance': 'ALL'}
            caps['chromeOptions'] = {'perfLoggingPrefs': {'enableTimeline': False, 'enablePage': False}}

        self.caps = caps
        self.readlog = readlog
        self.driver = None

        if host_name:
            try:
                self.driver = Remote(command_executor='http://{0}:4444/wd/hub'.format(host_name),
                                     desired_capabilities=caps)
            except:
                pass

        if not self.driver:
            self.driver = Chrome(chrome_options=Options(), desired_capabilities=caps)

    def close(self):
        if self.driver:
            self.driver.quit()

    def visit(self, url):
        self.driver.start_session(self.caps)
        self.driver.get(url)

        results = {}

        if not self.readlog:
            return results

        try:
            log = self.driver.get_log('performance')
        except Exception as e:
            print(e)
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

        print(results)
        return results


if __name__ == "__main__":
    global browser
    browser = ChromeBrowser()
