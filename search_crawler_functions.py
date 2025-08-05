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
from langdetect import detect

import search_crawler_credentials as cred

# Say Hello
def print_hello(name):
    print(f'Hello {name}')


# Start selenium chromedriver and open the startpage
def start_browser_sel(chromedriver_path, startpage, user_agent, headless = False):
    # Open the Browser with a service object and an user agent
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'user-agent={user_agent}')
    if headless:
        chrome_options.add_argument('--headless')
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    driver.get(startpage)
    time.sleep(3)
    # Click through the first Cookie Banner
    cookiebuttons = driver.find_elements('xpath', "//*[contains(text(), 'ablehnen') or contains(text(), 'Ablehnen')]")
    if len(cookiebuttons) == 0 or 'youtube' in driver.current_url:
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        time.sleep(2)
        cookiebuttons = driver.find_elements('xpath', '//button[contains(., "ablehnen")]')
    if len(cookiebuttons) == 0 and not 'instagram' in driver.current_url:
        cookiebuttons = driver.find_elements(By.TAG_NAME, 'button')
    if len(cookiebuttons) >= 1:
        for c in cookiebuttons:
            try:
                c.click()
            except:
                pass
    return driver, startpage


# Get all text elements from the page or bigger elements
def get_visible_text(soup):
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

def extract_number(element):
    if element:
        if not isinstance(element,(str,int,float)):
            element = element.text.strip()
        element = str(element)
        if len(element) < 1:
            return element
        element = str(re.sub(r'[^0-9.,]', '', element)).strip()
        if element[-2:] == '.0' or element[-2:] == ',0':
            element = element[:-2]
        if ',' in element:
            if len(element.split(',')[1]) >= 3:
                element = element.replace(',','')
            else:
                element = element.replace(',','.')
        if '.' in element:
            try:
                element = float(element)
            finally:
                return element
        try:
            element = int(element)
        finally:
            return element

# Improved version of extract_number
def extract_every_number(element):
    if element:
        if not isinstance(element,(str,int,float)):
            element = element.text.strip()
        if str(element) == '0':
            return 0
        if not element:
            return element
        element = str(element).replace('\u200b', '').replace('\xa0', ' ').replace('\\xa0', ' ').replace('\n', ' ')
        element = element.replace('!', '').replace('#', '').replace('+', ' ').replace('-', ' ').replace('%', ' ')
        element = re.sub('\s+', ' ', element).strip()
        if 'M' in element:
            try:
                element = str(int(float(element.replace("Mio", " ").replace("M", " ").split(' ')[0].replace(",", ".").strip()) * 1000000))
            except:
                return element
        elif 'Tsd.' in element:
            try:
                element = float(str(re.sub(r'[^0-9,]', '', element)).strip().replace(',','.')) * 1000
            except:
                return element
        elif str(element)[-1] == 'K':
            try:
                element = float(str(re.sub(r'[^0-9.]', '', element)).strip()) * 1000
            except:
                return element
        else:
            element = str(re.sub(r'[^0-9.,]', '', element)).strip()
        element = str(element)
        if element[-2:] == '.0' or element[-2:] == ',0':
            element = element[:-2]
            try:
                element = int(element)
            finally:
                return element
        if '.' in element and ',' in element:
            if ',' in element.split('.')[-1]:
                element = element.replace('.', '').replace(',', '.')
            else:
                element = element.replace(',', '')
            try:
                element = float(element)
            finally:
                return element
        if ',' in element:
            if element[-1] == '0':
                element = element.replace(',', '')
            element = element.replace(',','.')
        if '.' in element:
            try:
                element = float(element)
            finally:
                return element
        try:
            element = int(element)
        finally:
            return element


