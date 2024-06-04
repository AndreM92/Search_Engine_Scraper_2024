import re
from datetime import datetime, timedelta
import time
import os

chromedriver_path = r"C:\Users\andre\Documents\Python\chromedriver-win64\chromedriver.exe"
path_to_crawler_functions = r"C:\Users\andre\Documents\Python\Web_Crawler\Search_Engine_Scraper_2024"
folder_name = "SMP_Brauereien_2024"
file_path = "C:\\Users\\andre\OneDrive\Desktop/" + folder_name
source_file = "Liste_Brauereien_Ergänzung.xlsx"
branch_keywords = ['Brauerei', 'Brauhaus', 'Bräu', 'braeu', 'Bier', 'brewing']

########################################################################################################################

def compose_search_url(platform, company):
    keyword = ' '.join([company.lower(), platform.lower()]).replace('&', 'und').replace(' ', '+')
    search_engine = 'https://www.google.com/search?q='
    lang_loc = '&gl=de&hl=de&num=50&start=0&location=Germany&uule=w+CAIQICIHR2VybWFueQ'
    return f"{search_engine}{keyword}{lang_loc}"

def collect_search_results(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = get_search_results(soup)
    return results

def rank_sm_accounts(platform, comp_keywords, branch_keywords, search_results):
    p_link = platform.lower() + '.com/'
    not_profile = ['/post', 'hashtag', 'sharer','/status', '/photo', 'photos', 'watch?', '/video', 'discover', '.help',
                'groups', 'reels', 'story', 'explore', 'playlist', 'sharer', 'policy', 'privacy', 'instagram.com/p/',
                '/blog', '/event', '/reel/', '/tag/', '/embed/']
    accounts = [row for row in search_results
                  if p_link in row[0] and not any(n in row[0] for n in not_profile) and not 'Blog' in row[2]
                        and (any(k.lower() in row[0].lower() for k in comp_keywords) or
                             any(k.lower() in row[0].lower() for k in branch_keywords))]
    if len(accounts) == 0:
        accounts = [row for row in search_results if p_link in row[0] and not any(n in row[0] for n in not_profile)]
    ranking_dict = {}
    for pos, row in enumerate(accounts):
        link, title, content = [str(r) for r in row]
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
    # If you only want to open the browser once (include driver.get(search_url) into the loop)
    search_url = 'https://www.google.de/'
    new_table = []

    driver, page = start_browser_sel(chromedriver_path, search_url, headless=False)
    for count, row in df_source.iterrows():
#        old_count = 768
        if count < old_count:
            continue
        old_count = count

        id = extract_every_number(row['ID'])
        account = ''
        comp_keywords, company = get_company_keywords(row, col_list)
        search_url = compose_search_url(platform, company)
        # Start the driver for every search request
#        driver, page = start_browser_sel(chromedriver_path, search_url, headless=False)
        driver.get(search_url)
        time.sleep(2)
        # In case there is a bot ban or website error
        if '/sorry' in driver.current_url:
            input('Press ENTER after solving the captcha')
#            driver.quit()
#            time.sleep(3)
#            driver, page = start_browser_sel(chromedriver_path, search_url, headless=False)
#            time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pagetext = get_visible_text(soup)
        if '403' in pagetext[:100] or 'That’s an error' in pagetext or 'not have permission' in pagetext:
            driver.quit()
            break
        search_results = collect_search_results(driver)
        account_list = rank_sm_accounts(platform, comp_keywords, branch_keywords, search_results)
        if len(account_list) >= 1:
            account = account_list.pop(0)
#        elif len(account_list) == 0:

        new_row = [id, company, account, account_list]
        new_table.append(new_row)
#        driver.quit()
        print(count, id, account)

    # Dataframe
    header = ['ID', 'Anbieter', platform, 'alt_links']
    df_se = pd.DataFrame(new_table, columns=header)

    # Create an Excel file
    dt_str_now = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    recent_filename = 'Search_Results_' + platform + '_' + dt_str_now + '.xlsx'
    df_se.to_excel(recent_filename)


########################################################################################################################
'''
new_table = new_table[:16]
for n in new_table:
    print(n)
    
cookies
try:
    cookiebanner = driver.find_element('xpath', "//*[text()='Alle ablehnen']")
    cookiebanner.click()
except:
    pass
if len(account) > 10 and (any(k.lower() in account.lower() for k in comp_keywords) or 'channel' in account):
    complete_row = [id, company, account, '']
    new_table.append(complete_row)
    print(count, id)
    continue
print(new_table[-1])
'''