import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import time
import requests
import json
import os
from datetime import datetime, timedelta
import threading
import random
import re
import urllib.parse
from collections import defaultdict
import logging
from dotenv import load_dotenv
from flask import Flask, request

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
OMDB_API_KEY = os.getenv('OMDB_API_KEY')
MDISK_API_KEY = os.getenv('MDISK_API_KEY')
# To store user interaction timestamps and additional user information
user_last_interaction = {}
user_bios = {}  # Store user bios if applicable
DEVELOPER_ID = os.getenv('DEVELOPER_ID')  # Replace with your Telegram user ID
# Dictionary to store bot statistics
bot_stats = defaultdict(int)
# Global cache
cache = defaultdict(lambda: None)
# Track broadcast status
broadcast_status = {}
# Add this with your other global variables
filtered_words = set()
# Add this at the beginning of your script, with your other global variables
recommendation_cache = {}
# Add these new variables
API_REQUEST_COUNT = 0
LAST_RESET_DATE = datetime.now().date()
MAX_DAILY_REQUESTS = 1000
# Create Flask app
app = Flask(__name__)

# Initialize group_ids and channel_ids from environment variables
group_ids = json.loads(os.getenv('GROUP_IDS', '[]'))
channel_ids = json.loads(os.getenv('CHANNEL_IDS', '[]'))

def reset_api_counter():
    global API_REQUEST_COUNT, LAST_RESET_DATE
    current_date = datetime.now().date()
    if current_date > LAST_RESET_DATE:
        API_REQUEST_COUNT = 0
        LAST_RESET_DATE = current_date

def increment_api_counter():
    global API_REQUEST_COUNT
    API_REQUEST_COUNT += 1

def check_api_limit():
    reset_api_counter()  # Ensure the counter is reset if it's a new day
    return API_REQUEST_COUNT < MAX_DAILY_REQUESTS

# Modify your API request functions to use these new functions
def invoke_rest_method(url, params=None):
    if not check_api_limit():
        return {'Response': 'False', 'Error': 'Daily API limit reached. Please try again tomorrow.'}
    
    try:
        response = requests.get(url, params=params, timeout=60)
        increment_api_counter()

        if response.status_code == 200:
            data = response.json()
            if data.get('Response') == 'True':
                return data
            else:
                return data
        else:
            return {'Response': 'False', 'Error': f"HTTP Error: {response.status_code}"}
    except Exception as e:
        return {'Response': 'False', 'Error': str(e)}

# Render API details
RENDER_API_KEY = os.getenv('RENDER_API_KEY')
RENDER_SERVICE_ID = os.getenv('RENDER_SERVICE_ID')
RENDER_API_URL = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/env-vars"

def save_ids():
    global group_ids, channel_ids
    
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    env_vars = [
        {'key': 'GROUP_IDS', 'value': json.dumps(group_ids)},
        {'key': 'CHANNEL_IDS', 'value': json.dumps(channel_ids)}
    ]
    
    for var in env_vars:
        response = requests.post(RENDER_API_URL, headers=headers, json=var)
        if response.status_code != 200:
            print(f"Failed to update {var['key']}: {response.text}")
        else:
            print(f"Successfully updated {var['key']}")
    
    # Update local environment variables
    os.environ['GROUP_IDS'] = json.dumps(group_ids)
    os.environ['CHANNEL_IDS'] = json.dumps(channel_ids)

def load_ids():
    global group_ids, channel_ids
    group_ids = json.loads(os.getenv('GROUP_IDS', '[]'))
    channel_ids = json.loads(os.getenv('CHANNEL_IDS', '[]'))

load_ids()

# Update these functions to use the new save_ids() function
def handle_my_chat_member(message):
    if message.new_chat_member.status in ['member', 'administrator']:
        chat_id = message.chat.id
        chat_type = message.chat.type
        
        if chat_type == 'channel' and chat_id not in channel_ids:
            channel_ids.append(chat_id)
            save_ids()
            print(f"Bot added to channel. Channel ID {chat_id} saved.")
        elif chat_type in ['group','supergroup'] and chat_id not in group_ids:
            group_ids.append(chat_id)
            save_ids()
            print(f"Bot added to group. Group ID {chat_id} saved.")

