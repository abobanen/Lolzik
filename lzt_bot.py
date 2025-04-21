import asyncio
import logging
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
from bs4 import BeautifulSoup

TOKEN = "7747932663:AAGjBtgIp9di9aLZ09bk8-Gm5k802RfozCs"
user_tasks = {}

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне ссылку на товар с lzt.market, и я буду следить за ним 1 час.")

async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = " ".join(context.args)
    if not url.startswith("https://lzt.market"):
        await update.message.reply_text("Пожалуйста, пришли корректную ссылку на товар с сайта lzt.market")
        return

    chat_id = update.effective_chat.id
    await update.message.reply_text("Начинаю отслеживание товара на 1 час.")

    async def monitor():
        logging.info(f"[{chat_id}] Старт отслеживания: {url}")
        last_seen_ids = set()
        last_prices = {}

        start_time = time.time()
        while time.time() - start_time < 3600:
            try:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.select(".market-item")

                current_ids = set()
                for item in items:
                    item_id = item.get("data-id")
                    current_ids.add(item_id)
                    price_tag = item.select_one(".price")
                    price = int(price_tag.text.replace("₽", "").strip()) if price_tag else 0

                    if item_id not in last_seen_ids:
                        item_link = f"https://lzt.market/{item_id}"
                        await context.bot.send_message(chat_id=chat_id, text=f"Новый товар: {item_link}")
                    elif item_id in last_prices and price < last_prices[item_id]:
                        item_link = f"https://lzt.market/{item_id}"
                        await context.bot.send_message(chat_id=chat_id, text=f"Цена снизилась: {item_link} — {price}₽")

                    last_prices[item_id] = price

                last_seen_ids = current_ids
                await asyncio.sleep(60)

            except Exception as e:
                logging.error(f"[{chat_id}] Ошибка при парсинге: {e}")
                await asyncio.sleep(60)

    task = asyncio.create_task(monitor())
    user_tasks[chat_id] = task

if __name__ == "__main__":
    print("Запуск бота...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track", track))
    print("Бот инициализирован. Запускаем polling...")
    app.run_polling()
