from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from urllib import urlencode


# ============================================================================
class PrefixHandler(object):
    def __init__(self, prefix, desc='Url Prefix Archiving Handler'):
        self.prefix = prefix
        self.desc = desc

    def __call__(self, browser, url):
        log_results = browser.visit(self.prefix + url)

        try:
            error = self.get_error(log_results, browser, url)
        except NoSuchElementException:
            # no error
            error = None
        except Exception as e:
            error = {'msg': str(e)}

        results = {'time': str(datetime.utcnow())}

        if error:
            results['error'] = error
            results['archived'] = False
        else:
            results['archived'] = True
            results['actual_url'] = self.get_actual_url(browser)
            self.set_success_results(browser, url, results)

        results['browser_url'] = self.get_browser_url(browser)

        for n in list(log_results.keys()):
            if not self.is_archived_url(n):
                del log_results[n]

        results['log'] = log_results

        return results

    def set_success_results(self, browser, url, results):
        pass

    def get_error(self, log_results, browser, url):
        return None

    def is_archived_url(self, url):
        return url.startswith(self.prefix)

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

    def set_success_results(self, browser, url, results):
        cookie = browser.driver.get_cookie('webrecorder.session')

        # not exact but close enough
        results['replay_url'] = 'https://web.archive.org/web/' + url

    def get_error(self, log_results, browser, url):
        err_text = browser.driver.find_element_by_css_selector("div#positionHome #error h2").text
        info = err_text + ' ' + browser.driver.find_element_by_css_selector("div#positionHome #error p").text

        if err_text in self.BLOCKED_MSGS:
            return {'msg': info, 'type': 'blocked'}
        else:
            return {'msg': info}

        return None


# ============================================================================
class WebRecorderHandler(PrefixHandler):
    def __init__(self, prefix='https://webrecorder.io/record/',
                       desc='<a href="https://webrecorder.io/">webrecorder.io</a> Archiving'):
        super(WebRecorderHandler, self).__init__(prefix, desc)

    def get_error(self, log_results, browser, url):
        browser.driver.switch_to.frame('iframe')
        err_elem = browser.driver.find_element_by_css_selector('div.webrec-error div.page-header span.h2')
        if err_elem.text == 'WebRecorder.io error':
            try:
                msg = browser.driver.find_element_by_css_selector('div.webrec-error p.h4').text
                if 'Name or service not known' in msg:
                    msg = 'This url could not be reached'
            except:
                msg = 'unknown'

            return {'msg': msg}

        return None

    def set_success_results(self, browser, url, results):
        cookie = browser.driver.get_cookie('webrecorder.session')

        if cookie:
            query = urlencode({'url': url, 'sesh': cookie['value']})
            #results['download_session'] = cookie['name'] + '=' + cookie['value']
            results['download_url'] = 'https://webrecorder.io/cmd/sesh_download?' + query
            results['replay_url'] = 'https://webrecorder.io/cmd/setsesh?' + query

        return results

    def is_archived_url(self, url):
        if url.startswith(self.prefix) and '_/' in url:
            return True

        return False