def handle_new_message(message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    
    if chat_type == 'channel' and chat_id not in channel_ids:
        channel_ids.append(chat_id)
        save_ids()
        print(f"New message from untracked channel. Channel ID {chat_id} saved.")
    elif chat_type in ['group','supergroup'] and chat_id not in group_ids:
        group_ids.append(chat_id)
        save_ids()
        print(f"New message from untracked group. Group ID {chat_id} saved.")
        
def invoke_rest_method(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=60)

        if response.status_code == 200:
            data = response.json()
            if data.get('Response') == 'True':
                return data
            else:
                return data
        else:
            return {'Response': 'False', 'Error': f"HTTP Error: {response.status_code}"}
    except Exception as e:
        return {'Response': 'False', 'Error': str(e)}

cache = {}

def get_cached_data(key, expiry=3600):
    if key in cache:
        data, timestamp = cache[key]
        if time.time() - timestamp < expiry:
            return data
    return None

def set_cached_data(key, data):
    cache[key] = (data, time.time())

def save_filtered_words():
    with open('filtered_words.json', 'w') as f:
        json.dump(list(filtered_words), f)

def load_filtered_words():
    global filtered_words
    try:
        with open('filtered_words.json', 'r') as f:
            filtered_words = set(json.load(f))
    except FileNotFoundError:
        filtered_words = set()

load_filtered_words()

def shorten_url(long_url):
    encoded_url = requests.utils.quote(long_url)
    api_url = f"https://mdiskshortner.link/api?api={MDISK_API_KEY}&url={encoded_url}&format=text"
    
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            short_url = response.text.strip()
            if short_url:
                return short_url
            else:
                print("Received an empty response from API.")
                return long_url
        else:
            print(f"Failed to shorten URL. Status code: {response.status_code}")
            return long_url
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return long_url

def send_message_with_keyboard_removal(chat_id, text, reply_markup=None):
    bot.send_message(chat_id, text, reply_markup=reply_markup)
    if reply_markup is not None:
        # Send a message to remove the keyboard
        bot.send_message(chat_id, " ", reply_markup=types.ReplyKeyboardRemove())

def handle_recommend_command(message):
    if not check_api_limit():
        return bot.reply_to(message, 'My Daily limit reached. Please try again tomorrow.')
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton('Movie'), KeyboardButton('Series'))
    markup.add(KeyboardButton('Cancel'))
    response = bot.send_message(message.chat.id, "Please select whether you want a recommendation for a Movie or a Series:", reply_markup=markup)
    schedule_deletion(message.chat.id, message.message_id, response.message_id)
    bot.register_next_step_handler(message, process_media_type)

def process_genre_selection(message, media_type):
    if message.text.lower() == 'cancel':
        cancel_recommendation(message)
        return

    genre = message.text
    if genre not in ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi', 'Thriller']:
        response = bot.send_message(message.chat.id, "Invalid genre. Please select a valid genre.", reply_markup=ReplyKeyboardRemove())
        schedule_deletion(message.chat.id, message.message_id, response.message_id)
        return
    
    recommendations = get_recommendations_by_genre(genre, media_type)
    if recommendations:
        formatted_recommendations = "\n".join(f"• {rec}" for rec in recommendations)
        response = bot.send_message(message.chat.id, f"Here are some {media_type} recommendations for the {genre} genre:\n\n{formatted_recommendations}", reply_markup=ReplyKeyboardRemove())
    else:
        response = bot.send_message(message.chat.id, f"Sorry, I couldn't find any {media_type} recommendations for the {genre} genre.", reply_markup=ReplyKeyboardRemove())
    
    schedule_deletion(message.chat.id, message.message_id, response.message_id)

def schedule_deletion(chat_id, *message_ids, delay=20):
    threading.Timer(delay, delete_messages, args=[chat_id, *message_ids]).start()

def process_media_type(message):
    if message.text.lower() == 'cancel':
        cancel_recommendation(message)
        return

    media_type = message.text.lower()
    if media_type not in ['movie', 'series']:
        response = bot.send_message(message.chat.id, "Invalid selection. Please use the /recommend command again and select either 'Movie' or 'Series'.", reply_markup=ReplyKeyboardRemove())
        schedule_deletion(message.chat.id, message.message_id, response.message_id)
        return
    
    genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi', 'Thriller']
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(*[KeyboardButton(genre) for genre in genres])
    markup.add(KeyboardButton('Cancel'))
    response = bot.send_message(message.chat.id, f"Great! Now please select a genre for your {media_type} recommendation:", reply_markup=markup)
    schedule_deletion(message.chat.id, message.message_id, response.message_id)
    bot.register_next_step_handler(message, lambda msg: process_genre_selection(msg, media_type))

