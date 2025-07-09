from flask import Flask, request
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

user_orders = {}  # Temporary in-memory storage for orders per user

def send_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(f"{TELEGRAM_API}/sendMessage", json=data)

def answer_callback(callback_id, text=None):
    data = {
        "callback_query_id": callback_id,
    }
    if text:
        data["text"] = text
        data["show_alert"] = False
    requests.post(f"{TELEGRAM_API}/answerCallbackQuery", json=data)

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()

    # Handle Callback Query (inline button pressed)
    if 'callback_query' in data:
        callback = data['callback_query']
        chat_id = str(callback['message']['chat']['id'])
        callback_id = callback['id']
        data_payload = callback['data']

        if data_payload.startswith("order_"):
            item = data_payload.split("_",1)[1]
            user_orders.setdefault(chat_id, {})
            user_orders[chat_id][item] = user_orders[chat_id].get(item, 0) + 1
            answer_callback(callback_id, f"Added 1 {item} to your order.")
            # Update order summary message
            order_text = "🛒 Your current order:\n"
            for k,v in user_orders[chat_id].items():
                order_text += f"{k} x{v}\n"
            send_message(chat_id, order_text)
        
        elif data_payload == "complete_order":
            if chat_id not in user_orders or not user_orders[chat_id]:
                send_message(chat_id, "❌ You have not added any items yet.")
            else:
                order_summary = "\n".join([f"{k} x{v}" for k,v in user_orders[chat_id].items()])
                send_message(chat_id, f"✅ Order received:\n{order_summary}\nWe will contact you shortly.")
                # Notify admin
                send_message(ADMIN_ID, f"📩 New order from {chat_id}:\n{order_summary}")
                user_orders[chat_id] = {}  # Clear user order after submission

        return 'OK'

    # Handle normal messages
    message = data.get('message', {})
    chat_id = str(message.get('chat', {}).get('id', ''))
    text = message.get('text', '').strip()

    if text == '/start':
        keyboard = {
            "keyboard": [
                ["📋 View Menu", "📆 Reserve Table"],
                ["🕐 Opening Hours", "📞 Contact Us"],
                ["🛒 My Orders"]
            ],
            "resize_keyboard": True
        }
        send_message(chat_id, "👋 Welcome to TasteBite Bistro!\nChoose an option:", reply_markup=keyboard)

    elif text == "📋 View Menu":
        # Send inline menu keyboard
        keyboard = {
            "inline_keyboard": [
                [{"text": "🍕 Pizza - 15dt", "callback_data": "order_Pizza"}],
                [{"text": "🥙 Couscous - 20dt", "callback_data": "order_Couscous"}],
                [{"text": "🍰 Dessert - 8dt", "callback_data": "order_Dessert"}],
                [{"text": "🥤 Drinks - 4dt", "callback_data": "order_Drinks"}],
                [{"text": "✅ Complete Order", "callback_data": "complete_order"}]
            ]
        }
        send_message(chat_id, "Select items to add to your order:", reply_markup=keyboard)

    elif text == "🕐 Opening Hours":
        send_message(chat_id, "🕐 We are open:\nMon-Sat: 12pm - 10pm\nSun: Closed")

    elif text == "📞 Contact Us":
        send_message(chat_id, "📞 Phone: +216 12345678\n📍 Address: 123 Main Street, Tunis")

    elif text == "🛒 My Orders":
        send_message(chat_id, "⚠️ This feature will be available soon!")

    elif text == "📆 Reserve Table":
        send_message(chat_id, "📅 Please type your reservation like this:\n\nTable for 2 on Friday at 8PM")

    else:
        send_message(chat_id, "❓ Sorry, I didn't understand that command. Use the menu buttons below.")

    return 'OK'

if __name__ == '__main__':
    app.run(debug=True)