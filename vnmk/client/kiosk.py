#!/usr/bin/env python3

import time

from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  


def getCredential(
#    userid,
    host="terminal-dogma.firebaseapp.com",
    driverExecutablePath="/usr/lib/firefox/geckodriver"
):

    """    options = Options()
    options.add_argument("--incognito")
    options.add_argument("--kiosk")"""

    driver = webdriver.Firefox(
        executable_path=driverExecutablePath
#        firefox_options=options
    )

    driver.get("http://%s/" % host)

    while True:
        time.sleep(1)
        try:
            element = driver.find_element_by_id('credential')
        except NoSuchElementException:
            continue
        except Exception as e:
            print(e)
            return None
        unlocked = element.get_attribute("data-unlocked")
        if not unlocked: continue
        credential = element.text
        driver.quit()
        return credential