def cancel_recommendation(message):
    response = bot.send_message(message.chat.id, "Recommendation process cancelled.", reply_markup=ReplyKeyboardRemove())
    schedule_deletion(message.chat.id, message.message_id, response.message_id)

def get_recommendations_by_genre(genre, media_type):
    search_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={genre}&type={media_type}"
    response = requests.get(search_url)
    if response.status_code == 200:
        data = response.json()
        if 'Search' in data:
            titles = [item['Title'] for item in data['Search']]
            random.shuffle(titles)
            return titles[:5]
    return []
    
def get_recommendations(title, media_type):
    cache_key = f"{media_type}:{title}"
    current_time = datetime.now()
    
    # Check if recommendations are in cache and not expired (24 hours)
    if cache_key in recommendation_cache:
        cached_data, timestamp = recommendation_cache[cache_key]
        if current_time - timestamp < timedelta(hours=24):
            return cached_data

    # If not in cache or expired, fetch new recommendations
    if media_type == 'movie':
        data = get_movie_data(title)
    else:
        data = get_series_data(title)
    
    if not data or 'Genre' not in data:
        return []

    genres = data['Genre'].split(', ')
    
    recommendations = set()
    for genre in genres:
        search_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={genre}&type={media_type}'
        response = requests.get(search_url)
        
        if response.status_code == 200:
            search_data = response.json()
            if 'Search' in search_data:
                recommendations.update(item['Title'] for item in search_data['Search'] if item['Title'] != title)
    
    recommendations = list(recommendations)
    random.shuffle(recommendations)
    recommendations = recommendations[:5]

    # Cache the recommendations
    recommendation_cache[cache_key] = (recommendations, current_time)

    return recommendations

def get_movie_data(movie_name):
    cache_key = f"movie:{movie_name}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    response = requests.get(f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={movie_name}', timeout=60)
    if response.status_code == 200:
        data = response.json()
        set_cached_data(cache_key, data)
        return data
    else:
        return None

def get_series_data(series_name):
    cache_key = f"series:{series_name}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    params = {
        'apikey': OMDB_API_KEY,
        't': series_name,
        'type': 'series'
    }
    url = 'http://www.omdbapi.com/'
    
    data = invoke_rest_method(url, params)
    
    if data.get('Response') == 'True':
        set_cached_data(cache_key, data)
    
    return data

def delete_data(chat_id, message_id):
    bot.delete_message(chat_id=chat_id, message_id=message_id)

def handle_help_command(message):
    help_text = (
        "Here are the commands you can use:\n\n"
        "/start - Start the bot and get a welcome message with instructions.\n"
        "/recommend - Get a recommendation for a movie or series based on genre.\n"
        "Movie - Search for a movie by its name.\n"
        "Series - Search for a series by its name.\n"
        "Specific Season - Search for a specific season of a series eg. wednesday season 1.\n"
        "\nUse these commands to explore movies and series. Enjoy!"
    )
    response = bot.send_message(message.chat.id, help_text)
    delete_message_after_delay(message.chat.id, response.message_id)

def handle_start(message):
    try:
        user = message.from_user
        username = user.username
        first_name = user.first_name
        user_id = user.id
        
        mention = f"[{first_name}](tg://user?id={user_id})"
        
        welcome_message = f"Hi {mention}! 🎬🍿 Welcome to MOVIZINFO Bot.\n\nYou can search for any movie by typing movie name.\nor for a series, type series name.\nor for a specific season type series name season seasonnumber \nI'll provide you with detailed information about the movie or series, including a link to its IMDb page. Let's start exploring the world of cinema together! 🌍🎥"

        markup = InlineKeyboardMarkup()
        invite_button = InlineKeyboardButton(text="Add me to your group", url=f"https://t.me/{bot.get_me().username}?startgroup=true")
        
        markup.add(invite_button)
    
        response = bot.send_message(chat_id=message.chat.id, text=welcome_message, parse_mode='Markdown', reply_markup=markup)
        delete_message_after_delay(message.chat.id, response.message_id)
    except Exception as e:
        print(f"Error in handle_start: {e}")

