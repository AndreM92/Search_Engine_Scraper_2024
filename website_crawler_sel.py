import os
func_import = r"C:\Users\andre\Documents\Python\Web_Scraper\Search_Engine_Scraper_2024"
os.chdir(func_import)
from search_crawler_functions import *
chromedriver_path = r"C:\Users\andre\Documents\Python\chromedriver-win64\chromedriver.exe"
startpage = 'https://www.google.de'

from bs4 import BeautifulSoup

import numpy as np
import pandas as pd
import re
from datetime import datetime, timedelta
import time
########################################################################################################################

# Scrape the startpage
def scrape_startpage(driver, website):
    try:
        driver.get(website)
        time.sleep(5)
    except:
        return ['' for _ in range(4)]
    decline_str = "//*[contains(text(), 'ablehnen') or contains(text(), 'Ablehnen') or contains(text(), 'ABLEHNEN') or contains(text(), 'Verweigern')]"
    cookiebuttons = driver.find_elements('xpath', decline_str)
    if len(cookiebuttons) == 0:
        accept_str = "//*[contains(text(), 'akzeptieren') or contains(text(), 'AKZEPTIEREN') or contains(text(), 'einverstanden')]"
        cookiebuttons = driver.find_elements('xpath', accept_str)
    if len(cookiebuttons) >= 1:
        for c in cookiebuttons:
            try:
                c.click()
            except:
                pass
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pagetext = get_visible_text(soup)
    linklist = list(set(get_all_links(soup)))
    sm_links, linklist = sm_filter(linklist)
    account_list, sm_else = sm_order(sm_links, linklist)
    linklist_f = [l for l in linklist if (l not in account_list and l not in sm_else)]
    linklist_f.sort(key=len)
    return account_list, sm_else, linklist_f, pagetext

# Scrape the impressum page
def scrape_imp(website, linklist_f):
    curr_page = driver.current_url
    imp_buttons = driver.find_elements('xpath', "//*[contains(text(), 'Impressum') or contains(text(), 'impressum')]")
    if len(imp_buttons) >= 1:
        for b in imp_buttons:
            try:
                b.click()
                time.sleep(3)
            except:
                pass
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    imp_pagetext = str(get_visible_text(soup))
    if 'Seite existiert nicht' in imp_pagetext or 'Not Found' in imp_pagetext or curr_page == driver.current_url:
        imp_page = [l for l in linklist_f if 'impressum' in str(l).lower()]
        if len(imp_page) == 0:
            if website[-1] != '/':
                imp_page = website + '/impressum'
            else:
                imp_page = website + 'impressum'
        try:
            driver.get(imp_page)
            time.sleep(3)
        except:
            return '', ''
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        imp_pagetext = get_visible_text(soup)
        if 'Seite existiert nicht' in imp_pagetext or 'Not Found' in imp_pagetext or curr_page == driver.current_url:
            return '', ''
    linklist = list(set(get_all_links(soup)))
    imp_links = [l for l in linklist if l not in linklist_f]
    return imp_links, imp_pagetext
########################################################################################################################

# Starting with an empty table and a number of rows you want so skip
newtable = []
skip = -1

# Run the Crawler/ Scraper
if __name__ == '__main__':
    # Load the excel file with the required data
    # It should contain the company names and websites
    output_path = r"C:\Users\andre\OneDrive\Desktop\Nahrungsergaenzungsmittel"
    os.chdir(output_path)
    source_file = r"Liste_Nahrungsergaenzungsmittel_2024_20240101.xlsx"
    df_source = pd.read_excel(source_file)

    driver, startpage = start_browser_sel(chromedriver_path, startpage)

    for id, row in df_source.iterrows():
 #   def main (id, row):
  #      if id <= 432:
  #          continue
        company = extract_text(row['Anbieter'])
        website = str(row['Webseite'])
        if len(website) <= 4:
            website = ''
        if website:
            account_links, sm_else, linklist_f, pagetext = scrape_startpage(driver, website)
            imp_links, imp_pagetext = scrape_imp(website, linklist_f)
            imp_links_f = [l for l in imp_links if l not in account_links and l not in sm_else]
        if len(str(account_links)) <= 4:
            account_links = ['' for _ in range(6)]
        account_links_se = []
        sm_se_str = str(row['Social Media'])
        if len(sm_se_str) > 4 and '[' in sm_se_str:
            try:
                sm_se = eval(row['Social Media'])
                sm_se_else = []
                for l in sm_se:
                    account_list = [l for l in account_links if len(str(l)) > 4]
                    if any(a in l for a in account_list):
                        continue
                    sm_se_else.append(l)
                    account_links_se, sm_else_se = sm_order(sm_se_else, sm_se_else)
            except:
                pass
        if len(str(account_links_se)) <= 4:
            account_links_se = ['' for _ in range(6)]

        full_row = [id, company, website] + account_links + account_links_se + [sm_else, linklist_f, pagetext,
                                                                                    imp_links_f, imp_pagetext]
        newtable.append(full_row)
        print(id, company, website, account_links)


    # Dataframe
    sm_headers = ['Facebook', 'Instagram', 'LinkedIn', 'TikTok', 'X', 'YouTube']
    sm_headers2 = [h + '2' for h in sm_headers]
    header = ['ID', 'Anbieter', 'Website'] + sm_headers + sm_headers2 + \
             ['Andere_sm', 'Links', 'Startseite', 'Links_Imp', 'Impressum']
    df_website = pd.DataFrame(newtable,columns=header)

    # Create an Excel file
    dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    recent_filename = 'Nahrungsergaenzungsmittel_Webseiten' + dt_str_now + '.xlsx'
    df_website.to_excel(recent_filename)

    df_website.to_csv('output.csv', index=False)



'''
cookie_twostep = driver.find_elements('xpath', "//*[contains(text(), 'klicke hier')]")
if len(cookie_twostep) >= 1:
    for c in cookie_twostep:
        try:
            c.click()
        except:
            pass
'''