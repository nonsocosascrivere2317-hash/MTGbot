TOKEN = "8516215785:AAFdYKVp7DyXZTeQ8J7d2RpF_P6bpHbStng"
CHAT_ID = "1589057444"
bot = telebot.TeleBot(TOKEN)

KEYWORDS_FILE = "keywords.json"

# ----------------------------
# 🔧  Gestione Keywords
# ----------------------------

def load_keywords():
    if not os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "w") as f:
            json.dump({}, f)
    with open(KEYWORDS_FILE, "r") as f:
        return json.load(f)

def save_keywords(data):
    with open(KEYWORDS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user_keywords(user_id):
    data = load_keywords()
    return data.get(str(user_id), ["magic the gathering mazzo"])

def set_user_keywords(user_id, keywords):
    data = load_keywords()
    data[str(user_id)] = keywords
    save_keywords(data)

def add_keyword(user_id, keyword):
    kw = get_user_keywords(user_id)
    if keyword not in kw:
        kw.append(keyword)
    set_user_keywords(user_id, kw)

def del_keyword(user_id, keyword):
    kw = get_user_keywords(user_id)
    if keyword in kw:
        kw.remove(keyword)
    set_user_keywords(user_id, kw)


# ----------------------------
# 📌  Comandi Telegram
# ----------------------------

@bot.message_handler(commands=['setkeywords'])
def set_keywords(message):
    text = message.text.replace("/setkeywords", "").strip()
    if not text:
        bot.reply_to(message, "Usa: `/setkeywords keyword1, keyword2`", parse_mode="Markdown")
        return

    keywords = [k.strip() for k in text.split(",")]
    set_user_keywords(message.chat.id, keywords)

    bot.reply_to(message, "✅ Keywords aggiornate a:\n\n" + "\n".join("- " + k for k in keywords))


@bot.message_handler(commands=['getkeywords'])
def get_keywords(message):
    keywords = get_user_keywords(message.chat.id)
    bot.reply_to(message, "📜 *Keywords attuali:*\n\n" + "\n".join("- " + k for k in keywords), parse_mode="Markdown")


@bot.message_handler(commands=['addkeyword'])
def add_keyword_cmd(message):
    text = message.text.replace("/addkeyword", "").strip()
    if not text:
        bot.reply_to(message, "Usa: `/addkeyword nuova_keyword`", parse_mode="Markdown")
        return

    add_keyword(message.chat.id, text)
    bot.reply_to(message, f"➕ Aggiunta keyword: **{text}**", parse_mode="Markdown")


@bot.message_handler(commands=['delkeywords'])
def del_keyword_cmd(message):
    text = message.text.replace("/delkeywords", "").strip()
    if not text:
        bot.reply_to(message, "Usa: `/delkeywords keyword_da_rimuovere`", parse_mode="Markdown")
        return

    del_keyword(message.chat.id, text)
    bot.reply_to(message, f"❌ Rimossa keyword: **{text}**", parse_mode="Markdown")


@bot.message_handler(commands=['clearkeywords'])
def clear_keywords(message):
    set_user_keywords(message.chat.id, [])
    bot.reply_to(message, "🗑️ Tutte le keyword sono state eliminate.")


# ----------------------------
# 🔍  Controllo Vinted
# ----------------------------

def search_vinted(keyword):
    url = "https://www.vinted.it/catalog?search_text=" + keyword.replace(" ", "%20")
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")

    items = soup.find_all("a", class_="feed__item")
    if not items:
        return None

    return items[0]


last_seen = {}

def main_loop():
    global last_seen

    while True:
        data = load_keywords()

        for user_id, keywords in data.items():
            if not keywords:
                continue

            for keyword in keywords:
                item = search_vinted(keyword)
                if not item:
                    continue

                item_url = "https://www.vinted.it" + item.get("href")

                if last_seen.get(item_url):
                    continue

                last_seen[item_url] = True

                title_el = item.find("h3")
                title = title_el.text.strip() if title_el else "Senza titolo"

                price_el = item.find("span", class_="text-body")
                price = price_el.text.strip() if price_el else "?"

                img_el = item.find("img")
                img = img_el.get("src") if img_el else None

                caption = f"🆕 Nuovo annuncio trovato!\n\n🔍 Keyword: {keyword}\n📦 {title}\n💶 Prezzo: {price}\n🔗 {item_url}"

                bot.send_photo(int(user_id), img, caption=caption) if img else bot.send_message(int(user_id), caption)

        time.sleep(300)


# ----------------------------
# 🚀 Avvio bot
# ----------------------------

import threading
threading.Thread(target=main_loop).start()

bot.polling(none_stop=True)
