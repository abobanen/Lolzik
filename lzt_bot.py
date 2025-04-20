
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import time

def parse_lzt_market(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    items_data = []

    items = soup.find_all("div", class_="market__product market__product--grid")
    for item in items:
        title_div = item.find("div", class_="market__product-title")
        price_div = item.find("div", class_="market__product-price")
        link_tag = item.find("a", class_="market__product-link")

        if title_div and price_div and link_tag:
            title = title_div.text.strip()
            price = price_div.text.strip().replace("₽", "").replace(" ", "").replace("\xa0", "")
            link = "https://lzt.market" + link_tag["href"]

            items_data.append({
                "title": title,
                "price": int(price),
                "link": link
            })

    return items_data

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на поиск lzt.market через /track <ссылка>, и я буду следить за новыми товарами и снижением цен в течение часа.")

async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй команду так: /track <ссылка>")
        return

    url = context.args[0]
    if not url.startswith("https://lzt.market/"):
        await update.message.reply_text("Ссылка должна начинаться с https://lzt.market/")
        return

    await update.message.reply_text(f"Отслеживаю: {url} — 1 час. Уведомлю о новых товарах и снижениях цен.")

    known_items = {}
    start_time = time.time()

    while time.time() - start_time < 3600:
        try:
            current_items = parse_lzt_market(url)
            for item in current_items:
                item_id = item["link"]

                if item_id not in known_items:
                    known_items[item_id] = item["price"]
                    await update.message.reply_text(
                        f"**[НОВЫЙ ТОВАР]**\n{item['title']}\nЦена: {item['price']}₽\n{item['link']}",
                        parse_mode="Markdown"
                    )
                elif item["price"] < known_items[item_id]:
                    old_price = known_items[item_id]
                    known_items[item_id] = item["price"]
                    await update.message.reply_text(
                        f"**[СНИЖЕНИЕ ЦЕНЫ]**\n{item['title']}\nБыло: {old_price}₽\nСтало: {item['price']}₽\n{item['link']}",
                        parse_mode="Markdown"
                    )
        except Exception as e:
            await update.message.reply_text(f"Ошибка при парсинге: {e}")
        
        await asyncio.sleep(60)

    await update.message.reply_text("Отслеживание завершено. Прошёл 1 час.")

if __name__ == "__main__":
    app = ApplicationBuilder().token("7747932663:AAGjBtgIp9di9aLZ09bk8-Gm5k802RfozCs").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track", track))

    print("Бот запущен.")
    app.run_polling()
