from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import pytesseract
import re
from PIL import Image
from flask import Flask, request, Response
import asyncio

TOKEN = "8168270944:AAGi56x3BpWZziLStohHjGL0N5xWnoTQOIA"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"https://topzone-diamond-bot.onrender.com{WEBHOOK_PATH}"

orders = {}
used_transactions = set()

# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Diamond Price 💎", callback_data="yes_topup")]]
    await update.message.reply_text(
        "Welcome to the TOPZONE \nMLBB Diamond Top-up Bot!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "yes_topup":
        keyboard = [[InlineKeyboardButton("Wp - 6200", callback_data="Wp"),
                     InlineKeyboardButton("Twilight - 32800", callback_data="Twilight")]]
        await query.edit_message_text("💎 Diamond Price List", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["Wp", "Twilight", "11", "22", "56", "112", "86", "172", "257", "343", "429", "514",
                        "600", "706", "792", "878", "963", "1049", "1412", "2195", "3688", "5534", "9288",
                        "50+50", "150+150", "250+250", "500+500"]:
        price_map = {
            "Wp": "6200", "Twilight": "32800", "11": "900", "22": "1600", "56": "3900", "112": "7700",
            "86": "5100", "172": "10000", "257": "14500", "343": "19500", "429": "24400", "514": "28900",
            "600": "33900", "706": "39000", "792": "44100", "878": "49000", "963": "53500", "1049": "58500",
            "1412": "78000", "2195": "118100", "3688": "197000", "5534": "297400", "9288": "493900",
            "50+50": "3200", "150+150": "9600", "250+250": "15300", "500+500": "31300"
        }
        orders[user_id] = {
            "item": str(query.data),
            "price": price_map[query.data],
            "paid": False,
            "slip": None,
            "txid": None
        }
        await query.edit_message_text(
            f"💰 သင်ပေးချေရမဲ့ ပမာဏ - {price_map[query.data]} Ks\n📲 Payment Number - 09950574646\n\n⚠️ ငွေလွှဲပြီးပြေစာပို့ပေးပါ"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in orders:
        return

    file = await update.message.photo[-1].get_file()
    file_path = f"slip_{user_id}.jpg"
    await file.download_to_drive(file_path)
    orders[user_id]["slip"] = update.message.photo[-1].file_id

    text = pytesseract.image_to_string(Image.open(file_path))
    txid_match = re.search(r"\b\d{8,16}\b", text)
    txid = txid_match.group(0) if txid_match else None
    orders[user_id]["txid"] = txid

    if txid and txid in used_transactions:
        await update.message.reply_text("❌ ဤငွေလွှဲပြေစာကို အသုံးပြုပြီးသားဖြစ်သည်")
        return

    price = str(orders[user_id]["price"])
    cleaned_text = re.sub(r"[^\d]", "", text)

    if price == cleaned_text or price in cleaned_text:
        await update.message.reply_text(
            "✅ ငွေလွှဲမှုအောင်မြင်ပါသည်\nGame ID + Server ပေးပါ\n(ဥပမာ: 570780169 8270)"
        )
        orders[user_id]["paid"] = True
        if txid:
            used_transactions.add(txid)
    else:
        await update.message.reply_text("❌ ငွေပမာဏမမှန်ပါ")

async def handle_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in orders and orders[user_id].get("paid"):
        game_info = update.message.text.strip()
        item = orders[user_id]["item"]
        price = orders[user_id]["price"]
        slip_file_id = orders[user_id]["slip"]
        txid = orders[user_id].get("txid", "မသိပါ")
        await update.message.reply_text(
            f"✅ Order Received\nGame ID+Server: {game_info}\nDiamond: {item}\nPrice: {price}K\nနောက်ငါးမိနစ်အတွင်းရောက်ပါမည်"
        )
        ADMIN_ID = 1780875984
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"📦 New Order:\nGameID+Server: {game_info}\nDiamond: {item}\nPrice: {price}Ks\nSlip ID / TxID: {txid}")
        if slip_file_id:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=slip_file_id)
        orders.pop(user_id, None)

# --- Flask Webhook Server ---
app = Flask(__name__)
bot_app = Application.builder().token(TOKEN).build()

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(button))
bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_id))

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot_app.bot)
    asyncio.run(bot_app.update_queue.put(update))
    return Response("ok", status=200)

@app.before_first_request
def set_webhook():
    asyncio.run(bot_app.bot.set_webhook(WEBHOOK_URL))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
