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
chromedriver_path = r"C:\Users\andre\Documents\Python\chromedriver-win64\chromedriver.exe"
path_to_crawler_functions = r'C:\Users\andre\Documents\Python\Web_Scraper\Search_Engine_Scraper_2024'
file_path = r"C:\Users\andre\OneDrive\Desktop\Nahrungsergaenzungsmittel"
source_file = 'Liste_Nahrungsergänzungsmittel_2024_Auswahl.xlsx'
branch_keywords = ['nutrition', 'vitamin', 'mineral', 'protein', 'supplement', 'diet', 'health', 'ernährung',
                   'ergänzung', 'gesundheit', 'nährstoff', 'fitness', 'sport', 'leistung']
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

def rank_sm_accounts(platform, comp_keywords, branch_keywords, search_results):
    p_link = platform.lower() + '.com/'
    not_profile = ['/post', 'hashtag', 'sharer','/status', 'photo/', 'photos', 'watch?', '/video/', 'discover', '.help',
                    'reels', 'story', 'explore', 'playlist', 'sharer', 'policy', 'privacy', 'instagram.com/p/',
                   '/tag/','/embed/']
    accounts = [row for row in search_results if p_link in row[0] and any(k in row[0] for k in comp_keywords)
                and not any(n in row[0] for n in not_profile)]
    ranking_dict = {}
    for pos, row in enumerate(accounts):
        link, title, content = row
        ranking_dict[link] = len(accounts) - pos
        link_part = link.split(p_link)[1].split('/')[0]
        if link_part in comp_keywords:
            ranking_dict[link] += 2
        for k in comp_keywords:
            if k in title:
                ranking_dict[link] += 1
            if k in content:
                ranking_dict[link] += 1
        for k in branch_keywords:
            if k in title.lower():
                ranking_dict[link] += 1
            if k in content.lower():
                ranking_dict[link] += 1
    ordered_dict = sorted(ranking_dict.items(), key=lambda x:x[1], reverse=True)
    account_list = [key for key, value in ordered_dict]
    return account_list


if __name__ == '__main__':
    # Choose a Social Media Platform
    platform = 'Facebook'
    os.chdir(path_to_crawler_functions)
    from search_crawler_functions import *
    import search_crawler_credentials as cred
    os.chdir(file_path)
    df_source = pd.read_excel(source_file)
    col_list = list(df_source.columns)

    new_table = []
    for count, row in df_source.iterrows():
        id = extract_every_number(row['ID'])
        print(count, id)
        account = str(row[platform])
        comp_keywords, company = get_company_keywords(row, col_list)
#        if len(account) > 10 and any(k in account for k in comp_keywords):
        if len(account) > 10 and company.lower() in account.lower():
            complete_row = [id, company, account, '']
            new_table.append(complete_row)
            continue

        search_url = compose_search_url(platform, company)
        driver, page = start_browser_sel(chromedriver_path, search_url, headless=True)
        search_results = collect_search_results(driver)
        account_list = rank_sm_accounts(platform, comp_keywords, branch_keywords, search_results)
        if len(account_list) >= 1:
            account = account_list.pop(0)
        new_row = [id, company, account, account_list]
        new_table.append(new_row)

    # Dataframe
    header = ['ID', 'Anbieter', platform, 'alt_links']
    df_se = pd.DataFrame(new_table, columns=header)

    # Create an Excel file
    dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    recent_filename = 'Search_Results_' + platform + '_' + dt_str_now + '.xlsx'
    df_se.to_excel(recent_filename)


    driver.quit()