def handle_search_movie_command(message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) > 1:
        movie_name = command_parts[1]
        handle_search_movie(message, movie_name)
    else:
        bot.reply_to(message, 'Please provide a movie name with the /searchmovie command.')

def handle_search_series_command(message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) > 1:
        series_name = command_parts[1]
        handle_search_series(message, series_name)
    else:
        bot.reply_to(message, 'Please provide a series name with the /searchseries command.')

def handle_search_season_command(message):
    command_parts = message.text.split()[1:]  # Remove the command itself
    if len(command_parts) >= 2:
        season_number = command_parts[-1]  # Last part should be the season number
        series_name = " ".join(command_parts[:-1])  # Join all parts except the last one for the series name
        if season_number.isdigit():
            handle_search_season(message, series_name, season_number)
        else:
            bot.reply_to(message, 'Please provide a valid season number.')
    else:
        bot.reply_to(message, 'Please use the format: /searchseason <series name> <season number>')

def handle_search_season(message, series_name, season_number):
    if not check_api_limit():
        return bot.reply_to(message, 'My Daily limit reached. Please try again tomorrow.')
    series_data = get_series_data(series_name)
    if series_data and series_data.get('Response') == 'True':
        season_data = get_season_data(series_data['imdbID'], season_number)
        if season_data and season_data.get('Response') == 'True':
            formatted_data = format_season_data(series_data, season_data, season_number)
            return bot.send_message(message.chat.id, formatted_data, parse_mode='HTML')
    return None

def format_season_data(series_data, season_data, season_number):
    formatted_data = f"<b>{series_data['Title']} - Season {season_number}</b>\n\n"
    formatted_data += f"Total Episodes: {len(season_data['Episodes'])}\n\n"

    for episode in season_data['Episodes']:
        formatted_data += f"Episode {episode['Episode']}: {episode['Title']} - Rating: {episode['imdbRating']}\n"

    # Add a link to watch the season if available
    season_link = shorten_url(f"https://www.youtube.com/results?search_query={series_data['Title'].replace(' ', '+')}+season+{season_number}")
    formatted_data += f"\n<b>Watch Season:</b> <a href='{season_link}'>Search for Season {season_number}</a>"

    return formatted_data

def process_season_data(message, series_data, season_data, season_number):
    # Format and send the season information
    formatted_data = f"*{series_data['Title']} - Season {season_number}*\n\n"
    formatted_data += f"Total Episodes: {len(season_data['Episodes'])}\n\n"

    for episode in season_data['Episodes']:
        formatted_data += f"Episode {episode['Episode']}: {episode['Title']} - Rating: {episode['imdbRating']}\n"

    return formatted_data

def get_season_data(imdb_id, season_number):
    cache_key = f"season:{imdb_id}:{season_number}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    params = {
        'apikey': OMDB_API_KEY,
        'i': imdb_id,
        'Season': season_number
    }
    url = 'http://www.omdbapi.com/'
    
    data = invoke_rest_method(url, params)
    
    if data.get('Response') == 'True':
        set_cached_data(cache_key, data)
    
    return data

