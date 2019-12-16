# Don't think idea will work as it is dependent on Chrome version on the computer. 

import os
from selenium import webdriver

username = os.environ.get('ZENUSER')
password = os.environ.get('ZENPASSWORD')

driver = webdriver.Chrome('/home/brandon/Repo/python/account_manager/account_manager/drivers/chromedriver')

driver.set_page_load_timeout(10)
driver.get('https://dp.zencharts.com')
driver.find_element_by_name('LoginForm[username]').send_keys(username)
driver.find_element_by_name('LoginForm[password]').send_keys(password)
#driver.find_element_by_name('').click()
