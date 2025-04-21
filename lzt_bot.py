import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

TOKEN = '7747932663:AAGjBtgIp9di9aLZ09bk8-Gm5k802RfozCs'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URL = "https://lzt.market/steam/?rt=nomatter&mm_ban=nomatter&order_by=pdate_to_down_upload"

user_data = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await context.bot.send_message(chat_id=user_id, text=f"[{user_id}] Старт отслеживания: {URL}")
    user_data[user_id] = {"last_title": None}
    asyncio.create_task(monitor(update, context, user_id))


async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    while True:
        try:
            response = requests.get(URL, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            listing = soup.find("div", class_="market-lot market-lot-hover")

            if not listing:
                raise Exception("Не удалось найти лот")

            title = listing.find("div", class_="title").text.strip()
            link = listing.find("a", href=True)["href"]

            if user_data[user_id]["last_title"] != title:
                user_data[user_id]["last_title"] = title
                full_url = f"https://lzt.market{link}"
                await context.bot.send_message(chat_id=user_id, text=f"Новый лот: {title}\n{full_url}")
        except Exception as e:
            logger.error(f"[{user_id}] Ошибка при парсинге: {e}")
        await asyncio.sleep(30)


if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
        
