# 7892328849:AAF-GW_43V2eG3gxcvIQ-E2LKpuKmMw9X54
import asyncio
import json
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from flask import Flask
from threading import Thread

# Flask serverni yaratamiz
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

    
# Bot tokeni
API_TOKEN = '7892328849:AAF-GW_43V2eG3gxcvIQ-E2LKpuKmMw9X54'

# Bot va Dispatcher yaratish
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Ma'lumotlarni faylda saqlash funksiyalari
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": {}, "active_chats": {}, "blocked_users": {}}

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

# Fayldan yuklangan ma'lumotlar
data = load_data()
users = data["users"]
active_chats = data["active_chats"]
blocked_users = data.get("blocked_users", {})

# Klaviatura tugmalari
menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💭 Suhbatni boshlash")],
        [KeyboardButton(text="✅ Start")],
        [KeyboardButton(text="💤 End")]
    ],
    resize_keyboard=True
)

chat_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 Boshqa suhbatdosh tanlash")],
        [KeyboardButton(text="🚫 Bloklash")],
        [KeyboardButton(text="💤 Yakunlash")]
    ],
    resize_keyboard=True
)

# Foydalanuvchini ro'yxatga olish va /start buyrug'i
@dp.message(Command(commands=["start"]))
async def start_handler(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"chat_partner": None, "available": True}
    else:
        users[user_id]["available"] = True
    await message.answer(
        "👋 Salom! Tasodifiy suhbatni boshlash uchun '💭 Suhbatni boshlash' tugmasini bosing.",
        reply_markup=menu_kb
    )

# End tugmasi
@dp.message(lambda message: message.text == "End")
async def end_handler(message: Message):
    user_id = str(message.from_user.id)
    if user_id in users:
        users[user_id]["available"] = False
    await message.answer(
        "💤  Siz end tugmasini bosdingiz. Suhbatlar uchun mavjud emassiz. Agar qayta qo'shilmoqchi bo'lsangiz, 'Start' tugmasini bosing.",
        reply_markup=menu_kb
    )

# Bloklash funksiyasi
@dp.message(lambda message: message.text == "🚫 Bloklash")
async def block_user(message: Message):
    user_id = str(message.from_user.id)
    partner_id = users.setdefault(user_id, {"chat_partner": None})["chat_partner"]

    if partner_id:
        # Blok qilish va suhbatni tugatish
        if user_id not in blocked_users:
            blocked_users[user_id] = []
        blocked_users[user_id].append(partner_id)

        users[partner_id]["chat_partner"] = None
        users[user_id]["chat_partner"] = None
        active_chats.pop(user_id, None)
        active_chats.pop(partner_id, None)

        await bot.send_message(partner_id, "🚫 Sizning suhbatdoshingiz suhbatni tark etdi.", reply_markup=menu_kb)
        await message.answer("🚫 Foydalanuvchini blokladingiz. Suhbat tugatildi.", reply_markup=menu_kb)
    else:
        await message.answer("❌ Hozircha suhbatdoshingiz yo'q.", reply_markup=menu_kb)

# Tasodifiy suhbatni boshlash
@dp.message(lambda message: message.text == "💭 Suhbatni boshlash")
async def start_chat(message: Message):
    user_id = str(message.from_user.id)

    if user_id in active_chats.values():
        await message.answer("❗️ Siz allaqachon suhbatdasiz. Suhbatni tugatib, qayta urinib ko'ring.")
        return

    # Suhbatdoshingizni qidirish
    available_users = [
        user for user, data in users.items()
        if data["chat_partner"] is None and user != user_id and data.get("available", True)
        and user_id not in blocked_users.get(user, [])
        and user not in blocked_users.get(user_id, [])
    ]

    if available_users:
        partner_id = available_users[0]
        users[user_id]["chat_partner"] = partner_id
        users[partner_id]["chat_partner"] = user_id
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        await message.answer("✅ Sizning suhbatdoshingiz topildi! Endi xabar yozishingiz mumkin.", reply_markup=chat_kb)
        await bot.send_message(partner_id, "✅ Sizning suhbatdoshingiz topildi! Endi xabar yozishingiz mumkin.", reply_markup=chat_kb)
    else:
        await message.answer("⏳ Hozircha boshqa foydalanuvchi yo'q. Biroz kutib turing yoki qayta urinib ko'ring.")

