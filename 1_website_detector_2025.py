import os
func_import = r"C:\Users\andre\Documents\Python\Web_Crawler\Search_Engine_Scraper_2024"
os.chdir(func_import)
from search_crawler_functions import *
from search_crawler_credentials import *
chromedriver_path = r"C:\Users\andre\Documents\Python\chromedriver-win64\chromedriver.exe"
startpage = 'https://www.google.de'

from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import re
from datetime import datetime, timedelta
import time

folder_name = "SMP_Automatisierungstechnik 2025"
file_name = "Auswahl_SMP Automatisierungstechnik"
file_path = r"C:\Users\andre\OneDrive\Desktop/" + folder_name
file_type = ".xlsx"
source_file = file_name + file_type
########################################################################################################################

def main_function(driver, startpage, row, col_list, platform):
    comp_keywords, company, web_address, web_address2 = get_company_keywords(row, col_list)
    keyword = company
    if platform:
        keyword = keyword + ' ' + platform

    search_url = search_for(driver, startpage, keyword)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pagetext = get_visible_text(soup)
    if search_url == startpage or '/sorry' in search_url or 'CAPTCHA' in pagetext:
        input('Press ENTER after solving the captcha')
        soup = BeautifulSoup(driver.page_source,'lxml')
    sresults = get_search_results(soup)
    website, website_options = get_website(comp_keywords, sresults, web_address, web_address2)
    if not website and len(website_options) == 0:
        search_url = search_for(driver, startpage, company)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        sresults = get_search_results(soup)
        website, website_options = get_website(comp_keywords, sresults, web_address, web_address2)
    linklist = get_all_links(soup)
    sm_links, linklist = sm_filter(linklist)
    other_links = [l for l in linklist if not any(l in e for e in sm_links) and not any(l in e for e in website_options)]
    result_row = [company, website, website_options, sm_links, other_links]
    print(result_row)
    return result_row

########################################################################################################################
# Starting with an empty table and a number of rows you want so skip
newtable = []
ID_old = 0
platform = ''

# Run the Crawler/ Scraper
if __name__ == '__main__':
    # Load the excel file with the required data
    # It should contain the company names and ideally some search keywords for their website
    os.chdir(file_path)
    df_source = pd.read_excel(source_file)
    col_list = list(df_source.columns)

    # Start the selenium chromedriver
    driver, startpage = start_browser_sel(chromedriver_path, startpage, my_useragent, headless=False)

    # search queries
    for ID, row in df_source.iterrows():
        if 'ID' in col_list:
            ID = row['ID']
        if ID < ID_old:
            continue
        ID_old = ID

        if platform and platform in col_list:
            platform_link = extract_text(row[platform])
            if platform_link and len(platform_link) > 10:
                continue
        result_row = [IDn] + main_function(driver, startpage, row, col_list, platform)
        if not result_row:
            break
        newtable.append(result_row)

    # DataFrame
    header = ['ID','Anbieter','Webseite','Alternative Webseiten','Social Media','Weitere Links']
    df_company_links = pd.DataFrame(newtable,columns=header)

    # Create an Excel file
    dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    recent_filename = 'Automatisierungstechnik_Links_' + dt_str_now + '.xlsx'
    df_company_links.to_excel(recent_filename)