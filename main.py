import time
import json

from bs4 import BeautifulSoup as bs

from selenium import webdriver as wd
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager

url = 'https://www.sports.ru/football/tournament/rfpl/'

browser = wd.Chrome(service=ChromeService(ChromeDriverManager().install()))
browser.get(url)

open_search = browser.find_element(By.CLASS_NAME, "navigation-search-btn")
open_search.click()

search = browser.find_element(By.CLASS_NAME,"navigation-search-popup__input")
search.send_keys('НБА')

time.sleep(1)

open_search = browser.find_element(By.CLASS_NAME, "navigation-search-results__name")
open_search.click()



soup = bs(browser.page_source,'html.parser')
data = []
all_publics = soup.find('div',class_='nl-item')
all_p = all_publics.find_all('p')

for article in all_p:
    a = article.find('span').get_text()
    b = article.find('a').get_text()
    c = article.find('a')['href']
    data.append({'time': a, 'title': b, 'link': c})
    print(f'Да ну насмерть чтоже будет в {a}. Это же {b}. А вот и ссылка чтобы перейти {c}')

with open('nba_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)