from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest

def test_signin():
    browser = webdriver.Firefox()
    browser.get('http://localhost:3000/')
    username = browser.find_element_by_name('username')
    password = browser.find_element_by_name('password')
    username.send_keys('admin')
    password.send_keys('admin')
    password.submit()
    element = WebDriverWait(browser, 10).until(
        EC.url_to_be('http://localhost:3000/')
    )
    assert browser.current_url == 'http://localhost:3000/'

    browser.close()
