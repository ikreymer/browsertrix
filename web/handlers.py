from selenium.common.exceptions import NoSuchElementException
from datetime import datetime


# ============================================================================
class PrefixHandler(object):
    def __init__(self, prefix, desc='Url Prefix Archiving Handler'):
        self.prefix = prefix
        self.desc = desc

    def __call__(self, browser, url):
        log_results = browser.visit(self.prefix + url)

        error = self.get_error(log_results, browser, url)

        results = {'time': str(datetime.utcnow())}

        if error:
            results['error'] = error
            results['archived'] = False
        else:
            results['archived'] = True
            results['actual_url'] = self.get_actual_url(browser)

        results['browser_url'] = self.get_browser_url(browser)
        results['log'] = log_results
        return results

    def get_error(self, log_results, browser, url):
        return None

    def get_desc(self):
        return self.desc

    def get_browser_url(self, browser):
        try:
            return browser.driver.current_url
        except:
            return ''

    def get_actual_url(self, browser):
        url = self.get_browser_url(browser)
        try:
            inx = url[1:].index('/http')
            url = url[inx + 2:]
        except:
            pass

        return url


# ============================================================================
class SavePageNowHandler(PrefixHandler):
    BLOCKED_MSGS = ('Sorry.', 'Page cannot be crawled or displayed due to robots.txt.')

    def __init__(self, prefix='https://web.archive.org/save/',
                       desc='Internet Archive <a href="https://web.archive.org/web/">Save Page Now</a> Archiving'):
        super(SavePageNowHandler, self).__init__(prefix, desc)

    def get_error(self, log_results, browser, url):
        try:
            err_text = browser.driver.find_element_by_css_selector("div#positionHome #error h2").text
            info = err_text + ' ' + browser.driver.find_element_by_css_selector("div#positionHome #error p").text

            if err_text in self.BLOCKED_MSGS:
                return {'blocked': info}
            else:
                return {'other': info}

        except NoSuchElementException:
            pass
        except Exception as e:
            return {'unknown': str(e)}

        return None


# ============================================================================
class WebRecorderHandler(PrefixHandler):
    def __init__(self, prefix='https://webrecorder.io/record/',
                       desc='<a href="https://webrecorder.io/">webrecorder.io</a> Archiving'):
        super(WebRecorderHandler, self).__init__(prefix, desc)

    def get_error(self, log_results, browser, url):
        return None

    def __call__(self, browser, url):
        results = super(WebRecorderHandler, self).__call__(browser, url)
        cookie = browser.driver.get_cookie('webrecorder.session')
        results['session'] = cookie
        print('SESSION', cookie)
        return results