def handle_search_movie(message, movie_name=None):
    if not check_api_limit():
        return bot.reply_to(message, 'My Daily limit reached. Please try again tomorrow.')
    if not movie_name:
        movie_name = message.text
    movie_data = get_movie_data(movie_name)
    if movie_data and 'Error' not in movie_data:
        # Start with the poster URL
        formatted_movie_data = ''
        if movie_data.get("Poster") and movie_data["Poster"] != "N/A":
            formatted_movie_data = f'<a href="{movie_data["Poster"]}">&#8205;</a>'
        
        # Add the movie information
        keys = ['Title', 'Year', 'Rated', 'Released', 'Runtime', 'Genre', 'Director', 'Writer', 'Actors', 'Language',
                'Country', 'Awards', 'imdbRating']
        formatted_movie_data += '\n\n' + '\n'.join(f'<b>{k}</b>: {movie_data.get(k, "N/A")}' for k in keys)
        
        trailer_link = shorten_url(f"https://www.youtube.com/results?search_query={movie_name.replace(' ', '+')}+trailer")
        formatted_movie_data += f'\n\n<b>Trailer:</b> <a href="{trailer_link}">Watch Trailer</a>'
        movie_link = shorten_url(f"https://www.youtube.com/results?search_query={movie_name.replace(' ', '+')}+full movie")
        formatted_movie_data += f'\n\n<b>Movie:</b> <a href="{movie_link}">Watch Movie (if available)</a>'
        imdb_link = shorten_url(f"http://www.movieclue.rf.gd/movie_detail.html?imdbID={movie_data['imdbID']}")
        formatted_movie_data += f'\n\n<a href="{imdb_link}">More Information</a>'
        
        # Add recommendations
        recommendations = get_recommendations(movie_name, 'movie')
        if recommendations:
            formatted_movie_data += "\n\n<b>Recommendations:</b>\n" + "\n".join(recommendations)
        
        # Send the message
        return bot.send_message(chat_id=message.chat.id, text=formatted_movie_data, parse_mode='HTML')
    else:
        response = bot.reply_to(message, 'Please provide a movie name after the /searchmovie command.\nFor example: /searchmovie Inception')
        schedule_deletion(message.chat.id, message.message_id, response.message_id)

def handle_search_series(message, series_name=None):
    if not check_api_limit():
        return bot.reply_to(message, 'My Daily limit reached. Please try again tomorrow.')
    if not series_name:
        series_name = message.text
    series_data = get_series_data(series_name)
    if series_data and 'Error' not in series_data:
        # Start with the poster URL
        formatted_series_data = ''
        if series_data.get("Poster") and series_data["Poster"] != "N/A":
            formatted_series_data = f'<a href="{series_data["Poster"]}">&#8205;</a>'
        
        # Add the series information
        keys = ['Title', 'Year', 'Rated', 'Released', 'Runtime', 'Genre', 'Director', 'Writer', 'Actors', 'Language',
                'Country', 'Awards', 'imdbRating']
        formatted_series_data += '\n\n' + '\n'.join(f'<b>{k}</b>: {series_data.get(k, "N/A")}' for k in keys)
        
        trailer_link = shorten_url(f"https://www.youtube.com/results?search_query={series_name.replace(' ', '+')}+trailer")
        formatted_series_data += f'\n\n<b>Trailer:</b> <a href="{trailer_link}">Watch Trailer</a>'
        series_link = shorten_url(f"https://www.youtube.com/results?search_query={series_name.replace(' ', '+')}+full series")
        formatted_series_data += f'\n\n<b>Series:</b> <a href="{series_link}">Watch Series (if available)</a>'
        imdb_link = shorten_url(f'https://www.imdb.com/title/{series_data["imdbID"]}/')
        formatted_series_data += f'\n\n<a href="{imdb_link}">More Information</a>'
        
        # Add recommendations
        recommendations = get_recommendations(series_name, 'series')
        if recommendations:
            formatted_series_data += "\n\n<b>Recommendations:</b>\n" + "\n".join(recommendations)
        
        # Send the message
        return bot.send_message(chat_id=message.chat.id, text=formatted_series_data, parse_mode='HTML')
    return None
    
        
def handle_search_movie_or_series(message):
    search_query = message.text.strip()
    print(f"Searching for: {search_query}")
    
    try:
        if not handle_search_movie(message, search_query):
            if not handle_search_series(message, search_query):
                bot.reply_to(message, f"Sorry, I couldn't find any information about '{search_query}'.")
    except Exception as e:
        print(f"Error in handle_search_movie_or_series: {e}")
        bot.reply_to(message, "An error occurred while processing your request. Please try again later.")

def handle_filter_command(message):
    # Split the message text to get the filter criteria
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide filter criteria after the command.")
        return

    criteria = command_parts[1].strip()
    
    # Store the filter criteria
    filtered_words.add(criteria)
    save_filtered_words()
    
    bot.reply_to(message, f"Filter criteria '{criteria}' has been added.")

  # This handler will process all incoming messages
def filter_messages(message):
    if not filtered_words:
        return

    # Check if the message text contains any of the filtered words
    message_text = message.text.lower()
    for word in filtered_words:
        if word.lower() in message_text:
            # Send notification message
            sent_message = bot.send_message(message.chat.id, f"Your message containing '{word}' has been deleted.")
            
            # Delete the original message
            bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            
            # Wait for a specific period (e.g., 10 seconds) before deleting the notification message
            time.sleep(5)
            bot.delete_message(chat_id=message.chat.id, message_id=sent_message.message_id)
            return



