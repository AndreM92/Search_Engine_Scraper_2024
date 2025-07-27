import os
func_import = r"C:\Users\andre\Documents\Python\Web_Crawler\Search_Engine_Scraper_2024"
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

folder_name = "SMP_Automatisierungstechnik 2025"
file_name = "Auswahl_SMP Automatisierungstechnik 2025"
file_path = "C:\\Users\\andre\OneDrive\Desktop/" + folder_name
file_type = ".xlsx"
source_file = file_name + file_type
########################################################################################################################

# Scrape the startpage
def scrape_startpage(driver, website):
    try:
        driver.get(website)
        time.sleep(4)
    except:
        return [], None, website
    website = driver.current_url
    decline_str = "//*[contains(text(), 'ablehnen') or contains(text(), 'Ablehnen') or contains(text(), 'ABLEHNEN') or contains(text(), 'Verweigern')]"
    cookiebuttons = driver.find_elements('xpath', decline_str)
    if len(cookiebuttons) == 0:
        accept_str = "//*[contains(text(), 'akzeptieren') or contains(text(), 'AKZEPTIEREN') or contains(text(), 'einverstanden') or contains(text(), 'zulassen') or contains(text(), 'zustimmen') or contains(text(), 'annehmen') or contains(text(), 'accept')]"
        cookiebuttons = driver.find_elements('xpath', accept_str)
    if len(cookiebuttons) >= 1:
        for c in cookiebuttons:
            try:
                c.click()
            except:
                pass
        time.sleep(2)
    driver.execute_script("window.scrollBy(0,2500)", "")
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pagetext = get_visible_text(soup)
    linklist = list(set(get_all_links(soup)))
    return linklist, pagetext, website

# Scrape the impressum page
def scrape_imp(startpage, linklist):
    for l in linklist:
        if 'impressum' in str(l):
            driver.get(l)
            time.sleep(3)
    if startpage == driver.current_url:
        imp_buttons = driver.find_elements('xpath', "//*[contains(text(), 'Impressum') or contains(text(), 'impressum')]")
        if len(imp_buttons) >= 1:
            for b in imp_buttons:
                try:
                    b.click()
                except:
                    pass
    time.sleep(3)
    if startpage == driver.current_url:
        return [],''
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pagetext = str(get_visible_text(soup))
    if 'Seite existiert nicht' in pagetext or 'Not Found' in pagetext:
        return [], ''
    linklist = list(set(get_all_links(soup)))
    return linklist, pagetext


def main(id, row):
    company = extract_text(row['Firma'])
    website = str(row['Website'])
    if len(str(website)) <= 4:
        return [id, company, website] + ['' for _ in range(9)]
    linklist, pagetext, website = scrape_startpage(driver, website)
    if len(linklist) <= 1 or not pagetext:
        return [id, company, website] + ['' for _ in range(9)]
    linklist_imp, pagetext_imp = scrape_imp(website, linklist)
    if len(linklist) <= 1:
        return [id, company, website] + ['' for _ in range(9)]
    all_links = list(set(linklist + linklist_imp))
    sm_links, linklist = sm_filter(all_links)
    account_list, sm_else = sm_order(sm_links, linklist)
    linklist_f = [l for l in linklist if (l not in account_list and l not in sm_else)]
    linklist_f.sort(key=len)
    crawled_row = [id, company, website] + account_list + [sm_else, linklist_f, pagetext, pagetext_imp]
    return crawled_row

########################################################################################################################

# Starting with an empty table and a number of rows you want so skip
newtable = []

# Run the Crawler/ Scraper
if __name__ == '__main__':
    # Load the excel file with the required data
    # It should contain the company names and websites
    os.chdir(file_path)
    df_source = pd.read_excel(source_file)

    driver, page = start_browser_sel(chromedriver_path, startpage, cred.my_useragent, headless=False)
    for id, row in df_source.iterrows():
        id += 1
        full_row = main(id, row)
        newtable.append(full_row)
        print(full_row[:9])

    # Dataframe
    sm_headers = ['Facebook', 'Instagram', 'LinkedIn', 'TikTok', 'Twitter', 'YouTube', 'X']
    header = ['ID', 'Anbieter', 'Website'] + sm_headers + ['Andere_sm', 'Links', 'Startseite', 'Impressum']
    df_website = pd.DataFrame(newtable,columns=header)

    try:
        # Create an Excel file
        dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        recent_filename = 'Website_Links_' + dt_str_now + '.xlsx'
        df_website.to_excel(recent_filename)
    except:
        # If there are problems with forbidden characters
        df_website.to_csv('output.csv', index=False)

    driver.quit()