# Yakunlash tugmasi
@dp.message(lambda message: message.text == "💤 Yakunlash")
async def end_chat(message: Message):
    user_id = str(message.from_user.id)
    partner_id = users.get(user_id, {}).get("chat_partner")

    if partner_id:
        await bot.send_message(partner_id, "❌ Suhbatdoshingiz suhbatni yakunladi.", reply_markup=menu_kb)
        await message.answer("✅ Siz suhbatni yakunladingiz.", reply_markup=menu_kb)

        users[partner_id]["chat_partner"] = None
        active_chats.pop(partner_id, None)

    users[user_id]["chat_partner"] = None
    active_chats.pop(user_id, None)

# Boshqa suhbatdosh tanlash
@dp.message(lambda message: message.text == "🔄 Boshqa suhbatdosh tanlash")
async def switch_chat(message: Message):
    user_id = str(message.from_user.id)
    partner_id = users.get(user_id, {}).get("chat_partner")

    if partner_id:
        # Oldingi suhbatni tugatish
        await bot.send_message(partner_id, "❌ Sizning suhbatdoshingiz suhbatni tark etdi.", reply_markup=menu_kb)
        users[partner_id]["chat_partner"] = None
        active_chats.pop(partner_id, None)

    users[user_id]["chat_partner"] = None
    active_chats.pop(user_id, None)

    # Suhbatdoshingizni qidirishda eski suhbatdoshingizni chiqarib tashlash
    available_users = [
        user for user, data in users.items()
        if data["chat_partner"] is None and user != user_id and user != partner_id
        and data.get("available", True)
        and user_id not in blocked_users.get(user, [])
        and user not in blocked_users.get(user_id, [])
    ]

    if available_users:
        partner_id = available_users[0]
        users[user_id]["chat_partner"] = partner_id
        users[partner_id]["chat_partner"] = user_id
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        await message.answer("✅ Sizning yangi suhbatdoshingiz topildi! Endi xabar yozishingiz mumkin.", reply_markup=chat_kb)
        await bot.send_message(partner_id, "✅ Sizning yangi suhbatdoshingiz topildi! Endi xabar yozishingiz mumkin.", reply_markup=chat_kb)
    else:
        await message.answer("📌 Hozircha boshqa foydalanuvchi yo'q. Siz kutish ro'yxatiga qo'shildingiz.", reply_markup=menu_kb)

# Xabarlarni yuborish
@dp.message()
async def forward_message(message: Message):
    user_id = str(message.from_user.id)
    partner_id = users.get(user_id, {}).get("chat_partner")

    if partner_id is None:
        await message.answer("❗️Suhbatdoshingiz yo'q. '💭 Suhbatni boshlash' tugmasini bosing.")
        return

    if message.text in ["🔄 Boshqa suhbatdosh tanlash", "🚫 Bloklash", "💤 Yakunlash"]:
        return  # Tugmalar xabar sifatida uzatilmaydi

    await bot.send_message(partner_id, message.text)

# Botni ishga tushirish
async def main():
    import atexit
    # Ma'lumotlarni saqlash funksiyasini dastur to'xtaganda ishga tushirish
    atexit.register(lambda: save_data({"users": users, "active_chats": active_chats, "blocked_users": blocked_users}))

    # Flask serverni ishga tushiramiz
    keep_alive()

    # Telegram botni ishlatamiz
    await dp.start_polling(bot)

# Pythondagi asosiy ishga tushirish
if __name__ == "__main__":
    asyncio.run(main())
