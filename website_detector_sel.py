import os
path = r"C:\Users\andre\OneDrive\Desktop\Nahrungsergaenzungsmittel"
os.chdir(path)

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
import lxml

from collections import OrderedDict
import numpy as np
import pandas as pd
import re
from datetime import datetime, timedelta
import time


# Settings
chromedriver_path = r"C:\Users\andre\Documents\Python\chromedriver-win64\chromedriver.exe"
startpage = 'https://www.google.de'


# Start driver and open a new page
def start_browser_sel(chromedriver_path, startpage):
    # Open the Browser with a service object and an user agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'user-agent={user_agent}')
#    chrome_options.add_argument('--headless')
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    driver.get(startpage)
    time.sleep(2)
    try:
        cookiebanner = driver.find_element('xpath', "//*[text()='Alle ablehnen']")
        cookiebanner.click()
    except:
        pass
    return driver, startpage


# Search for a specific keyword
def search_for(startpage, keyword):
    try:
        searchbox = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="APjFqb"]')))
    except:
        driver.get(startpage)
#        driver, startpage = start_browser_sel(chromedriver_path, startpage)
        searchbox = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="APjFqb"]')))
    searchbox.clear()
    for k in keyword:
        searchbox.send_keys(k)
        time.sleep(.1)
    searchbox.send_keys(Keys.ENTER)
    time.sleep(2)
    return driver.current_url

# Collect all the links from the search results
def get_links():
    soup = BeautifulSoup(driver.page_source, 'lxml')
    linklist = [str(l['href']) for l in soup.find_all('a', href=True) if ('http' in l['href'] and not 'google' in l['href'])]
    linklist = list(OrderedDict.fromkeys(linklist))
    return linklist, soup


# Start the selenium chromedriver
keyword = 'Nahrungsergänzungsmittel'
driver, startpage = start_browser_sel(chromedriver_path, startpage)
pagelink = search_for(startpage, keyword)
if driver.current_url != startpage:
    link_list, soup = get_links()
    for l in link_list:
        print(l)

