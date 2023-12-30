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

from datetime import datetime, timedelta
import time
import os
import re

# Say Hello
def print_hello(name):
    print(f'Hello {name}')


# Start selenium chromedriver and open the startpage
def start_browser_sel(webdriver, Service, chromedriver_path, startpage):
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


# Get all text elements from the page or bigger elements
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
    comp_l1 = company.replace('-',' ').replace('.',' ').split()
    comp_l2 = company.replace('_',' ').replace('.',' ').split()
    comp_l3 = company.lower().replace('ä','ae').replace('ö','oe').replace('ü','ue').split()
    comp_l4 = company.split()
    comp_l5 = company.replace('[', '').replace(']', '').split()
    comp_l = list(set(comp_l1 + comp_l2 + comp_l3 + comp_l4 + comp_l5))
    comp_keywords_f = [str(e).lower() for e in comp_l if len(str(e).lower()) >= 3]
    appendix = ['gmbh', 'mbh', 'inc', 'limited', 'ltd', 'llc', 'com', 'co.']
    comp_keywords = [e for e in comp_keywords_f if not any(a in e for a in appendix)]
    sm_names = ['Facebook', 'Instagram']
    for n in sm_names:
        if n in col_list:
            addkey = str(row[n])
            sm_linkpart = n.lower() + '.com'
            if sm_linkpart in addkey:
                sm_name = addkey.split(sm_linkpart)[1].replace('/', '').strip().lower()
                comp_keywords.append(sm_name.lower())
    comp_keywords = list(set(comp_keywords)) + [company]
    return comp_keywords


# Search for a specific keyword
def search_for(driver, startpage, keyword):
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
    # Scrolling
    for i in range(5):
        driver.execute_script("window.scrollBy(0,2500)", "")
        time.sleep(1)
    return driver.current_url


#Get the full search results
def get_search_results(Comment, soup):
    hits = soup.find_all('div', class_='MjjYud')
    ads = soup.find_all('div', class_='uEierd')
    results = []
    for h in hits:
        link_elem = h.find('a',href=True)
        if not link_elem:
            continue
        link = str(link_elem['href']).strip()
        title_elem = h.find('h3', class_='LC20lb MBeuO DKV0Md')
        title = extract_text(title_elem)
        content_elem = h.find('div', class_='kb0PBd cvP2Ce')
        content = extract_text(content_elem)
        results.append([link, title, content])
    for a in ads:
        link_elem = a.find('a',href=True)
        if not link_elem:
            continue
        link = str(link_elem['href']).strip()
        title_elem = a.find('div', {'role':'heading'})
        title = extract_text(title_elem)
        content = get_visible_text(Comment, a)
        results.append([link, title, content])
    return results


# Filter function for website links with the highest probability
def get_website(comp_keywords, search_results):
    other_pages = ['facebook', 'instagram', 'twitter', 'youtube', 'tiktok', 'linkedin', 'xing', 'trustpilot', 'amazon',
                   'ebay', 'pinterest', 'giphy.co', 'koelnerliste', 'kimeta.de', 'yumpu.com', 'kununu', '/es/', '.co/'
                   'praxispanda', '.co.in']
    filtered_results = [row for row in search_results if 'http' in row[0] and (not any(n in row[0] for n in other_pages)
                                                                        and any(k in row[0] for k in comp_keywords))]
    website_scores = {}
    for row in filtered_results:
        website_scores[row[0]] = 0
        l_part = row[0]
        if len(l_part) >= 40:
            l_part = l_part[:40]
        for k in comp_keywords:
            if k in row[0][:30]:
                website_scores[row[0]] += 2
            if k in l_part:
                website_scores[row[0]] += 1
            if k in str(row[1]) or k in str(row[2]):
                website_scores[row[0]] += 1
        if 'Homepage' in str(row[1]) or 'Official' in str(row[1]):
            website_scores[row[0]] += 1
        if 'www.' in row[0]:
            website_scores[row[0]] += 1
        if '.com' in row[0]:
            website_scores[row[0]] += 1
        if '.de' in row[0] and not ('impressum' in row[0] or 'contact' in row[0]):
            website_scores[row[0]] += 1
        if len(row[0]) <= (len(''.join(comp_keywords)) + 20):
            website_scores[row[0]] += 1

    # Order the dictionary by scores in descending order and the shortest length of the links
    sorted_websites = sorted(website_scores.items(), key=lambda x: (x[1], -len(x[0])), reverse=True)
    if len(sorted_websites) == 0:
        return '', sorted_websites

    website_links = [k[0] for k in sorted_websites]
    website = website_links[0]
    website_links.pop(0)
    return website, website_links


# Collect all the links and remove duplicates (but keep them ordered)
def get_all_links(soup):
    linklist = [str(l['href']) for l in soup.find_all('a', href=True) if ('http' in l['href'] and not 'google' in l['href'])]
    linklist = list(OrderedDict.fromkeys(linklist))
    return linklist


# Filter Social Media account links
def sm_filter(linklist):
    platforms = ['facebook.com', 'instagram.com', 'twitter.com', 'youtube.com', 'tiktok.com', 'linkedin.com', 'xing.com']
    sm_links_all = [l for l in linklist if any(p in l for p in platforms)]
    not_profile = ['/post', 'hashtag', 'sharer','/status', 'photo/', 'photos', 'watch?', '/video/', 'discover', '.help',
                    'reels', 'story', 'explore', 'playlist', 'sharer', 'policy', 'privacy', 'instagram.com/p/',
                   '/tag/','/embed/']
    sm_links = [l for l in sm_links_all if not any(e in l for e in not_profile)]
    sm_links = list(set(sm_links))
    sm_links.sort(key=len)
    pos = 0
    for l in sm_links_all:
        if '/status' in l:
            l = l.split('/status')[0]
            if l not in sm_links:
                sm_links.insert(pos,l)
                pos += 1
    return sm_links, linklist

