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

folder_name = "SMP_Automatisierungstechnik"
file_name = "Kontakte_Automatisierungstechnik_gekürzt"
file_path = r"C:\Users\andre\OneDrive\Desktop/" + folder_name
file_type = ".xlsx"
source_file = file_name + file_type

########################################################################################################################
# Search query scraping
def compose_search_url(platform, company):
    #    if platform == 'X':
    #       platform = 'Twitter'
    keyword = ' '.join([company.lower(), platform.lower()]).replace('&', 'und').replace(' ', '+')
    search_engine = 'https://www.google.com/search?q='
    lang_loc = '&gl=de&hl=de&num=50&start=0&location=Germany&uule=w+CAIQICIHR2VybWFueQ'
    return f"{search_engine}{keyword}{lang_loc}"

def main_function(driver, startpage, row, col_list):
    comp_keywords, company = get_company_keywords(row, col_list)

    search_url = search_for(driver, startpage, company)

    '''
    # search query scraper
    platform = ''
    search_url = compose_search_url(platform, company)
    driver.get(search_url)
    time.sleep(1)
    '''

    if search_url == startpage or '/sorry' in driver.current_url:
        driver.quit()
        return None
#           time.sleep(7)
    soup = BeautifulSoup(driver.page_source,'lxml')
    sresults = get_search_results(soup)
    website, website_options = get_website(comp_keywords, sresults)
    if not website and len(website_options) == 0:
        search_url = search_for(driver, startpage, company)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        sresults = get_search_results(soup)
        website, website_options = get_website(comp_keywords, sresults)
    linklist = get_all_links(soup)
    sm_links, linklist = sm_filter(linklist)
    other_links = [l for l in linklist if not any(l in e for e in sm_links) and not any(l in e for e in website_options)]
    result_row = [company, website, website_options, sm_links, other_links]
    print(result_row[:3])
    return result_row

########################################################################################################################
# Starting with an empty table and a number of rows you want so skip
newtable = []
skip = -1

# Run the Crawler/ Scraper
if __name__ == '__main__':
    # Load the excel file with the required data
    # It should contain the company names and ideally some search keywords for their website
    os.chdir(file_path)
    df_source = pd.read_excel(source_file)
    col_list = list(df_source.columns)
    newtable = []
    ID_old = 1

    # Start the selenium chromedriver
    driver, startpage = start_browser_sel(chromedriver_path, startpage, my_useragent, headless=False)

    # search queries
    IDn = 0
    for id, row in df_source.iterrows():
        # new IDs
        IDn += 1
        if IDn < ID_old:
            continue

        result_row = [IDn] + main_function(driver, startpage, row, col_list)
        if not result_row:
            break

        newtable.append(result_row)
        ID_old += 1

    # DataFrame
    header = ['ID','Anbieter','Webseite','Alternative Webseiten','Social Media','Weitere Links']
    df_company_links = pd.DataFrame(newtable,columns=header)

    # Create an Excel file
    dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    recent_filename = 'Automatisierungstechnik_Links_' + dt_str_now + '.xlsx'
    df_company_links.to_excel(recent_filename)


#newtable = newtable[:-1]
#for t in newtable:
#    print(t[:3])
#print(newtable[-1][:4])