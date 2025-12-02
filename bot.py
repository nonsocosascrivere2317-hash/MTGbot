import os
import json
import requests
import time
import threading
import telebot
from telebot import types

TOKEN = "8516215785:AAFdYKVp7DyXZTeQ8J7d2RpF_P6bpHbStng"
bot = telebot.TeleBot(TOKEN)

KEYWORDS_FILE = "keywords.json"
SEEN_FILE = "seen.json"  # per tenere traccia degli annunci già notificati

# CREA FILES SE NON ESISTONO
if not os.path.exists(KEYWORDS_FILE):
    with open(KEYWORDS_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "w") as f:
        json.dump({}, f)


# ---------------------------------------------------------
# FUNZIONI DI UTILITÀ
# ---------------------------------------------------------

def load_keywords():
    with open(KEYWORDS_FILE, "r") as f:
        return json.load(f)

def save_keywords(data):
    with open(KEYWORDS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_seen():
    with open(SEEN_FILE, "r") as f:
        return json.load(f)

def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=4)

def send_telegram_message(user_id, text):
    bot.send_message(user_id, text)


# ---------------------------------------------------------
# BOT COMMANDS
# ---------------------------------------------------------

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Ciao! Sono il bot che traccia annunci su Vinted.\nUsa /setkeywords per aggiungere parole chiave.")

@bot.message_handler(commands=['setkeywords'])
def set_keywords(message):
    bot.reply_to(message, "Perfetto! Scrivimi ora la parola chiave che vuoi aggiungere.")
    bot.register_next_step_handler(message, add_keyword)

def add_keyword(message):
    kw = message.text.strip().lower()
    data = load_keywords()
    uid = str(message.from_user.id)

    if uid not in data:
        data[uid] = []

    if kw in data[uid]:
        bot.reply_to(message, f"La keyword '{kw}' è già presente!")
    else:
        data[uid].append(kw)
        save_keywords(data)
        bot.reply_to(message, f"Keyword aggiunta: {kw}")

@bot.message_handler(commands=['getkeywords'])
def get_keywords(message):
    data = load_keywords()
    uid = str(message.from_user.id)

    if uid not in data or len(data[uid]) == 0:
        bot.reply_to(message, "Non hai ancora parole chiave. Usa /setkeywords.")
    else:
        lista = "\n - ".join(data[uid])
        bot.reply_to(message, f"Le tue keyword attuali sono:\n - {lista}")

@bot.message_handler(commands=['deletekeywords'])
def delete_keywords(message):
    data = load_keywords()
    uid = str(message.from_user.id)

    if uid in data:
        data[uid] = []
        save_keywords(data)
        bot.reply_to(message, "Tutte le tue keyword sono state eliminate!")
    else:
        bot.reply_to(message, "Non avevi keyword salvate.")

# Messaggi normali
@bot.message_handler(func=lambda m: True)
def check_keywords(message):
    data = load_keywords()
    uid = str(message.from_user.id)

    if uid not in data:
        return

    text = message.text.lower()
    for kw in data[uid]:
        if kw in text:
            bot.reply_to(message, f"Ho trovato la parola chiave '{kw}' nel tuo messaggio!")
            break


# ---------------------------------------------------------
# MONITORAGGIO VINTED AUTOMATICO
# ---------------------------------------------------------

API_URL = "https://www.vinted.it/api/v2/items"

def search_vinted_loop():
    bot.send_message(OWNER_ID, "🔍 Avvio monitoraggio Vinted...")  # opzionale

    while True:
        keywords = load_keywords()
        seen = load_seen()

        # evita crash se file è vuoto
        if not isinstance(seen, dict):
            seen = {}

        try:
            response = requests.get(API_URL, params={"order": "newest_first", "per_page": 20})
            items = response.json().get("items", [])
        except Exception as e:
            print("Errore Vinted:", e)
            time.sleep(30)
            continue

        for user_id, user_keywords in keywords.items():

            if user_id not in seen:
                seen[user_id] = []

            for item in items:
                title = item["title"].lower()
                item_id = str(item["id"])

                # controlla se la keyword appare nel titolo
                if any(kw.lower() in title for kw in user_keywords):

                    # non notificare due volte
                    if item_id not in seen[user_id]:
                        seen[user_id].append(item_id)
                        save_seen(seen)

                        link = f"https://www.vinted.it/items/{item_id}"
                        price = item["price"]
                        brand = item.get("brand_title", "N/D")

                        msg = (
                            f"🆕 *Nuovo annuncio trovato!*\n\n"
                            f"📌 *Titolo:* {item['title']}\n"
                            f"🏷 *Brand:* {brand}\n"
                            f"💶 *Prezzo:* {price}€\n"
                            f"🔗 {link}"
                        )

                        bot.send_message(user_id, msg, parse_mode="Markdown")

        time.sleep(20)  # intervallo tra i controlli


# THREAD PER MONITORARE SENZA BLOCCARE IL BOT
thread = threading.Thread(target=search_vinted_loop, daemon=True)
thread.start()

# ---------------------------------------------------------
# AVVIO BOT
# ---------------------------------------------------------

bot.infinity_polling()