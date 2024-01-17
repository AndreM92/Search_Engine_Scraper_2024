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

import os
path_to_crawler_functions = r'C:\Users\andre\Documents\Python\Web_Scraper\Search_Engine_Scraper_2024'
file_path = r"C:\Users\andre\OneDrive\Desktop\Nahrungsergaenzungsmittel"
chromedriver_path = r"C:\Users\andre\Documents\Python\chromedriver-win64\chromedriver.exe"
########################################################################################################################

def compose_search_url(platform, company):
    keyword = ' '.join([company.lower(), platform.lower()]).replace(' ', '+')
    search_engine = 'https://www.google.com/search?q='
    lang_loc = '&gl=de&hl=de&num=50&start=0&location=Germany&uule=w+CAIQICIHR2VybWFueQ'
    return f"{search_engine}{keyword}{lang_loc}"

def collect_search_results(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = get_search_results(soup)
    return results


if __name__ == '__main__':
    os.chdir(path_to_crawler_functions)
    from search_crawler_functions import *
    import search_crawler_credentials as cred
    os.chdir(file_path)
    source_file = pd.read_excel('Liste_Nahrungsergänzungsmittel_2024_Auswahl.xlsx')

    # Insert the company and Platform you want to search for
    company = 'Optimum Nutrition'
    platform = 'Instagram'

    search_url = compose_search_url(platform, company)
    driver, page = start_browser_sel(chromedriver_path, search_url, headless=True)
    search_results = collect_search_results(driver)

    for id, r in enumerate(search_results):
        print(r)
        if id == 3:
            break

    driver.quit()