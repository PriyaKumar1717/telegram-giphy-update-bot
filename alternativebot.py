import telebot
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import Any

TOKEN = "your_telegram_api_code"

bot = telebot.TeleBot(TOKEN)
tracked_projects = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome to the Giphy Views Tracker Bot! Please enter the Giphy project ID you want to track.")

@bot.message_handler(commands=['daily_updates'])
def enable_daily_updates(message):
    for project_id, project_info in tracked_projects.items():
        if project_info['chat_id'] == message.chat.id:
            tracked_projects[project_id]['daily_updates_enabled'] = True
    bot.reply_to(message, "Daily updates enabled for tracked projects.")

@bot.message_handler(commands=['stop_updates'])
def stop_daily_updates(message):
    for project_id, project_info in tracked_projects.items():
        if project_info['chat_id'] == message.chat.id:
            tracked_projects[project_id]['daily_updates_enabled'] = False

def send_daily_updates():
    for project_id, project_info in tracked_projects.items():
        if project_info and project_info['daily_updates_enabled']:
            fetch_project_views(project_info['message'])

@bot.message_handler(commands=['track'])
def fetch_project_views(message):
    try:
        if len(message.text.split()) >= 2:
            project_id = message.text.split(' ', 1)[1]
            tracked_projects[project_id] = {"message":message,'chat_id': message.chat.id, 'daily_updates_enabled': False}
            bot.reply_to(message, f"Project {project_id} is now being tracked. Please wait for result.")

            url = f"https://giphy.com/gifs/{project_id}"
            options = Options()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            driver.implicitly_wait(10)

            html = driver.page_source
            driver.close()

            soup = BeautifulSoup(html, 'html.parser')
            views_element = soup.find('div', class_='ViewCountContainer-sc-15ri43l')
            if views_element:
                views = views_element.text
                tracked_projects[project_id]['views'] = views
                bot.reply_to(message, f"Total views for project {project_id}: {views}")
            else:
                bot.reply_to(message, f"Views data not found for project {project_id}")
        else:
            bot.reply_to(message, "Please specify the project ID after the /views command.")
    except requests.RequestException as e:
        print(f"Error fetching views for project {project_id}: {e}")
        bot.reply_to(message, f"Error fetching views for project {project_id}: {e}")
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, f"An unexpected error occurred: {e}")

def telegram_polling():
    bot.infinity_polling()

def daily_update_loop():
    while True:
        current_time = time.localtime()
        if current_time.tm_hour == 10 and current_time.tm_min == 0:
            send_daily_updates()
            time.sleep(60)  # Sleep for a minute to avoid repeated updates
        time.sleep(30)  # Check every 30 seconds

thread1 = threading.Thread(target=telegram_polling)
thread1.start()

thread2 = threading.Thread(target=daily_update_loop)
thread2.start()
