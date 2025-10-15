
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

folder_name = "SMP_Mineralwasser 2025"
file_name = "Auswahl SMP Mineralwasser_2025-10-14"
file_path = "C:\\Users\\andre\OneDrive\Desktop/" + folder_name
file_type = ".xlsx"
source_file = file_name + file_type
branch_keywords = [
    'Abfüll', 'Getränk', 'Lebensmittel', 'PET-', 'Flasche', 'Etikett', 'Dosier', 'Wasser', 'Mineral', 'Füllstand',
    'Verpackung', 'Trink', 'Durst']
########################################################################################################################

def scrape_page(driver, startpage, row, col_list, platform):
    comp_keywords, company, website, web_address2 = get_company_keywords(row, col_list)
    account = extract_text(row[platform])
    if len(account) > 10:
        if '?locale' in account:
            account = account.split('?locale')[0]
        result_row = [company, website, account, '', 'account from website']
        return result_row

    keyword = company + ' ' + platform
    search_url = search_for(driver, startpage, keyword)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pagetext = get_visible_text(soup)
    if search_url == startpage or '/sorry' in search_url or 'CAPTCHA' in pagetext:
        input('Press ENTER after solving the captcha')
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pagetext = get_visible_text(soup)
    if '403' in pagetext[:100] or 'That’s an error' in pagetext or 'not have permission' in pagetext:
        result_row = [company, website, account, '', 'Error: ' + pagetext]
        return result_row

    search_results = get_search_results(soup)
    account_list = rank_sm_accounts(platform, comp_keywords, branch_keywords, search_results)
    account, account2, account_list = get_accounts(account_list)
    result_row = [company, website, account, account2, account_list]
    return result_row

#######################################################################################################################
new_table = []
ID_old = 0
platform = 'LinkedIn'

if __name__ == '__main__':
    os.chdir(file_path)
    df_source = pd.read_excel(source_file)
    col_list = list(df_source.columns)

    # Start the selenium chromedriver
    driver, startpage = start_browser_sel(chromedriver_path, startpage, my_useragent, headless=False)

    for ID, row in df_source.iterrows():
        if 'ID' in col_list:
            ID = row['ID']
        if ID <= ID_old:
            continue
        ID_old = ID

        result_row = scrape_page(driver, startpage, row, col_list, platform)
        if 'Error' in result_row[-1]:
            input('Press ENTER after solving the issue')
        full_row = [ID] + result_row
        print(full_row)
        new_table.append(full_row)

    driver.quit()

    # Dataframe
    header = ['ID', 'Firma', 'Website', platform, platform + '_2', 'alternatives']
    df_se = pd.DataFrame(new_table, columns=header)

    # Create an Excel file
    dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    recent_filename = 'Search_Results_' + platform + '_' + dt_str_now + '.xlsx'
    df_se.to_excel(recent_filename)