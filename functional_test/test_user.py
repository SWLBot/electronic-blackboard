from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest

def connectBackendServer():
    browser = webdriver.Firefox()
    browser.get('http://localhost:3000/')
    return browser

def wait_url(browser,url=''):
    element = WebDriverWait(browser, 10).until(
        EC.url_to_be('http://localhost:3000/{url}'.format(url=url))
    )
    assert browser.current_url == 'http://localhost:3000/{url}'.format(url=url)

def signin(browser,username,password):
    usernameInput = browser.find_element_by_name('username')
    passwordInput = browser.find_element_by_name('password')
    usernameInput.send_keys(username)
    passwordInput.send_keys(password)
    passwordInput.submit()
    wait_url(browser)
    return browser

def signout(browser):
    signout = browser.find_element_by_id('signout')
    signout.click()

def closeBrowser(browser):
    browser.close()

def test_signin():
    browser = connectBackendServer()
    signin(browser,'admin','admin')
    closeBrowser(browser)

def test_add_user():
    try:
        browser = connectBackendServer()
        signin(browser,'admin','admin')
        add_user = browser.find_element_by_id('signup')
        add_user.click()
        username = browser.find_element_by_id('username')
        password = browser.find_element_by_id('password')
        confirm_password = browser.find_element_by_id('confirm-password')
        username.send_keys('test')
        password.send_keys('test_password')
        confirm_password.send_keys('test_password')
        browser.find_element_by_id('submit').click()

        element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, 'flash'))
        )
        flash = browser.find_element_by_id('flash').text
        assert 'create success!' in flash

        signout(browser)

        signin(browser,'test','test_password')

        closeBrowser(browser)
    except Exception as e:
        closeBrowser(browser)
        raise e

def test_change_password():
    browser = connectBackendServer()

    signin(browser,'test','test_password')

    changepwLink = browser.find_element_by_id('changepw')
    changepwLink.click()
    wait_url(browser,'changepw')

    oldPasswdInput = browser.find_element_by_name('old_password')
    oldPasswdInput.send_keys('test_password')
    passwdInput = browser.find_element_by_name('password')
    passwdInput.send_keys('tester')
    confirmPasswdInput = browser.find_element_by_name('confirm-password')
    confirmPasswdInput.send_keys('tester')
    browser.find_element_by_id('submit').click()

    signout(browser)

    signin(browser,'test','tester')

    closeBrowser(browser)
