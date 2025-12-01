import os
import json
import telebot
from telebot import types

TOKEN = "8516215785:AAFdYKVp7DyXZTeQ8J7d2RpF_P6bpHbStng"
bot = telebot.TeleBot(TOKEN)
KEYWORDS_FILE = "keywords.json"

# Carica o crea il file keywords
if not os.path.exists(KEYWORDS_FILE):
    with open(KEYWORDS_FILE, "w") as f:
        json.dump({}, f)

# Funzioni utili

def load_keywords():
    with open(KEYWORDS_FILE, "r") as f:
        return json.load(f)

def save_keywords(data):
    with open(KEYWORDS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Comando /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Ciao! Sono il bot per tracciare parole chiave dei mazzi Magic su Vinted!\nUsa /setkeywords per aggiungerne.")

# Comando /setkeywords
@bot.message_handler(commands=['setkeywords'])
def set_keywords(message):
    bot.reply_to(message, "Perfetto! Scrivimi ora la parola chiave che vuoi aggiungere.")
    bot.register_next_step_handler(message, add_keyword)

# Aggiunge una keyword

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

# Comando /getkeywords
@bot.message_handler(commands=['getkeywords'])
def get_keywords(message):
    data = load_keywords()
    uid = str(message.from_user.id)

    if uid not in data or len(data[uid]) == 0:
        bot.reply_to(message, "Non hai ancora parole chiave. Usa /setkeywords.")
    else:
        lista = "\n - ".join(data[uid])
        bot.reply_to(message, f"Le tue keyword attuali sono:\n - {lista}")

# Comando /deletekeywords
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

# Risposta se un messaggio contiene una keyword
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

# Avvio bot (polling)
bot.infinity_polling()
