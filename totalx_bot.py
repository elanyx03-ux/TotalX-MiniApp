import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Carica le variabili dal file .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Dizionario per salvare gli utenti e i loro movimenti
user_data = {}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Ciao! Sono TotalX Bot. Usa /+numero per aggiungere, /-numero per sottrarre, /tot per il totale e /report per l'estratto conto.")

def add(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = []

    try:
        value = int(context.args[0])
        user_data[user_id].append(value)
        total = sum(user_data[user_id])
        update.message.reply_text(f"Aggiunto {value}. Totale: {total}")
    except (IndexError, ValueError):
        update.message.reply_text("Uso corretto: /+numero, esempio /+3")

def subtract(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = []

    try:
        value = int(context.args[0])
        user_data[user_id].append(-value)
        total = sum(user_data[user_id])
        update.message.reply_text(f"Sottratto {value}. Totale: {total}")
    except (IndexError, ValueError):
        update.message.reply_text("Uso corretto: /-numero, esempio /-2")

def total(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    total = sum(user_data.get(user_id, []))
    update.message.reply_text(f"Totale attuale: {total}")

def report(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    movements = user_data.get(user_id, [])
    if not movements:
        update.message.reply_text("Nessun movimento registrato.")
    else:
        report_text = "\n".join([f"{'+' if m>0 else ''}{m}" for m in movements])
        update.message.reply_text(f"Movimenti:\n{report_text}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("+", add))
    dp.add_handler(CommandHandler("-", subtract))
    dp.add_handler(CommandHandler("tot", total))
    dp.add_handler(CommandHandler("report", report))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