# Get company keywords
def get_company_keywords(row, col_list):
    company = ''
    web_address = ''
    web_address2 = ''
    comp_keywords = []
    for e in col_list:
        e = str(e)
        if 'Firma' in e or 'Anbieter' in e or 'Marke' in e:
            company = extract_text(row[e])
            break

    comp_l1 = company.replace('-',' ').replace('.',' ').split()
    comp_l2 = company.replace('_',' ').replace('.',' ').replace('+','').replace('-','').replace("'","").split()
    comp_l3 = company.lower().replace('ä','ae').replace('ö','oe').replace('ü','ue').split()
    comp_l4 = company.split()
    comp_l5 = company.replace('[', '').replace(']', '').replace(')','').replace('(','').split()
    comp_l = list(set(comp_l1 + comp_l2 + comp_l3 + comp_l4 + comp_l5))
    comp_keywords_f = [str(e).lower() for e in comp_l]
    appendix = ['gmbh', 'mbh', 'inc', 'limited', 'ltd', 'llc', 'co.', 'lda', 'a.s.', 'S.A.', ' OG', ' AG', ' SE',
                'GmbH & Co. KG', 'GmbH', 'B.V.', 'KG', 'LLC', 'NV', 'N.V.',
                '& Co.', 'S.L.U.', '(', ')', '.de', '.com', '.at', 'oHG', 'Ltd.', 'Limited']
    for c in comp_keywords_f:
        for a in appendix:
            c = c.replace(a, '')
        if len(c) >= 4:
            comp_keywords.append(c)
    if company:
        comp_keywords = comp_keywords + [company]
    web_name, name = None, None
    for e in col_list:
        web_name = None
        el = e.lower()
        if 'name ' in el and not name:
            name = extract_text(row[e])
            comp_keywords.append(name)
        elif 'webs' in el:
            col_val = str(extract_text(row[e]))
            if len(col_val) >= 4:
                if '//' in col_val:
                    col_val = str(col_val).split('//', 1)[1]
                web_name = col_val.replace('www.', '').split('.')[0]
        elif 'homepage' in el:
            col_val = extract_text(row[e])
            if len(col_val) >= 4:
                web_address2 = col_val
                web_name = col_val.split('.')[0]
        elif 'internet' in el:
            col_val = extract_text(row[e])
            if len(col_val) >= 4:
                web_address = col_val
                web_name = col_val.split('.')[0]
        if web_name:
            comp_keywords.append(web_name)
    if 'Website' in col_list:
        web_name = extract_text(row['Website'])
        if len(web_name) > 10:
            web_address = web_name
    sm_names = ['Facebook', 'Instagram']
    for n in sm_names:
        if n in col_list:
            addkey = str(row[n])
            sm_linkpart = n.lower() + '.com'
            if sm_linkpart in addkey:
                sm_name = addkey.split(sm_linkpart)[1].replace('/', '').strip().lower()
                comp_keywords.append(sm_name.lower())
    comp_keywords = list(set(comp_keywords))
    comp_keywords = [str(e) for e in comp_keywords if len(e) >= 3 and e != 'nan']
    return comp_keywords, company, web_address, web_address2


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
        time.sleep(.05)
    searchbox.send_keys(Keys.ENTER)
    time.sleep(4)
    # Scrolling
    for i in range(3):
        driver.execute_script("window.scrollBy(0,2500)", "")
        time.sleep(1)
    return driver.current_url


#Get the full search results
def get_search_results(soup):
    hits = soup.find_all('div', class_='MjjYud')
    ads = soup.find_all('div', class_='uEierd')
    sresults = []
    for h in hits:
        link_elem = h.find('a',href=True)
        if not link_elem:
            continue
        link = str(link_elem['href']).strip()
        title_elem = h.find('h3', class_='LC20lb MBeuO DKV0Md')
        title = extract_text(title_elem)
        content_elem = h.find('div', class_='kb0PBd cvP2Ce')
        content = extract_text(content_elem)
        if not content:
            content = get_visible_text(h)
            if content and title and title in content:
                content = content.split(title)[1].strip()
        sresults.append([link, title, content])
    for a in ads:
        link_elem = a.find('a',href=True)
        if not link_elem:
            continue
        link = str(link_elem['href']).strip()
        title_elem = a.find('div', {'role':'heading'})
        title = extract_text(title_elem)
        content = get_visible_text(a)
        sresults.append([link, title, content])
    return sresults


