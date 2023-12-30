import os
func_import = r"C:\Users\andre\Documents\Python\Web_Scraper\Search_Engine_Scraper_2024"
os.chdir(func_import)
from search_crawler_functions import *
chromedriver_path = r"C:\Users\andre\Documents\Python\chromedriver-win64\chromedriver.exe"
startpage = 'https://www.google.de'

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

########################################################################################################################
# Load the excel file with the required data
# It should contain the company names and ideally some search keywords for their website
output_path = r"C:\Users\andre\OneDrive\Desktop\Nahrungsergaenzungsmittel"
os.chdir(output_path)
source_file = r"Liste_Nahrungsergänzungsmittel 2024_20231227.xlsx"
df_source = pd.read_excel(source_file)
col_list = list(df_source.columns)
for e in col_list:
    if 'Firma' in e or 'Anbieter' in e:
        comp_col = e
        break

# Starting with an empty table
newtable = []

count = 0
#skip = -1
skip = 119

for id, row in df_source.iterrows():
    if id <= skip:
        continue
#    if id == 150:
#        break
    # Restart the browser after 7 search queries
    if count == 7:
        driver.quit()
        count = 0
    # Start the selenium chromedriver
    if count == 0:
        driver, startpage = start_browser_sel(webdriver, Service, chromedriver_path, startpage)
    count += 1

    company = extract_text(row[comp_col])
    nextpos = col_list.index(comp_col) + 1
    if len(str(row[nextpos])) > 4:
        key_w = str(row[nextpos])
    elif len(str(row[nextpos + 1])) > 4:
        key_w = str(row[nextpos + 1])
    else:
        key_w = company
    comp_keywords = get_company_keywords(company, row, col_list)
    search_url = search_for(driver, startpage, key_w)
    if search_url == startpage or 'sorry' in search_url:
        time.sleep(7)
    if search_url == startpage or 'sorry' in search_url:
        search_url = search_for(driver, startpage, company)
    soup = BeautifulSoup(driver.page_source,'lxml')
    search_results = get_search_results(Comment, soup)
    website, website_options = get_website(comp_keywords, search_results)
    if not website and len(website_options) == 0:
        search_url = search_for(driver, startpage, company)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        search_results = get_search_results(Comment, soup)
        website, website_options = get_website(comp_keywords, search_results)
    linklist = get_all_links(soup)
    sm_links, linklist = sm_filter(linklist)
    other_links = [l for l in linklist if not any(l in e for e in sm_links) and not any(l in e for e in website_options)]
    full_row = [id, company, website, website_options, sm_links, other_links]
    newtable.append(full_row)
    print(full_row[:3])
    print(comp_keywords)


# DataFrame
header = ['ID','Anbieter','Webseite','Alternative Webseiten','Social Media','Weitere Links']
df_company_links = pd.DataFrame(newtable,columns=header)

# Create an Excel file
dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
recent_filename = 'Nahrungsergaenzungsmittel_Links' + dt_str_now + '.xlsx'
df_company_links.to_excel(recent_filename)


newtable = newtable[:-1]
len(newtable)
for t in newtable:
    print(t[:3])
print(newtable[-1][:4])