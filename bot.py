import requests
import telebot
import time
from bs4 import BeautifulSoup

TOKEN = "8516215785:AAFdYKVp7DyXZTeQ8J7d2RpF_P6bpHbStng"
CHAT_ID = "1589057444"

bot = telebot.TeleBot(TOKEN)

SEARCH_URL = "https://www.vinted.it/catalog?search_text=magic%20deck%20commander"

last_seen = None

def check_vinted():
    global last_seen

    response = requests.get(SEARCH_URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")

    items = soup.find_all("a", class_="feed__item")

    if not items:
        return

    latest = items[0]
    url = "https://www.vinted.it" + latest.get("href")

    if url == last_seen:
        return

    last_seen = url

    title_el = latest.find("h3")
    title = title_el.text.strip() if title_el else "Senza titolo"

    price_el = latest.find("span", class_="text-body")
    price = price_el.text.strip() if price_el else "?"

    img_el = latest.find("img")
    img = img_el.get("src") if img_el else None

    message = f"🆕 **Nuovo annuncio Magic trovato!**\n\n📦 *{title}*\n💶 Prezzo: {price}\n🔗 {url}"

    if img:
        bot.send_photo(CHAT_ID, img, caption=message, parse_mode="Markdown")
    else:
        bot.send_message(CHAT_ID, message, parse_mode="Markdown")


# LOOP principale
while True:
    try:
        check_vinted()
        time.sleep(300)  # ogni 5 minuti
    except Exception as e:
        print("Errore:", e)
        time.sleep(60)