# Filter function for website links with the highest probability
def get_website(comp_keywords, sresults, web_address, web_address2):
    website = ''
    all_links = [x[0] for x in sresults]
    if len(all_links) == 0:
        return website, []
    sorted_links = sorted(all_links, key=lambda x: len(x))

    other_pages = ['facebook', 'instagram', 'twitter', 'youtube', 'tiktok', 'linkedin', 'xing', 'trustpilot', 'amazon',
                   'ebay', 'pinterest', 'giphy.co', 'koelnerliste', 'kimeta.de', 'yumpu.com', 'kununu', '/es/', '.co/'
                   'praxispanda', '.co.in', 'wlw.de', 'firmendatenbank/']
    filtered_results = [rows for rows in sresults if 'http' in rows[0] and (not any(n in rows[0] for n in other_pages)
                                                                        and any(k in rows[0] for k in comp_keywords))]
    if len(filtered_results) == 0:
        filtered_results = sorted_links
    if len(filtered_results) == 1:
        if len(filtered_results[0]) == 3:
            filtered_results = filtered_results[0]
        return website, filtered_results[0]

    website_scores = {}
    for pos, row2 in enumerate(filtered_results):
        if len(row2[0]) < 17:
            continue
        website_scores[row2[0]] = 0
        for k in comp_keywords:
            if k in row2[0]:
                website_scores[row2[0]] += 2
            if k in row2[0] or k in str(row2[2]):
                website_scores[row2[0]] += 1
        if 'Homepage' in str(row2[1]) or 'Official' in str(row2[1]):
            website_scores[row2[0]] += 1
        if 'www.' in row2[0]:
            website_scores[row2[0]] += 1
        if '.com' in row2[0]:
            website_scores[row2[0]] += 1
        if '.de' in row2[0] and not ('impressum' in row2[0] or 'contact' in row2[0]):
            website_scores[row2[0]] += 2
        if len(row2[0]) <= 50:
            website_scores[row2[0]] += 2
        for f in filtered_results:
            if row2[0] in f[0]:
                website_scores[row2[0]] += 2
        website_scores[row2[0]] -= pos

    if len(website_scores) == 0:
        return website, all_links

    # Order the dictionary by scores in descending order and the shortest length of the links
    sorted_websites = sorted(website_scores.items(), key=lambda x: (x[1], -len(x[0])), reverse=True)
    website_links = [k[0] for k in sorted_websites]

    if not web_address:
        website = website_links[0]
        website_links.pop(0)
        return website, website_links
    if web_address:
        for l in sorted_links:
            if web_address in l:
                return l, website_links
    if web_address2:
        for l in sorted_links:
            if web_address in l:
                return l, website_links

    return website, website_links


# Collect all the links and remove duplicates (but keep them ordered)
def get_all_links(soup):
    linklist = [str(l['href']) for l in soup.find_all('a', href=True) if ('http' in l['href'] and not 'google' in l['href'])]
    linklist = list(OrderedDict.fromkeys(linklist))
    return linklist


# Filter Social Media account links
def sm_filter(linklist):
    platforms = ['facebook.com', 'instagram.com', 'twitter.com', 'youtube.com', 'tiktok.com', 'linkedin.com', 'x.com', 'xing.com']
    sm_links_all = [l for l in linklist if any(p in l for p in platforms)]
    not_profile = ['/post', 'hashtag', 'sharer','/status', 'photo/', 'photos', 'watch?', '/video/', 'discover', '.help',
                    'reels', 'story', 'explore', 'playlist', 'policy', 'policies', 'privacy', 'instagram.com/p/', '/share'
                   '/tag/','/embed/', '/terms', '/legal', '/tos', '/help', 'stepstone.de']
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

# Order the Social Media accounts
def sm_order(sm_links, linklist):
    platforms = ['facebook.com', 'instagram.com', 'linkedin.com', 'tiktok.com', 'twitter.com', 'youtube.com', 'x.com']
    account_list = ['' for _ in range(len(platforms))]
    for l in sm_links:
        for pos, h in enumerate(platforms):
            if h in str(l).lower() and account_list[pos] == '':
                account_list[pos] = l
    sm_else = [l for l in sm_links if l not in account_list]
    for l in linklist:
        if any(h.split('.')[0] in str(l).lower() for h in platforms) and l not in account_list:
            sm_else.append(l)
    return account_list, sm_else


