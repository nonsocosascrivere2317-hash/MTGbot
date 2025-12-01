import requests
import telebot
import time
import json
import os
from bs4 import BeautifulSoup

TOKEN = "8516215785:AAFdYKVp7DyXZTeQ8J7d2RpF_P6bpHbStng"
CHAT_ID = "1589057444"

bot = telebot.TeleBot(TOKEN)

KEYWORDS_FILE = "keywords.json"

# Carica o crea file keywords
def load_keywords():
    if not os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "w") as f:
            json.dump({}, f)
    with open(KEYWORDS_FILE, "r") as f:
        return json.load(f)

def save_keywords(data):
    with open(KEYWORDS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Prende keyword dell’utente
def get_user_keywords(user_id):
    data = load_keywords()
    return data.get(str(user_id), ["magic the gathering mazzo"])

# Setta keyword via comando
@bot.message_handler(commands=['setkeywords'])
def set_keywords(message):
    user_id = message.chat.id
    text = message.text.replace("/setkeywords", "").strip()

    if not text:
        bot.reply_to(message, "❗ Usa il comando così:\n`/setkeywords mazzo commander, mtg deck`", parse_mode="Markdown")
        return

    keywords = [k.strip() for k in text.split(",")]

    data = load_keywords()
    data[str(user_id)] = keywords
    save_keywords(data)

    bot.reply_to(message, f"✅ Keywords aggiornate a:\n\n- " + "\n- ".join(keywords))

# Funzione per controllare vinted
def check_vinted_for_keywords(user_id):
    keywords = get_user_keywords(user_id)
    found_items = []

    for keyword in keywords:
        search_url = "https://www.vinted.it/catalog?search_text=" + keyword.replace(" ", "%20")

        response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        items = soup.find_all("a", class_="feed__item")
        if not items:
            continue

        latest = items[0]
        url = "https://www.vinted.it" + latest.get("href")

        found_items.append((keyword, latest, url))

    return found_items

last_seen = {}

# LOOP principale
def main_loop():
    global last_seen

    while True:
        data = load_keywords()

        for user_id in data.keys():
            items = check_vinted_for_keywords(user_id)

            for keyword, item, url in items:
                if last_seen.get(url) == True:
                    continue

                last_seen[url] = True

                title_el = item.find("h3")
                title = title_el.text.strip() if title_el else "Senza titolo"

                price_el = item.find("span", class_="text-body")
                price = price_el.text.strip() if price_el else "?"

                img_el = item.find("img")
                img = img_el.get("src") if img_el else None

                caption = f"🆕 Nuovo annuncio trovato!\n\n🔍 Keyword: {keyword}\n📦 {title}\n💶 Prezzo: {price}\n🔗 {url}"

                bot.send_photo(int(user_id), img, caption=caption) if img else bot.send_message(int(user_id), caption)

        time.sleep(300)

# Avvia bot + loop
import threading
loop_thread = threading.Thread(target=main_loop)
loop_thread.start()

bot.polling(none_stop=True)
