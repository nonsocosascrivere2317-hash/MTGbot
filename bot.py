import os
import json
import requests
import time
import threading
import telebot
from telebot import types

TOKEN = "8516215785:AAFdYKVp7DyXZTeQ8J7d2RpF_P6bpHbStng"
bot = telebot.TeleBot(TOKEN)
OWNER_ID = 1589057444

KEYWORDS_FILE = "keywords.json"
SEEN_FILE = "seen.json"

# CREA I FILE SE NON ESISTONO
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


# ---------------------------------------------------------
# MONITORAGGIO VINTED AUTOMATICO
# ---------------------------------------------------------

VINTED_URL = "https://www.vinted.it/api/v2/catalog/items"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "it-IT,it;q=0.9"
}

def search_vinted_loop():
    bot.send_message(OWNER_ID, "🔍 Avvio monitoraggio Vinted...")

    while True:
        keywords = load_keywords()
        seen = load_seen()

        if not isinstance(seen, dict):
            seen = {}

        try:
            params = {
                "order": "newest_first",
                "per_page": 20
            }

            response = requests.get(VINTED_URL, headers=HEADERS, params=params)

            # Se la risposta non è valida → evita crash
            if response.status_code != 200:
                print("STATUS:", response.status_code)
                print("RISPOSTA:", response.text[:500])
                time.sleep(30)
                continue

            try:
                data = response.json()
                items = data.get("items", [])
            except Exception as e:
                print("ERRORE JSON:", e)
                print("RISPOSTA GREZZA:", response.text[:500])
                time.sleep(30)
                continue

        except Exception as e:
            print("Errore Vinted:", e)
            time.sleep(30)
            continue

        # ----------------------------------------------------
        # CHECK ANNUNCI
        # ----------------------------------------------------
        for user_id, user_keywords in keywords.items():

            if user_id not in seen:
                seen[user_id] = []

            for item in items:
                title = item["title"].lower()
                item_id = str(item["id"])

                # Trova keyword nel titolo
                if any(kw.lower() in title for kw in user_keywords):

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