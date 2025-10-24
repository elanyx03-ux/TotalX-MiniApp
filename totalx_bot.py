import os
import csv
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv

# ----------------------------
# Config
# ----------------------------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OPERATORS_FILE = "operators.txt"
OPERATIONS_FILE = "operations.csv"
TOTAL_FILE = "total.txt"  # mantiene il totale attuale in memoria

# ----------------------------
# Operatori
# ----------------------------
def read_operators():
    try:
        with open(OPERATORS_FILE, "r") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []

def save_operators(operators):
    with open(OPERATORS_FILE, "w") as f:
        for op in operators:
            f.write(f"{op}\n")

def is_operator(update: Update):
    username = update.effective_user.username
    operators = read_operators()
    return username in operators

# ----------------------------
# Totale
# ----------------------------
def read_total():
    try:
        with open(TOTAL_FILE, "r") as f:
            return int(f.read())
    except FileNotFoundError:
        return 0

def save_total(total):
    with open(TOTAL_FILE, "w") as f:
        f.write(str(total))

# ----------------------------
# Log operazioni su CSV
# ----------------------------
def log_operation(username, op_type, amount, total):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(OPERATIONS_FILE)
    with open(OPERATIONS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Data", "Operatore", "Tipo", "Importo", "Totale"])
        writer.writerow([date_str, username, op_type, amount, total])

# ----------------------------
# Comandi bot
# ----------------------------
def add(update: Update, context: CallbackContext):
    if not is_operator(update):
        update.message.reply_text("❌ Non sei autorizzato a modificare il totale.")
        return
    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        update.message.reply_text("❌ Usa /a <importo>")
        return
    total = read_total() + amount
    save_total(total)
    log_operation(update.effective_user.username, "+", amount, total)
    update.message.reply_text(f"✅ Totale aggiornato: {total}")

def subtract(update: Update, context: CallbackContext):
    if not is_operator(update):
        update.message.reply_text("❌ Non sei autorizzato a modificare il totale.")
        return
    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        update.message.reply_text("❌ Usa /s <importo>")
        return
    total = read_total() - amount
    save_total(total)
    log_operation(update.effective_user.username, "-", amount, total)
    update.message.reply_text(f"✅ Totale aggiornato: {total}")

def commission(update: Update, context: CallbackContext):
    if not is_operator(update):
        update.message.reply_text("❌ Non sei autorizzato a modificare il totale.")
        return
    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        update.message.reply_text("❌ Usa /c <importo>")
        return
    total = read_total() + amount
    save_total(total)
    log_operation(update.effective_user.username, "commissioni / tasse", amount, total)
    update.message.reply_text(f"💰 Commissioni/tasse aggiunte: {amount}\nTotale aggiornato: {total}")

def total_cmd(update: Update, context: CallbackContext):
    total = read_total()
    update.message.reply_text(f"💰 Totale attuale: {total}")

# ----------------------------
# Chiusura cassa /stop
# ----------------------------
def stop(update: Update, context: CallbackContext):
    if not is_operator(update):
        update.message.reply_text("❌ Non sei autorizzato a fermare il conteggio.")
        return

    # Leggi tutte le operazioni
    operations = []
    if os.path.exists(OPERATIONS_FILE):
        with open(OPERATIONS_FILE, "r") as f:
            reader = csv.reader(f)
            operations = list(reader)

    # Prepara l'estratto conto
    if len(operations) > 1:  # la prima riga è l'intestazione
        message = "📄 Estratto conto di chiusura:\n"
        for row in operations[1:]:
            data, operatore, tipo, importo, totale = row
            message += f"{data} | {operatore} | {tipo} {importo} | Totale: {totale}\n"
    else:
        message = "📄 Nessuna operazione registrata oggi."

    total = read_total()
    message += f"\n💰 Totale finale: {total}"

    # Invia estratto conto su Telegram
    update.message.reply_text(message)

    # Resetta il totale e CSV
    save_total(0)
    with open(OPERATIONS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Data", "Operatore", "Tipo", "Importo", "Totale"])

    update.message.reply_text("♻️ Chiusura cassa completata. Nuovo foglio pronto!")

# ----------------------------
# Comandi gestione operatori
# ----------------------------
def add_operatore(update: Update, context: CallbackContext):
    if not is_operator(update):
        update.message.reply_text("❌ Non sei autorizzato a fare questa operazione.")
        return
    try:
        new_op = context.args[0].lstrip("@")
    except IndexError:
        update.message.reply_text("❌ Usa /add_operatore @username")
        return
    operators = read_operators()
    if new_op in operators:
        update.message.reply_text("❌ Utente già operatore")
        return
    operators.append(new_op)
    save_operators(operators)
    update.message.reply_text(f"✅ Operatore aggiunto: @{new_op}")

def rm_operatore(update: Update, context: CallbackContext):
    if not is_operator(update):
        update.message.reply_text("❌ Non sei autorizzato a fare questa operazione.")
        return
    try:
        rm_op = context.args[0].lstrip("@")
    except IndexError:
        update.message.reply_text("❌ Usa /rm_operatore @username")
        return
    operators = read_operators()
    if rm_op not in operators:
        update.message.reply_text("❌ Utente non presente nella lista")
        return
    operators.remove(rm_op)
    save_operators(operators)
    update.message.reply_text(f"✅ Operatore rimosso: @{rm_op}")

# ----------------------------
# Main
# ----------------------------
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("a", add))
    dp.add_handler(CommandHandler("s", subtract))
    dp.add_handler(CommandHandler("c", commission))
    dp.add_handler(CommandHandler("total", total_cmd))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("add_operatore", add_operatore))
    dp.add_handler(CommandHandler("rm_operatore", rm_operatore))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
