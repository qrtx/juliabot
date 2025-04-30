import logging
import requests
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart

API_TOKEN = '7581738932:AAGWk4a_9d3y3kFutWfZfDG1V49QviSEWmU'
FIREBASE_URL = 'https://ozon-shifts-default-rtdb.firebaseio.com'
FIREBASE_KEY = 'AIzaSyBx7N43Wpf0Ohh6197YLlv-ppeHHaJq_TQ'
ADMIN_ID = 470626186

OPENAI_API_KEY = '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'
openai.api_key = OPENAI_API_KEY

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

system_prompt = "Ты — вежливый и нейтральный помощник сотрудников ПВЗ Озона. Отвечай кратко, строго по теме, без флирта и шуток."

# --- Проверка, стоит ли отвечать ---
def should_respond(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        return True
    if f"@{bot.username}" in message.text:
        return True
    if "Юля" in message.text:
        return True
    return False

# --- Firebase функции ---
def get_shifts():
    r = requests.get(f"{FIREBASE_URL}/shifts.json?auth={FIREBASE_KEY}")
    return r.json() or {}

def add_shift(name, point, date):
    payload = {"name": name, "point": point, "date": date}
    r = requests.post(f"{FIREBASE_URL}/shifts.json?auth={FIREBASE_KEY}", json=payload)
    return r.status_code == 200

# --- GPT ответ ---
def ask_openai(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# --- Обработка обычных сообщений ---
@dp.message_handler()
async def handle_message(message: types.Message):
    if not should_respond(message):
        return

    user_text = message.text

    if "сколько у меня смен" in user_text.lower():
        all_shifts = get_shifts()
        count = sum(1 for shift in all_shifts.values() if shift.get("name") == message.from_user.full_name)
        await message.reply(f"У вас {count} смен.")
        return

    reply = ask_openai(user_text)
    await message.reply(reply)

# --- Команды админа ---
@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_ID and msg.text.startswith("/set_prompt"))
async def set_prompt(message: Message):
    global system_prompt
    system_prompt = message.text.replace("/set_prompt", "").strip()
    await message.reply("Инструкция обновлена.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
