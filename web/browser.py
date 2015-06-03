from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import Chrome, Remote
from selenium.webdriver.chrome.options import Options

import json
import logging


# ============================================================================
class ChromeBrowser(object):
    def __init__(self, host_name=None, readlog=False):
        caps = DesiredCapabilities.CHROME

        if readlog:
            caps['loggingPrefs'] = {'performance': 'ALL'}
            caps['chromeOptions'] = {'perfLoggingPrefs': {'enableTimeline': False, 'enablePage': False}}

        self.caps = caps
        self.readlog = readlog
        self.host_name = host_name

        self._init_driver()

    def _init_driver(self):
        self.driver = None

        if self.host_name:
            try:
                self.driver = Remote(command_executor='http://{0}:4444/wd/hub'.format(self.host_name),
                                     desired_capabilities=self.caps)
            except:
                pass

        if not self.driver:
            self.driver = Chrome(chrome_options=Options(), desired_capabilities=self.caps)

    def close(self):
        if self.driver:
            self.driver.quit()

    def visit(self, url):
        try:
            self.driver.start_session(self.caps)
        except:
            logging.debug('Reiniting Driver, probably closed due to timeout')
            self._init_driver()

        self.driver.get(url)

        results = {}

        if not self.readlog:
            return results

        try:
            log = self.driver.get_log('performance')
        except Exception as e:
            import traceback
            traceback.print_exc()
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
