import os
import json
import requests
import time
import threading
import telebot

TOKEN = "8516215785:AAFdYKVp7DyXZTeQ8J7d2RpF_P6bpHbStng"
bot = telebot.TeleBot(TOKEN)

OWNER_ID = 1589057444

KEYWORDS_FILE = "keywords.json"
SEEN_FILE = "seen.json"

# -----------------------------
# CREAZIONE FILE
# -----------------------------
if not os.path.exists(KEYWORDS_FILE):
    with open(KEYWORDS_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "w") as f:
        json.dump({}, f)


# -----------------------------
# FUNZIONI UTILI
# -----------------------------
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


# -----------------------------
# BOT COMMANDS
# -----------------------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Ciao! Usa /setkeywords per aggiungere parole chiave da monitorare su Vinted.")

@bot.message_handler(commands=['setkeywords'])
def set_keywords(message):
    bot.reply_to(message, "Scrivi ora la parola chiave che vuoi aggiungere:")
    bot.register_next_step_handler(message, add_keyword)

def add_keyword(message):
    kw = message.text.strip().lower()
    data = load_keywords()
    uid = str(message.from_user.id)

    if uid not in data:
        data[uid] = []

    if kw in data[uid]:
        bot.reply_to(message, f"La keyword '{kw}' è già presente.")
    else:
        data[uid].append(kw)
        save_keywords(data)
        bot.reply_to(message, f"Keyword aggiunta: {kw}")

@bot.message_handler(commands=['getkeywords'])
def get_keywords(message):
    data = load_keywords()
    uid = str(message.from_user.id)

    if uid not in data or len(data[uid]) == 0:
        bot.reply_to(message, "Non hai parole chiave salvate.")
    else:
        lista = "\n - ".join(data[uid])
        bot.reply_to(message, f"Le tue keyword:\n{lista}")

@bot.message_handler(commands=['deletekeywords'])
def delete_keywords(message):
    data = load_keywords()
    uid = str(message.from_user.id)
    data[uid] = []
    save_keywords(data)
    bot.reply_to(message, "Tutte le keyword sono state eliminate.")


# -----------------------------
# 🔍 VINTED SCRAPER FUNZIONANTE
# -----------------------------

SEARCH_URL = "https://www.vinted.it/api/items"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def get_vinted_items(keyword):
     # Parametri da inviare con la richiesta
    params = {
        "search_text": keyword,
        "page": 1,
        "per_page": 20,
        "order": "newest_first"
    }

    # Stampa i parametri per vedere cosa stai inviando all'API
    print("Richiesta a Vinted con i seguenti parametri:", params)

    # Effettua la richiesta GET all'API di Vinted
    r = requests.get(SEARCH_URL, headers=HEADERS, params=params)
    
    # Controlla se la risposta ha uno status diverso da 200 (successo)
    if r.status_code != 200:
        print(f"Errore! Status code: {r.status_code}")
        print(f"Risposta: {r.text[:200]}")  # Mostra solo i primi 200 caratteri della risposta
        return None
    
    # Cerca di fare il parsing della risposta JSON
    try:
        j = r.json()
        return j.get("items", [])  # Ritorna gli articoli trovati
    except Exception as e:
        print(f"Errore durante il parsing della risposta JSON: {e}")
        return None


# -----------------------------
# 🔁 CICLO DI MONITORAGGIO
# -----------------------------
def search_vinted_loop():
    bot.send_message(OWNER_ID, "🔍 Monitoraggio attivo...")

    while True:
        keywords = load_keywords()
        seen = load_seen()

        for user_id, kws in keywords.items():

            if user_id not in seen:
                seen[user_id] = []

            for kw in kws:
                items = get_vinted_items(kw)
                if not items:
                    continue

                for item in items:
                    item_id = str(item["id"])
                    title = item["title"]

                    if item_id in seen[user_id]:
                        continue

                    seen[user_id].append(item_id)
                    save_seen(seen)

                    link = f"https://www.vinted.it/items/{item_id}"

                    msg = (
                        f"🆕 *Nuovo annuncio trovato!*\n"
                        f"🔎 Keyword: *{kw}*\n\n"
                        f"📌 *Titolo:* {title}\n"
                        f"💶 Prezzo: {item['price']}€\n"
                        f"🔗 {link}"
                    )

                    bot.send_message(user_id, msg, parse_mode="Markdown")

        time.sleep(25)


# -----------------------------
# THREAD MONITOR
# -----------------------------
thread = threading.Thread(target=search_vinted_loop, daemon=True)
thread.start()


# -----------------------------
# START BOT
# -----------------------------
bot.infinity_polling()
