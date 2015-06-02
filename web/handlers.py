from selenium.common.exceptions import NoSuchElementException
#import yaml
from datetime import datetime


# ============================================================================
#def init_config(filename):
#    with open(filename) as fh:
#        results = yaml.load(fh)

#    return results


# ============================================================================
class PrefixHandler(object):
    def __init__(self, prefix):
        self.prefix = prefix

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

        #results['log'] = log_results
        return results

    def get_error(self, log_results, browser, url):
        return None

    def get_actual_url(self, browser):
        url = browser.driver.current_url
        try:
            inx = url[1:].index('/http')
            url = url[inx + 2:]
        except:
            pass

        return url


# ============================================================================
class SavePageNowHandler(PrefixHandler):
    BLOCKED_MSGS = ('Sorry.', 'Page cannot be crawled or displayed due to robots.txt.')

    def __init__(self, prefix='https://web.archive.org/save/'):
        super(SavePageNowHandler, self).__init__(prefix)

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
        except e:
            return {'unknown': str(e)}

        return None


# ============================================================================
class WebRecorderHandler(PrefixHandler):
    def __init__(self, prefix='https://webrecorder.io/record/'):
        super(WebRecorderHandler, self).__init__(prefix)
