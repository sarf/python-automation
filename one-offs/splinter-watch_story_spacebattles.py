#!/usr/bin/python

import getopt
import sys
from time import sleep

from splinter import Browser
from splinter.exceptions import DriverNotFoundError


def first(elements):
    if elements and len(elements) > 0:
        return elements.first
    return None


def filterDict(dict=None, names=None):
    if dict is None or not isinstance(names, list) or len(names) <= 0:
        return

    data = {}
    for name in names:
        if dict[name]:
            data[name] = dict[name]

    return data


def getxpathfromdata(data):
    xpath = ''
    for name in data:
        xpath = '@{0} = "{1}" and {2}'.format(name, data[name], xpath)
    if len(xpath) > 0:
        return xpath[0:-5]
    return None


def getFormXPath(form=None):
    if not form or isinstance(form, str):
        return form
    if form['id']:
        return 'form[@id = "{}"]'.format(form['id'])
    else:
        return getxpathfromdata(filterDict(form, ['name', 'action']))


def getInputXPath(attributes=None):
    if attributes is None:
        return
    xpath = getxpathfromdata(attributes)
    if xpath and len(xpath) > 0:
        return 'input[{0}]'.format(xpath)
    else:
        return None


def getFormInputXPath(form=None, attributes=None):
    if attributes is None:
        return
    xpath = getInputXPath(attributes)
    if xpath is None:
        return None
    formxpath = getFormXPath(form)
    if formxpath is None:
        return '//{0}'.format(xpath)
    else:
        return '{0}{1}/descendant::{2}'.format(
            '' if formxpath.startswith('//') else '//', formxpath, xpath)


def findFirstSelector(browser, selector):
    elements = browser.find_by_css(selector)
    if elements.is_empty():
        print('failed to find selector {0}'.format(selector))
        return None
    return first(elements)


def findFirstXPath(browser, xpath):
    elements = browser.find_by_xpath(xpath)
    if elements.is_empty():
        print('failed to find xpath {0}'.format(xpath))
        return None
    return first(elements)


def ensureLoggedIn(browser, username=None, password=None):
    if username is None or password is None:
        print('Needs both username and password to log in')
        return False

    browser.click_link_by_href('login/')
    form = first(browser.find_by_id('login'))
    if form is None:
        print('Already logged in. Oh, frabjous day!')
        return True

    browser.fill_form({'login': username, "password": password, 'register': '0', 'remember': True}, 'login')

    redirect = first(form.find_by_css('input[type = "hidden"][name = "redirect"]'))

    if redirect:
        to = redirect['value']
        if to:
            index = to.find('/login')
            if index > -1:
                redirect['value'] = to[:(index + 1)]

    submit = first(form.find_by_css('input[type = "submit"]'))
    if submit:
        submit.click()
        # Wait needed?
        sleep(0.2)
        return True
    else:
        return False


def selectorattributeendswith(attr, sought):
    return '"{0}" = substring(@{1}, string-length(@{1}) - string-length("{0}") + 1)'.format(sought, attr)


def subscribeToStory(browser):
    browser.click_link_by_partial_href('/watch-confirm')
    form = first(browser.find_by_css('form[action $= "watch"]'))
    if not form:
        return False

    # subscribe = findFirstXPath(browser, getFormInputXPath(watch, { 'name' : 'email_subscribe', 'value' : '2' }))
    # if not subscribe:
    #    return False
    # browser.choose('email_subscribe', '2')
    # endsWith = selectorattributeendswith('action', 'watch')
    subscribe = first(form.find_by_css('input[type = "radio"][name = "email_subscribe"][value = "2"]'))
    if not subscribe:
        print("Could not find option to choose to subscribe to OP only. Probably on unwatch dialog.")
        # reset = first(form.find_by_css('input[type = "reset"]'))
        # if reset:
        #     reset.click()
        return False
    submit = first(form.find_by_css('input[type = "submit"]'))
    if not submit:
        return False

    submit.click()
    # In order for the form not to go stale
    form = first(browser.find_by_css('form[action $= "watch"]'))
    while form and form.visible:
        sleep(0.2)
        form = first(browser.find_by_css('form[action $= "watch"]'))
    sleep(0.1)
    return True


def watch_story(url, username, password):
    try:
        browser = Browser()
        browser.visit(url)
        if ensureLoggedIn(browser, username, password) and subscribeToStory(browser):
            print('Successfully subscribed to {0}'.format(url))
            browser.quit()
            return True

        print('Failed to subscribe to {0}'.format(url))
        browser.quit()
        return False
    except DriverNotFoundError:
        print("No driver found; please make sure that the driver is available and in the PATH")
        exit(5)


def main(argv):
    username = ''
    password = ''
    url = ''
    help = 'splinter-watch_story_spacebattles.py -u <url> -U <username> -P <password>'
    try:
        opts, args = getopt.getopt(argv, "hU:P:u:",
                                   ["username=", "password=", "url="])
    except getopt.GetoptError:
        print(help)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help)
            sys.exit()
        elif opt in ("-U", "--username"):
            username = arg.strip()
        elif opt in ("-P", "--password"):
            password = arg.strip()
        elif opt in ("-u", "--url"):
            url = arg.strip()
    print('Username is "{}"'.format(username))
    print('Password is {}'.format('"******"' if password else 'NOT SET!'))
    print('url is "{0}"'.format(url))
    if username and password and url:
        watch_story(url, username, password)
    else:
        print('url, username and password are all mandatory.')
        print(help)


if __name__ == "__main__":
    main(sys.argv[1:])
