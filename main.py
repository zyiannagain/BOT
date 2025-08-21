from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import pytesseract, re
from PIL import Image

TOKEN = "8287530957:AAHtB42XbsqNCzRs8VpxnXPlVxGj1iDTwG4"

orders = {}
used_transactions = set()


# --- /start command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("Yes", callback_data="yes_topup"),
    ]]
    await update.message.reply_text(
        "MLBB Topup Bot ✅\nသင် MLBB Diamond ဝယ်ချင်ပါသလား?",
        reply_markup=InlineKeyboardMarkup(keyboard))


# --- Button handler ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "yes_topup":
        await context.bot.send_message(
            chat_id=user_id,
            text=
            "Dia 11 - 900 Ks\nDia 22 - 1600 Ks\nDia 56 - 3900 Ks\nDia 112 - 7700 Ks\nDia 86 - 5100 Ks\nDia 172 - 10000 Ks\nDia 257 - 14500 Ks\nDia 343 - 19500 Ks\nDia 429 - 24400 Ks\nDia 514 - 28900 Ks\nDia 600 - 33900 Ks\nDia 706 - 39000 Ks"
        )
    elif query.data == "buy":
        await query.edit_message_text(
            "KBZ/Wave/UAB/AYA Pay နဲ့ ငွေလွှဲကာပြေစာ ပို့ပါ")
    elif query.data == "cancel":
        orders.pop(user_id, None)
        await query.edit_message_text("🛑 အမှာစာကို ရပ်တန့်လိုက်ပါ")


# --- Handle topup choice ---
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    user_id = update.effective_user.id
    if choice in ["11","22","56","112","86","172","257","343","429","514","600","706"]:
        price_map = {"11": 900, "22": 1600, "56": 3900 , "112": 7700, "86": 5100, "172":10000, "257": 14500, "343": 19500, "429": 24400, "514": 28900, "600":33900, "706": 39000}
        orders[user_id] = {
            "item": int(choice),
            "price": price_map[choice],
            "paid": False,
            "slip": None,
            "txid": None
        }
        keyboard = [[
            InlineKeyboardButton("✅ Buy", callback_data="buy"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]]
        await update.message.reply_text(
            f"သင် ငွေပေးချေရမဲ့ ပမာဏ - {price_map[choice]} ကျပ်\n Payment Number - 09950574646",
            reply_markup=InlineKeyboardMarkup(keyboard))


# --- Handle payment slip photo ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in orders:
        return

    if orders[user_id].get("paid"):
        await update.message.reply_text(
            "⚠️ သင့် ငွေလွှဲပြေစာကို ပို့ပြီးသားဖြစ်ပါတယ်")
        return

    file = await update.message.photo[-1].get_file()
    file_path = f"slip_{user_id}.jpg"
    await file.download_to_drive(file_path)

    # Keep slip file_id
    orders[user_id]["slip"] = update.message.photo[-1].file_id

    # OCR read
    text = pytesseract.image_to_string(Image.open(file_path))

    # Transaction ID extraction
    txid_match = re.search(r"\b\d{8,16}\b", text)
    txid = txid_match.group(0) if txid_match else None
    orders[user_id]["txid"] = txid

    # Check if already used
    if txid and txid in used_transactions:
        await update.message.reply_text(
            "❌ ဤငွေလွှဲပြေစာကို အသုံးပြုပြီးသားဖြစ်သည်")
        return

    # Check payment amount
    price = str(orders[user_id]["price"])
    if price in text:
        await update.message.reply_text(
            "✅ ငွေလွှဲမှုအောင်မြင်ပါသည်\nGame ID + Server ပေးပါ\n(ဥပမာ: 570780169 8270)"
        )
        orders[user_id]["paid"] = True
        if txid:
            used_transactions.add(txid)
    else:
        await update.message.reply_text("ငွေပမာဏမမှန်ပါ")


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
    app.add_handler(
        MessageHandler(filters.Regex("^(11|12|13)$"), handle_choice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_id))

    app.run_polling()


if __name__ == "__main__":
    main()
