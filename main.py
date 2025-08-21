from pytesseract.pytesseract import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import pytesseract
import re
from PIL import Image
from flask import Flask
import threading

# Flask app
app = Flask(__name__)

# Tesseract command path (Linux/Docker)
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

def run_telegram_bot():
    run_bot()  # ဒီဟာ မင်းရဲ့ Telegram bot polling function

# Start bot in a separate thread
threading.Thread(target=run_telegram_bot).start()

@app.route('/')
def home():
    return "Bot is running 24/7!"

TOKEN = "8287530957:AAHtB42XbsqNCzRs8VpxnXPlVxGj1iDTwG4"

orders = {}
used_transactions = set()


# --- /start command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("Diamond Price 💎", callback_data="yes_topup"),
    ]]
    await update.message.reply_text(
        "Welcome to the TOPZONE \nMLBB Diamond Top-up Bot!",
        reply_markup=InlineKeyboardMarkup(keyboard))


# --- Button handler ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "yes_topup":
        # Diamond price list inline buttons
        keyboard = [[
            InlineKeyboardButton("Wp - 6200", callback_data="Wp"),
            InlineKeyboardButton("Twilight - 32800", callback_data="Twilight")
        ],
                    [
                        InlineKeyboardButton("11 - 900", callback_data="11"),
                        InlineKeyboardButton("22 - 1600", callback_data="22")
                    ],
                    [
                        InlineKeyboardButton("56 - 3900", callback_data="56"),
                        InlineKeyboardButton("112 - 7700", callback_data="112")
                    ],
                    [
                        InlineKeyboardButton("86 - 5100", callback_data="86"),
                        InlineKeyboardButton("172 - 10000",
                                             callback_data="172")
                    ],
                    [
                        InlineKeyboardButton("257 - 14500",
                                             callback_data="257"),
                        InlineKeyboardButton("343 - 19500",
                                             callback_data="343")
                    ],
                    [
                        InlineKeyboardButton("429 - 24400",
                                             callback_data="429"),
                        InlineKeyboardButton("514 - 28900",
                                             callback_data="514")
                    ],
                    [
                        InlineKeyboardButton("600 - 33900",
                                             callback_data="600"),
                        InlineKeyboardButton("706 - 39000",
                                             callback_data="706")
                    ],
                    [
                        InlineKeyboardButton("792 - 33900",
                                             callback_data="792"),
                        InlineKeyboardButton("878 - 39000",
                                             callback_data="878")
                    ],
                    [
                        InlineKeyboardButton("963 - 33900",
                                             callback_data="963"),
                        InlineKeyboardButton("1049 - 39000",
                                             callback_data="1049")
                    ],
                    [
                        InlineKeyboardButton("1412 - 33900",
                                             callback_data="1412"),
                        InlineKeyboardButton("2195 - 39000",
                                             callback_data="2195")
                    ],
                    [
                        InlineKeyboardButton("2195 - 33900",
                                             callback_data="2195"),
                        InlineKeyboardButton("3688 - 39000",
                                             callback_data="3688")
                    ],
                    [
                        InlineKeyboardButton("5532 - 33900",
                                             callback_data="5534"),
                        InlineKeyboardButton("9288 - 39000",
                                             callback_data="9288")
                    ],
                    [
                        InlineKeyboardButton("50+50 - 3200",
                                             callback_data="50+50"),
                        InlineKeyboardButton("150+150 - 9600",
                                             callback_data="150+150")
                    ],
                    [
                        InlineKeyboardButton("250+250 - 15300",
                                             callback_data="250+250"),
                        InlineKeyboardButton("500+500 - 31300",
                                             callback_data="500+500")
                    ]]
        await query.edit_message_text(
            "💎 Diamond Price List",
            reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in [
            "Wp", "Twilight", "11", "22", "56", "112", "86", "172", "257",
            "343", "429", "514", "600", "706", "792", "878", "963", "1049",
            "1412", "2195", "3688", "5534", "9288", "50+50", "150+150",
            "250+250", "500+500"
    ]:
        # User selects a diamond package
        price_map = {
            "Wp": "6200",
            "Twilight": "32800",
            "11": "900",
            "22": "1600",
            "56": "3900",
            "112": "7700",
            "86": "5100",
            "172": "10000",
            "257": "14500",
            "343": "19500",
            "429": "24400",
            "514": "28900",
            "600": "33900",
            "706": "39000",
            "792": "44100",
            "878": "49000",
            "963": "53500",
            "1049": "58500",
            "1412": "78000",
            "2195": "118100",
            "3688": "197000",
            "5532": "297400",
            "9288": "493900",
            "50+50": "3200",
            "150+150": "9600",
            "250+250": "15300",
            "500+500": "31300"
        }
        orders[user_id] = {
            "item": str(query.data),
            "price": price_map[query.data],
            "paid": False,
            "slip": None,
            "txid": None
        }
        # Ask user to send payment slip
        await query.edit_message_text(
            f"💰 သင်ပေးချေရမဲ့ ပမာဏ - {price_map[query.data]} Ks\n"
            f"📲 Payment Number - 09950574646\n\n"
            "⚠️ ငွေလွှဲပြီးပြေစာပို့ပေးပါ")

    elif query.data == "cancel":
        orders.pop(user_id, None)
        await query.edit_message_text("🛑 အမှာစာကို ရပ်တန့်လိုက်ပါ")


# --- Handle payment slip photo ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in orders:
        return

    if orders[user_id].get("paid"):
        await update.message.reply_text(
            "⚠️ သင့် ငွေလွှဲပြေစာကို ပို့ပြီးသားဖြစ်ပါတယ်"
        )
        return

    # Download photo
    file = await update.message.photo[-1].get_file()
    file_path = f"slip_{user_id}.jpg"
    await file.download_to_drive(file_path)
    orders[user_id]["slip"] = update.message.photo[-1].file_id

    # OCR read
    text = pytesseract.image_to_string(Image.open(file_path))

    # Transaction ID extraction
    txid_match = re.search(r"\b\d{8,16}\b", text)
    txid = txid_match.group(0) if txid_match else None
    orders[user_id]["txid"] = txid

    if txid and txid in used_transactions:
        await update.message.reply_text(
            "❌ ဤငွေလွှဲပြေစာကို အသုံးပြုပြီးသားဖြစ်သည်"
        )
        return

    # Check payment amount using digits only
    price = str(orders[user_id]["price"])

        # OCR မှာထွက်လာတဲ့ text မှာ comma, space, Ks, MMK ဖယ်ရှားပြီး digit-only string
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




# --- Handle GameID + Server ---
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

        # Forward to admin
        ADMIN_ID = 1780875984
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=(f"📦 New Order:\n"
                                             f"GameID+Server: {game_info}\n"
                                             f"Diamond: {item}\n"
                                             f"Price: {price}Ks\n"
                                             f"Slip ID / TxID: {txid}"))
        if slip_file_id:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=slip_file_id)

        orders.pop(user_id, None)


# --- Main ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_id))

    app.run_polling()


    


if __name__ == "__main__":
    # Start Flask server
    app.run(host="0.0.0.0", port=5000)

    main()
   