def handle_devinfo_command(message):
    user_id = message.from_user.id
    if user_id != int(DEVELOPER_ID):
        bot.reply_to(message, "Access denied. This command is for developers only.")
        return
    try:
        dev_info = (
            "🔧 *Developer Information* 🔧\n\n"
            f"**Developer ID:** `{DEVELOPER_ID}`\n"
            f"**Current Time:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"**Bot Status:** `Operational`\n"
            f"**Total Users:** `{len(user_last_interaction)}`\n"
            f"**Cached Items:** `{len(cache)}`\n"
        )
        response = bot.send_message(message.chat.id, dev_info, parse_mode='Markdown')
        delete_message_after_delay(message.chat.id, response.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, "An error occurred while processing the command.")

def handle_clear_cache_command(message):
    user_id= message.from_user.id
    if user_id != int(DEVELOPER_ID):
        bot.reply_to(message, "Access denied. This command is for developers only.")
        return
    
    global cache
    cache.clear()
    response = bot.send_message(message.chat.id, "Cache cleared")
    delete_message_after_delay(message.chat.id, response.message_id)
    

def handle_stats_command(message):
    user_id= message.from_user.id
    if user_id != int(DEVELOPER_ID):
        bot.reply_to(message, "Access denied. This command is for developers only.")
        return

    stats_message = (
        "📊 *Bot Statistics* 📊\n\n"
        f"**Messages Received:** `{bot_stats['messages_received']}`\n"
        f"**Active Users:** `{len(user_last_interaction)}`\n"
        f"**Errors Encountered:** `{bot_stats['errors']}`\n"
    )

    response = bot.send_message(message.chat.id, stats_message, parse_mode='Markdown')
    delete_message_after_delay(message.chat.id, response.message_id)

def handle_reload_command(message):
    user_id= message.from_user.id
    if user_id == int(DEVELOPER_ID):
        bot.reply_to(message, "Bot is reloading...")
        # Add your reload logic here
    else:
        bot.reply_to(message, "Access denied. You are not authorized to use this command.")

def handle_broadcast(message):
    user_id= message.from_user.id
    if user_id == int(DEVELOPER_ID):
        bot.send_message(message.chat.id, "Please send the message you want to broadcast.")
        bot.register_next_step_handler(message, handle_broadcast_message)
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

def process_broadcast_message(message):
    broadcast_message = message.text
    global group_ids  # Declare group_ids as global
    try:
        bot.send_message(group_ids, broadcast_message)
    except Exception as e:
        print(f"An error occurred: {e}")

def handle_broadcast_status(message):
    user_id = message.from_user.id
    if user_id == int(DEVELOPER_ID):
        status_message = "Tracked channels:\n"
        status_message += "\n".join([str(ch_id) for ch_id in channel_ids])
        status_message += "\n\nTracked groups:\n"
        status_message += "\n".join([str(gr_id) for gr_id in group_ids])
        
        if not channel_ids and not group_ids:
            status_message = "No channels or groups are currently being tracked."
        
        bot.reply_to(message, status_message)
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

def handle_broadcast_message(message):
    user_id = message.from_user.id
    if user_id != int(DEVELOPER_ID):
        bot.reply_to(message, "Access denied. This command is for developers only.")
        return

    broadcast_message = message.text
    broadcast_status[message.from_user.id] = 'broadcasting'
    
    # Broadcast to all users
    for user_id in user_last_interaction.keys():
        try:
            bot.send_message(user_id, broadcast_message)
        except Exception as e:
            print(f"Error sending message to user {user_id}: {e}")

    # Broadcast to all channels and groups
    for chat_id in channel_ids + group_ids:
        try:
            bot.send_message(chat_id, broadcast_message)
        except Exception as e:
            print(f"Error sending message to chat {chat_id}: {e}")

    bot.send_message(message.chat.id, "Broadcasting message to all users, channels, and groups.")
    bot.send_message(message.chat.id, f"Message sent: {broadcast_message}")

    # Clear the status
    del broadcast_status[message.from_user.id]

