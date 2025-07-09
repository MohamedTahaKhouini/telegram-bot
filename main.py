from flask import Flask, request
import requests
from replit import db

app = Flask(__name__)

# === CONFIG ===
BOT_TOKEN = '7498068418:AAE1zOdQ_gF1XnYKbubRZ4rNsH7DxhaWqEo'
ADMIN_ID = '6154924977'  # Replace this with your own Telegram ID
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

def send_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(TELEGRAM_API, json=data)

@app.route('/', methods=["POST"])
def webhook():
    data = request.get_json()
    message = data.get('message', {})
    chat_id = str(message['chat']['id'])
    text = message.get('text', '').strip()

    if text == '/start':
        keyboard = {
            "keyboard": [
                ["📋 View Menu", "🛒 Place Order"],
                ["📆 Reserve Table", "🕐 Opening Hours"],
                ["📞 Contact Us"]
            ],
            "resize_keyboard": True
        }
        send_message(chat_id, "👋 Welcome to TasteBite Bistro!\nChoose an option:", reply_markup=keyboard)

    elif text == "📋 View Menu":
        menu_text = "<b>🍴 Our Menu</b>\n\n🍕 Pizza - 15dt\n🥙 Couscous - 20dt\n🍰 Dessert - 8dt\n🥤 Drinks - 4dt"
        send_message(chat_id, menu_text)

    elif text == "🕐 Opening Hours":
        send_message(chat_id, "🕐 We are open:\nMon-Sat: 12pm - 10pm\nSun: Closed")

    elif text == "📞 Contact Us":
        send_message(chat_id, "📞 Phone: +216 12345678\n📍 Address: 123 Main Street, Tunis")

    elif text == "🛒 Place Order":
        send_message(chat_id, "🛒 Please type your order like this:\n\nPizza x1\nDessert x2")

    elif text == "📆 Reserve Table":
        send_message(chat_id, "📅 Please type your reservation like this:\n\nTable for 2 on Friday at 8PM")

    elif text == "/myorders":
        orders = db.get(chat_id, [])
        if not orders:
            send_message(chat_id, "🗂️ You have no orders yet.")
        else:
            order_list = "\n".join([f"{i+1}. {o}" for i, o in enumerate(orders)])
            send_message(chat_id, f"📦 Your orders:\n{order_list}")

    else:
        # Save order/reservation
        if chat_id not in db:
            db[chat_id] = []
        orders = db[chat_id]
        orders.append(text)
        db[chat_id] = orders

        send_message(chat_id, "✅ Your request has been received!")

        # Notify admin
        send_message(ADMIN_ID, f"📩 New message from {chat_id}:\n{text}")

    return 'OK'
