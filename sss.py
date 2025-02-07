#добавил изменения в квадрате

from time import sleep

import requests
import telebot
import time
import json
import threading
from datetime import datetime
from collections import deque
from bs4 import BeautifulSoup as bs
from selenium import webdriver as wd
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


TELEGRAM_TOKEN = "7932194967:AAGeR7N7mpoPKBnTRF1WdkLBdKJlbtOXGXo"
URL = 'https://www.sports.ru/'
JSON_FILE = 'sports_events.json'
USER_REQUEST_LIMIT = 5
REQUEST_TIMEOUT = 60


bot = telebot.TeleBot(TELEGRAM_TOKEN)
parsing_running = False
parsing_thread = None
user_request_history = {}

chrome_options = Options()
chrome_options.add_argument("--headless=new")


def parse_sports_events(url):
    try:

        data = []

        browser = wd.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        browser.get(url)
        sleep(2)

        soup = bs(browser.page_source, 'html.parser')
        all_publics = soup.find('div', class_='nl-item')
        all_p = all_publics.find_all('p')
        print(all_p)
        for article in all_p:
            a = article.find('span').get_text()
            b = article.find('a').get_text()
            c = article.find('a')['href']
            data.append({'time': a, 'title': b, 'link': c})
            print(f'Да ну насмерть чтоже будет в {a}. Это же {b}. А вот и ссылка чтобы перейти {c}')
        return data
    except Exception as e:
        print(f"Ошибка при парсинге: {e}")
        return None

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def start_parsing(chat_id,url):
    global parsing_running, parsing_thread
    if parsing_running:
        bot.send_message(chat_id, "Парсинг уже запущен.")
        return

    parsing_running = True
    bot.send_message(chat_id, "Запуск парсинга...")

    def parsing_task():
        global parsing_running
        events = parse_sports_events(url)
        if events:
            save_to_json(events, JSON_FILE)
            bot.send_message(chat_id, "Парсинг завершен. Результаты сохранены в sports_events.json.")
            send_parsed_data(chat_id)
        else:
            bot.send_message(chat_id, "Парсинг не удался.")
        parsing_running = False

    parsing_thread = threading.Thread(target=parsing_task)
    parsing_thread.start()

def stop_parsing(chat_id):
    global parsing_running, parsing_thread
    if not parsing_running:
        bot.send_message(chat_id, "Парсинг не запущен.")
        return

    parsing_running = False
    bot.send_message(chat_id, "Попытка остановить парсинг...  Это может занять некоторое время.")

def send_parsed_data(chat_id):
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            bot.send_message(chat_id, "Нет данных для отображения.")
            return

        message = "<b>Спортивные события:</b>\n"
        for event in data:
            message += f"<b>{event['time']}</b>\n"
            message += f"Дата: {event['title']}\n"
            message += f"{event['link']}\n\n"

        for i in range(0, len(message), 4096):
            bot.send_message(chat_id, message[i:i+4096], parse_mode='HTML')

    except FileNotFoundError:
        bot.send_message(chat_id, "Файл с данными не найден.")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при отправке данных: {e}")

def send_file(chat_id, filename):

    try:
        with open(filename, 'rb') as f:
            bot.send_document(chat_id, f)
    except FileNotFoundError:
        bot.send_message(chat_id, "Файл не найден.")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при отправке файла: {e}")

def is_user_rate_limited(user_id):
    now = datetime.now()

    if user_id not in user_request_history:
        user_request_history[user_id] = deque()

    request_queue = user_request_history[user_id]


    while request_queue and (now - request_queue[0]).total_seconds() > 60:
        request_queue.popleft()

    if len(request_queue) >= USER_REQUEST_LIMIT:
        return True

    request_queue.append(now)
    return False


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот для парсинга спортивных событий с sports.ru.\n"
                     "Доступные команды:\n"
                     "/start_parsing - Запустить парсинг\n"
                     "/stop_parsing - Остановить парсинг\n"
                     "/show_data - Показать последние спарсенные данные\n"
                     "/get_file - Получить файл с данными")

@bot.message_handler(commands=['start_parsing'])
def start_parsing_command(message):
    user_id = message.from_user.id
    if is_user_rate_limited(user_id):
        bot.reply_to(message, f"Слишком много запросов. Пожалуйста, подождите {REQUEST_TIMEOUT} секунд.")
        return
    bot.send_message(message.chat.id,"/barcelona - Барселона\n"
                                     "/nba - НБА\n")

@bot.message_handler(commands=['barcelona'])
def start_parsing_barcelona(message):
    user_id = message.from_user.id
    if is_user_rate_limited(user_id):
        bot.reply_to(message, f"Слишком много запросов. Пожалуйста, подождите {REQUEST_TIMEOUT} секунд.")
        return
    start_parsing(message.chat.id,'https://www.sports.ru/football/club/barcelona/')



@bot.message_handler(commands=['nba'])
def start_parsing_barcelona(message):
    user_id = message.from_user.id
    if is_user_rate_limited(user_id):
        bot.reply_to(message, f"Слишком много запросов. Пожалуйста, подождите {REQUEST_TIMEOUT} секунд.")
        return
    start_parsing(message.chat.id,'https://www.sports.ru/basketball/tournament/nba/')


@bot.message_handler(commands=['stop_parsing'])
def stop_parsing_command(message):
    user_id = message.from_user.id
    if is_user_rate_limited(user_id):
        bot.reply_to(message, f"Слишком много запросов. Пожалуйста, подождите {REQUEST_TIMEOUT} секунд.")
        return

    stop_parsing(message.chat.id)

@bot.message_handler(commands=['show_data'])
def show_data_command(message):
    user_id = message.from_user.id
    if is_user_rate_limited(user_id):
        bot.reply_to(message, f"Слишком много запросов. Пожалуйста, подождите {REQUEST_TIMEOUT} секунд.")
        return

    send_parsed_data(message.chat.id)

@bot.message_handler(commands=['get_file'])
def get_file_command(message):
    user_id = message.from_user.id
    if is_user_rate_limited(user_id):
        bot.reply_to(message, f"Слишком много запросов. Пожалуйста, подождите {REQUEST_TIMEOUT} секунд.")
        return

    send_file(message.chat.id, JSON_FILE)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