def handle_id_command(message):
    user_id = message.from_user.id
    response = bot.send_message(message.chat.id, f"Your user ID is: {user_id}")
    delete_message_after_delay(message.chat.id, response.message_id)

def handle_info_command(message):
    user = message.from_user
    chat_id = message.chat.id

    first_name = user.first_name or "N/A"
    last_name = user.last_name or "N/A"
    username = user.username or "N/A"
    user_id = user.id
    language_code = user.language_code or "N/A"

    # Format the message with improved UI/UX
    info_message = (
        "🌟 *User Profile Information* 🌟\n\n"
        f"**First Name:** `{first_name}`\n"
        f"**Last Name:** `{last_name}`\n"
        f"**Username:** `@{username}`\n"
        f"**User ID:** `{user_id}`\n"
        f"**Language Code:** `{language_code}`\n\n"
    )

    # Send the user information with styling
    response = bot.send_message(chat_id, info_message, parse_mode='Markdown')
    delete_message_after_delay(message.chat.id, response.message_id)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Update user interaction timestamp
    user_id = message.from_user.id
    user_last_interaction[user_id] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Check if the message is a command
    if message.text.startswith('/'):
        # Handle commands as before
        if '/help' in message.text:
            response = handle_help_command(message)
        elif '/recommend' in message.text:
            response = handle_recommend_command(message)
        elif '/start' in message.text:
            response = handle_start(message)
        elif '/devinfo' in message.text:
            response = handle_devinfo_command(message)
        elif '/filter' in message.text:
            response = handle_filter_command(message)
        elif '/clearcache' in message.text:
            response = handle_clear_cache_command(message)
        elif '/stats' in message.text:
            response = handle_stats_command(message)
        elif '/reload' in message.text:
            response = handle_reload_command(message)
        elif '/broadcast' in message.text:
            response = handle_broadcast(message)
        elif '/broadcast_status' in message.text:
            response = handle_broadcast_status(message)
        elif '/id' in message.text:
            response = handle_id_command(message)
        elif '/info' in message.text:
            response = handle_info_command(message)
        else:
            response = bot.reply_to(message, 'Unknown command. Please use /help to see available commands.')
    else:
        # If not a command, treat as a search query
        search_query = message.text.strip()

        # Try to detect if it's a season search
        season_match = re.match(r'(.*?)\s+season\s+(\d+)', search_query, re.IGNORECASE)
        if season_match:
            series_name = season_match.group(1)
            season_number = season_match.group(2)
            response = handle_search_season(message, series_name, season_number)
        else:
            # Try movie search first, then series
            response = handle_search_movie(message, search_query)
            if not response:
                response = handle_search_series(message, search_query)
        
        if not response:
            response = bot.reply_to(message, f"Sorry, I couldn't find any information about '{search_query}'.")

    # Delete both the user's message and the bot's response after a short delay
    if response:
        threading.Timer(80.0, delete_messages, args=[message.chat.id, message.message_id, response.message_id]).start()
    else:
        # If no response was sent (unlikely, but possible), just delete the user's message
        threading.Timer(80.0, delete_messages, args=[message.chat.id, message.message_id]).start()

def delete_messages(chat_id, *message_ids):
    for msg_id in message_ids:
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception as e:
            print(f"Error deleting message {msg_id}: {e}")

def delete_message_after_delay(chat_id, message_id, delay=60):
    def delete():
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"Error deleting message {message_id}: {e}")

    threading.Timer(delay, delete).start()

# Update this function to manage user interaction timestamps
#@bot.message_handler(func=lambda message: True)
#def update_user_info(message):
#    user_id = message.from_user.id
    # Track the last interaction
#    user_last_interaction[user_id] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Add this new route for the webhook
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/')
def home():
    return 'Bot is running!'

if __name__ == '__main__':
    if os.environ.get('ENVIRONMENT') == 'production':
        webhook_url = os.environ.get('WEBHOOK_URL')
        if webhook_url:
            full_webhook_url = webhook_url + BOT_TOKEN
            print(f"Setting webhook to: {full_webhook_url}")
            bot.remove_webhook()
            bot.set_webhook(url=full_webhook_url)
            app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
        else:
            print("WEBHOOK_URL is not set. Please set it in your Render environment variables.")
    else:
        bot.remove_webhook()
        bot.polling(none_stop=True)
