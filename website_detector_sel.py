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

# Get all text elements from the page or bigger text elements
def get_visible_text(Comment, soup):
    def tag_visible(element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True
    texts = soup.find_all(string=True)
    visible_texts = filter(tag_visible, texts)
    pagetext = u" ".join(t.strip() for t in visible_texts)
    pagetext = re.sub('\n', ' ', pagetext).replace('\\xa0', ' ')
    pagetext = re.sub('\s+', ' ', pagetext).strip()
    return pagetext

# Extract text from elements
def extract_text(element):
    if element:
        if not isinstance(element,(str,int,float)):
            element = element.text.strip()
        element = str(element)
        if element == '':
            return element
        elif len(element) >= 1:
            repl_element = element.replace('\u200b','').replace('\xa0', ' ').replace('\n',' ')
            new_element = re.sub('\s+', ' ', repl_element).strip()
            return new_element
        else:
            return element

# Get company keywords
def get_company_keywords(company, row, col_list):
    comp_l1 = company.replace('-','').replace('.','').split()
    comp_l2 = company.replace('-','').replace('.','').split()
    comp_l3 = company.lower().replace('ä','ae').replace('ö','oe').replace('ü','ue').split()
    comp_l4 = company.split()
    comp_l = list(set(comp_l1 + comp_l2 + comp_l3 + comp_l4))
    comp_keywords_f = [str(e).lower() for e in comp_l if len(str(e).lower()) >= 3]
    comp_keywords = [e for e in comp_keywords_f if not '.mbh' in e and not 'gmbh' in e]
    sm_names = ['Facebook', 'Instagram']
    for n in sm_names:
        if n in col_list:
            addkey = str(row[n])
            sm_linkpart = n.lower() + '.com'
            if sm_linkpart in addkey:
                sm_name = addkey.split(sm_linkpart)[1].replace('/', '').strip().lower()
                comp_keywords.append(sm_name.lower())
    comp_keywords = list(set(comp_keywords))
    return comp_keywords

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

#Get the full search results
def get_search_results(soup):
    hits = soup.find_all('div', class_='MjjYud')
    ads = soup.find_all('div', class_='uEierd')
    results = []
    for h in hits:
        link_elem = h.find('a',href=True)['href']
        link = extract_text(link_elem)
        title_elem = h.find('h3', class_='LC20lb MBeuO DKV0Md')
        title = extract_text(title_elem)
        content_elem = h.find('div', class_='kb0PBd cvP2Ce')
        content = extract_text(content_elem)
        results.append([link, title, content])
    for a in ads:
        link_elem = a.find('a',href=True)['href']
        link = extract_text(link_elem)
        title_elem = a.find('div', {'role':'heading'})
        title = extract_text(title_elem)
        content = get_visible_text(Comment, a)
        results.append([link, title, content])
        break
    return results

def get_website(comp_keywords, search_results):
    company_links = []
    sm_names = ['facebook', 'instagram', 'twitter', 'youtube', 'tiktok', 'linkedin']
    for row in search_results:
        if any(k in row[0] for k in comp_keywords):
            company_links.append(row[0])
    for row in search_results:
        if any(n in row[0] for n in sm_names):
            continue
        if any(k in row[0] for k in comp_keywords) and any(k in str(row[1]).lower() for k in comp_keywords):
            website = row[0]
            company_links.remove(website)
            return website, company_links
    return '', company_links


# Collect all the links from the search results
def get_links():
    soup = BeautifulSoup(driver.page_source, 'lxml')
    linklist = [str(l['href']) for l in soup.find_all('a', href=True) if ('http' in l['href'] and not 'google' in l['href'])]
    linklist = list(OrderedDict.fromkeys(linklist))
    return linklist, soup


def sm_filter(linklist):
    platforms = ['facebook.com', 'instagram.com', 'twitter.com', 'youtube.com', 'tiktok.com', 'linkedin.com']
    sm_links_all = [l for l in linklist if any(p in l for p in platforms)]
    not_profile = ['/post', 'hashtag', 'sharer','/status', 'photo/', 'photos', 'watch?', '/video/', 'discover', '.help',
                    'reels', 'story', 'explore', 'playlist', 'sharer', 'policy', 'privacy', 'instagram.com/p/']
    sm_links = [l for l in sm_links_all if not any(e in l for e in not_profile)]

    return sm_links

########################################################################################################################
# Load the excel file with the required data
# It should contain the company names and ideally some search keywords for their website
source_file = r"Liste_Nahrungsergänzungsmittel 2024_20231227.xlsx"
df_source = pd.read_excel(source_file)
col_list = list(df_source.columns)
for e in col_names:
    if 'Firma' in e or 'Anbieter' in e:
        comp_col = e
        break

# Start the selenium chromedriver
driver, startpage = start_browser_sel(chromedriver_path, startpage)
pagelink = search_for(startpage, keyword)

newtable = []
for id, row in df_source.iterrows():
    company = extract_text(row[comp_col])
    nextpos = col_list.index(comp_col) + 1
    if len(str(row[nextpos])) > 4:
        key_w = str(row[nextpos])
    elif len(str(row[nextpos + 1])) > 4:
        key_w = str(row[nextpos])
    else:
        key_w = company
    comp_keywords = get_company_keywords(company, row, col_list)
    search_url = search_for(startpage, key_w)
    if search_url == startpage:
        print('Error')
        # continue
    soup = BeautifulSoup(driver.page_source,'lxml')
    search_results = get_search_results(soup)
    website, website_options = get_website(comp_keywords, search_results)






################################

keyword = 'Nahrungsergänzungsmittel'
driver, startpage = start_browser_sel(chromedriver_path, startpage)
pagelink = search_for(startpage, keyword)
if driver.current_url != startpage:
    link_list, soup = get_links()
    for l in link_list:
        print(l)

