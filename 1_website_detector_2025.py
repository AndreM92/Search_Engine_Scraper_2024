
import os
from datetime import datetime, timedelta
func_import = r"C:\Users\andre\Documents\Python\Web_Crawler\Search_Engine_Scraper_2024"
os.chdir(func_import)
from search_crawler_functions import *
from search_crawler_credentials import *
chromedriver_path = r"C:\Users\andre\Documents\Python\chromedriver-win64\chromedriver.exe"
startpage = 'https://www.google.de'

folder_name = "SMP_Glücksspiel 2025"
file_name = "Auswahl SMP Glücksspiel_2025-11-15"
file_path = r"C:\Users\andre\OneDrive\Desktop/" + folder_name
source_file = file_name + ".xlsx"
branch_keywords = ['automat', 'bonus', 'casino', 'glück', 'legal', 'poker', 'spiel', 'sport', 'wette']
########################################################################################################################

def main_function(driver, startpage, row, col_list):
    comp_keywords, company, web_address, web_address2 = get_company_keywords(row, col_list)
    keyword = company
    search_url = search_for(driver, startpage, keyword)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pagetext = get_visible_text(soup)
    if search_url == startpage or '/sorry' in search_url or 'CAPTCHA' in pagetext:
        input('Press ENTER after solving the captcha')
        soup = BeautifulSoup(driver.page_source,'lxml')
    sresults = get_search_results(soup)
    website, website_options = get_website(comp_keywords, sresults, web_address, web_address2, branch_keywords)
    if not website and len(website_options) == 0:
        search_url = search_for(driver, startpage, company)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        sresults = get_search_results(soup)
        website, website_options = get_website(comp_keywords, sresults, web_address, web_address2)
    linklist = get_all_links(soup)
    sm_links, linklist = sm_filter(linklist)
    other_links = [l for l in linklist if not any(l in e for e in sm_links) and not any(l in e for e in website_options)]
    result_row = [company, website, website_options, sm_links, other_links]
    return result_row

########################################################################################################################
# Run the Crawler/ Scraper
if __name__ == '__main__':
    # Load the excel file with the required data
    # It should contain the company names and ideally some search keywords for their website
    os.chdir(file_path)
    df_source = pd.read_excel(source_file)
    col_list = list(df_source.columns)

    # Start with an empty table and a number of rows you want so skip
    newtable = []
    start_ID = 175

    # Start the selenium chromedriver
    driver, startpage = start_browser_sel(chromedriver_path, startpage, my_useragent, headless=False)

    # search queries
    for ID, row in df_source.iterrows():
        if 'ID' in col_list:
            ID = row['ID']
        if ID < start_ID:
            continue
        website = ''
        if 'Website' in col_list:
            website = str(row['Website'])
        if len(website) >= 13:
            comp_keywords, company, web_address, web_address2 = get_company_keywords(row, col_list)
            result_row = [ID, company, website, 'original', '', '']
            newtable.append(result_row)
            print(result_row)
            start_ID = ID + 1
            continue
        result_row = [ID] + main_function(driver, startpage, row, col_list)
        if not result_row:
            break
        newtable.append(result_row)
        print(result_row)
        start_ID = ID + 1

    # DataFrame
    header = ['ID','Anbieter','Website','Alternative Websites','Social Media','Weitere Links']
    df_company_links = pd.DataFrame(newtable,columns=header)

    # Create an Excel file
    dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    recent_filename = file_name + '_Websites_' + dt_str_now + '.xlsx'
    df_company_links.to_excel(recent_filename)

    driver.quit()