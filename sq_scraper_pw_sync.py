import os

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from bs4.element import Comment
import lxml
import re

import numpy as np
import pandas as pd

import time
from datetime import datetime, timedelta


def compose_search_url(platform, company):
    keyword = ' '.join([company.lower(), platform.lower()]).replace(' ', '+')
    keyword = 'More Nutrition'
    search_engine = 'https://www.google.com/search?q='
    lang_loc = '&gl=de&hl=de&num=50&start=0&location=Germany&uule=w+CAIQICIHR2VybWFueQ'
    return f"{search_engine}{keyword}{lang_loc}"


def start_pw_browser(sync_playwright, user_agent, url):
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False)
    # Open the browser with an user agent
    browser_agent = browser.new_context(user_agent=user_agent)
    page = browser_agent.new_page()
    page.goto(url)
    time.sleep(1)
    try:
        decline_cookies = page.get_by_role("button", name="Ablehnen")
        decline_cookies.click()
        time.sleep(1)
    except:
        pass
    return pw, browser_agent, page


def collect_search_results(page):
    soup = BeautifulSoup(page.content(), 'html.parser')
    results = get_search_results(soup)
    return results


if __name__ == '__main__':
    os.chdir(r'C:\Users\andre\Documents\Python\Web_Scraper\Search_Engine_Scraper_2024')
    from search_crawler_functions import *
    import search_crawler_credentials as cred
    # Insert the company and Platform you want to search for
    company = 'More Nutrition'
    platform = 'Instagram'

    url = compose_search_url(platform, company)
    pw, browser, page = start_pw_browser(sync_playwright, cred.my_useragent, url)
    results = collect_search_results(page)

    # Dataframe
    header = ['Link', 'Title', 'Content']
    df_se = pd.DataFrame(results, columns=header)

    # Create an Excel file and change the file path where you want to save the results
    newpath = r"C:\Users\andre\OneDrive\Desktop\Nahrungsergaenzungsmittel"
    os.chdir(newpath)
    dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    recent_filename = 'Search_Results_' + company + '_' + dt_str_now + '.xlsx'
    df_se.to_excel(recent_filename)

    browser.close()
    pw.stop()