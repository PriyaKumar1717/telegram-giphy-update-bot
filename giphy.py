import telebot
import requests
import schedule
import time
from bs4 import BeautifulSoup
from selenium import webdriver
import schedule
from selenium.webdriver.chrome.options import Options
import threading
import json
import pymongo


TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
GIPHY_API_KEY = "YOUR_GIPHY_API_KEY"

bot = telebot.TeleBot(TOKEN)
tracked_projects = {} #Storing locally for now, can be improved by persisting database.

client = pymongo.MongoClient("YOUR_MONGODB_URL")
db = client["GiphyBOT"]
tracked_projects_collection = db["Total_views"]

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome to the Giphy Views Tracker Bot! Please enter the Giphy project ID you want to track.")


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.reply_to(message, "Commands:\n/start - Start the bot\n/help - Get help\n/track <project_id> - Track a Giphy project\n/daily_updates - Enable daily updates\n/stop_updates - Stop daily updates")


# @bot.message_handler(commands=['track'])
# def track_project(message):
#     # Check if there are at least two parts after splitting
#     if len(message.text.split()) >= 2:
#         # Extract project_id from message
#         project_id = message.text.split(' ', 1)[1]
#         tracked_projects[project_id] = {"message":message,'chat_id': message.chat.id, 'daily_updates_enabled': False}
#         bot.reply_to(message, f"Project {project_id} is now being tracked.")
#     else:
#         bot.reply_to(message, "Please specify the project ID after the /track command.")
    

@bot.message_handler(commands=['daily_updates'])
def enable_daily_updates(message):
    # Enable daily updates for tracked projects
    for project_id, project_info in tracked_projects.items():
        if project_info['chat_id'] == message.chat.id:
            tracked_projects[project_id]['daily_updates_enabled'] = True
    bot.reply_to(message, "Daily updates enabled for tracked projects.")


@bot.message_handler(commands=['stop_updates'])
def stop_daily_updates(message):
    # Stop daily updates for tracked projects
    for project_id, project_info in tracked_projects.items():
        if project_info['chat_id'] == message.chat.id:
            tracked_projects[project_id]['daily_updates_enabled'] = False




def send_daily_updates():
    print('UPDATES')
    # Iterate over tracked projects and send daily updates if enabled
    for project_id, project_info in tracked_projects.items():
        if project_info and project_info['message'] and project_info['daily_updates_enabled']:
         fetch_project_views(project_info['message'])
           


# Scheduling daily updates

#schedule.every(2).minutes.do(send_daily_updates)
schedule.every().day.at("10:00").do(send_daily_updates)

# Start polling to receive and handle user messages from bs4 import BeautifulSoup

@bot.message_handler(commands=['track'])
def fetch_project_views(message):
    try:
        # Extract project_id from message
        if len(message.text.split()) >= 2:
            print(message.chat.first_name)
            project_id = message.text.split(' ', 1)[1]
            tracked_projects[project_id] = {"message":message,'chat_id': message.chat.id, 'daily_updates_enabled': False}
            bot.reply_to(message, f"Project {project_id} is now being tracked. Please wait for result.")
            # Fetch total views for project from Giphy API
            url = f"https://giphy.com/gifs/{project_id}"
            options = Options()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--headless=new')
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            driver.implicitly_wait(10)
            
            html=driver.page_source
            driver.close()

            soup = BeautifulSoup(html, 'html.parser')
            views_element = soup.find('div', class_='ViewCountContainer-sc-15ri43l')
            if views_element:
                views = views_element.text
                #Inserting thd datas in mongodb database
                tracked_projects_collection.insert_one({
                    "project_id": project_id,
                    "views": views,
                    "timestamp": time.time()
                })
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


# def get_views() -> int:
#     url = f"https://api.giphy.com/v1/gifs/E1w0yvMxBIv5M8WkL8?api_key={GIPHY_API_KEY}"
#     response = requests.get(url)
#     if response.status_code == 200:
#         data = json.loads(response.text)
#         return data['data']
#     else:
#         return -1
    
# print(get_views())
    
def telegram_polling():
    bot.infinity_polling()


def job():
    print("I'm working...")

    while True:
        schedule.run_pending()
        time.sleep(1)

thread1 = threading.Thread(target=telegram_polling)
thread1.start()

thread2 = threading.Thread(target=job)
thread2.start()
