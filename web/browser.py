from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import Chrome, Remote, Firefox

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

import json
import logging


# ============================================================================
class Browser(object):
    def __init__(self, host_name=None, readlog=False):
        self.readlog = readlog
        self.host_name = host_name

        self.caps = self._init_caps()
        self._init_driver()

    def _init_local(self):
        raise NotImplemented()

    def _init_driver(self):
        self.driver = None

        if not self.host_name:
            self.driver = self._init_local()
            return

        while True:
            try:
                self.driver = Remote(command_executor='http://{0}:4444/wd/hub'.format(self.host_name),
                                     desired_capabilities=self.caps)
                break
            except:
                import traceback
                traceback.print_exc()
                print('RETRY CONN')

    def close(self):
        if self.driver:
            self.driver.quit()

    def visit(self, url):
        try:
            self.driver.get(url)
        except:
            self._init_driver()
            self.driver.get(url)

        results = {}
        return results


# ============================================================================
class ChromeBrowser(Browser):
    def _init_caps(self):
        caps = DesiredCapabilities.CHROME

        if self.readlog:
            caps['loggingPrefs'] = {'performance': 'ALL'}
            caps['chromeOptions'] = {'perfLoggingPrefs': {'enableTimeline': False, 'enablePage': False}}

        return caps

    def _init_local(self):
        return Chrome(chrome_options=Options(), desired_capabilities=self.caps)

    def visit(self, url):
        results = super(ChromeBrowser, self).visit(url)

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


# ============================================================================
class FirefoxBrowser(Browser):
    def _init_caps(self):
        caps = DesiredCapabilities.FIREFOX
        return caps

    def _init_local(self):
        firefox_profile = FirefoxProfile()
        firefox_profile.set_preference('extensions.logging.enabled', False)
        firefox_profile.set_preference('network.dns.disableIPv6', False)
        return Firefox(firefox_profile)


# ============================================================================
if __name__ == "__main__":
    global browser

    import sys

    if len(sys.argv) <= 1 or sys.argv[1] != 'firefox':
        browser = ChromeBrowser()
    else:
        browser = FirefoxBrowser()