def rank_sm_accounts(platform, comp_keywords, branch_keywords, search_results):
    if platform == 'X':
        platform = 'Twitter'
    p_link = platform.lower() + '.com/'
    not_profile = ['/post', 'hashtag', 'sharer','/status', '/photo', 'photos', '/watch', '/video', '/search', '/events', '/mediaset', 'discover', '.help',
                'groups', 'reels', 'story', 'explore', 'playlist', 'sharer', 'policy', 'privacy', 'instagram.com/p/', '/public', '/developers'
                '/blog', '/event', '/reel/', '/tag/', '/embed/', '/jobs', '/pub/dir', '/pulse', '/place', '/channel', '/music',
                   '/stadt', 'schule']
    accounts = [row for row in search_results
                  if p_link in row[0] and not any(n in row[0] for n in not_profile) and not 'Blog' in row[2]
                        and (any(k.lower() in row[0].lower() for k in comp_keywords) or
                             any(k.lower() in row[0].lower() for k in branch_keywords))]
    if len(accounts) == 0:
        accounts = [row for row in search_results if p_link in row[0] and not any(n in row[0] for n in not_profile)]
    ranking_dict = {}
    for pos, row in enumerate(accounts):
        link, title, content = [str(r) for r in row]
        # One cleanup step
        affixes = ['about', 'impressum']
        for a in affixes:
            if a in link:
                link = link.split(a)[0]
        ranking_dict[link] = len(accounts) - pos
        link_part = link.split(p_link)[1].split('/')[0]
        if link_part in comp_keywords:
            ranking_dict[link] += 2
        for k in comp_keywords:
            if k.lower() in title.lower():
                ranking_dict[link] += 1
            if k in content:
                ranking_dict[link] += 1
        for k in branch_keywords:
            if k.lower() in link.lower():
                ranking_dict[link] += 2
            if k.lower() in title.lower():
                ranking_dict[link] += 2
            if k.lower() in content.lower():
                ranking_dict[link] += 2
        if 'locale=de' in link:
            ranking_dict[link] += 2
        if 'locale' in link and not '=de' in link:
            ranking_dict[link] -= 2
    ranking_dict = {k: v for k, v in ranking_dict.items() if v >= 3}
    ordered_dict = sorted(ranking_dict.items(), key=lambda x:x[1], reverse=True)
    account_list = [key for key, value in ordered_dict if len(str(key)) > 10]
    return account_list


def get_accounts(account_list):
    account = ''
    account2 = ''
    acc2_number = ''
    while len(account_list) >= 1:
        account = account_list.pop(0)
        if '?locale' in account:
            account = account.split('?')[0]
        if len(account) < 10:
            continue
        acc_number = str(extract_number(account)).replace('.','')
        if len(account_list) >= 1:
            account2 = account_list.pop(0)
            acc2_number = str(extract_number(account2)).replace('.','')
        if account in account2 or acc_number in acc2_number:
            account2 = ''
        if account2 in account and len(account2) >= 10:
            account = account2
            account2 = ''
        if account:
            break
    if len(account_list) == 0:
        account_list = ''
    elif len(account_list) == 1:
        account_list = account_list[0]
    return account, account2, account_list


# Interpretation of the language
def lang_interpreter(content):
    excludelist = ['http', 'web', 'follower', 'like', 'community', 'rating', 'joined', 'cookie', 'access', 'online', 'shop']
    eng_words = ['welcome', 'corporate', 'provider', 'products', 'individuals', 'disease']
    ger_words = ['herzlich', 'offiziell', 'erfahrung', 'stadt', 'fragen', 'familie', 'unternehmen', 'verbindung',
                 'produktion', 'vertrieb', 'tochter', 'aktuelle']
    content_list = content.split()
    for e in content_list:
        desc = ' '.join([str(c) for c in content_list if str(c).isalpha()
                         and not any(e in str(c).lower() for e in excludelist)])
    if len(desc) < 5:
        lang = '-'
    else:
        try:
            lang_det = detect(desc)
            if lang_det == 'en':
                lang = 'Englisch/ Internat.'
            elif lang_det == 'de':
                lang = 'Deutsch'
            else:
                lang = 'Andere'
        except:
            lang = '-'
    if any(w in desc.lower() for w in eng_words):
        lang = 'Deutsch'
    if any(w in desc.lower() for w in ger_words):
        lang = 'Englisch/ Internat.'
    return lang