# totalx_bot.py
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Carica il token dal file .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Lista operatori iniziale
OPERATORS = ["@elanyx"]

# Stato cassa e log
total = 0
commissions = 0
log = []  # lista di tuple (operatore, tipo, importo)

# ===== Funzioni helper =====
def is_operator(user):
    return user in OPERATORS

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total
    user = update.effective_user.username
    if not is_operator(f"@{user}"):
        await update.message.reply_text("Non sei autorizzato!")
        return
    try:
        amount = float(context.args[0])
        total += amount
        log.append((user, "+", amount))
        await update.message.reply_text(f"{user} ha aggiunto {amount}. Totale: {total}")
    except:
        await update.message.reply_text("Uso corretto: /a importo")

async def subtract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total
    user = update.effective_user.username
    if not is_operator(f"@{user}"):
        await update.message.reply_text("Non sei autorizzato!")
        return
    try:
        amount = float(context.args[0])
        total -= amount
        log.append((user, "-", amount))
        await update.message.reply_text(f"{user} ha sottratto {amount}. Totale: {total}")
    except:
        await update.message.reply_text("Uso corretto: /s importo")

async def commission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global commissions
    user = update.effective_user.username
    if not is_operator(f"@{user}"):
        await update.message.reply_text("Non sei autorizzato!")
        return
    try:
        amount = float(context.args[0])
        commissions += amount
        log.append((user, "C", amount))
        await update.message.reply_text(f"{user} ha aggiunto commissioni {amount}. Totale commissioni: {commissions}")
    except:
        await update.message.reply_text("Uso corretto: /c importo")

async def show_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Totale attuale: {total}\nCommissioni: {commissions}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total, commissions, log
    user = update.effective_user.username
    if not is_operator(f"@{user}"):
        await update.message.reply_text("Non sei autorizzato!")
        return

    # Estratto conto
    report = "Estratto conto:\n"
    for entry in log:
        report += f"{entry[0]} ha {entry[1]} {entry[2]}\n"
    report += f"\nTotale finale: {total}\nCommissioni: {commissions}"
    await update.message.reply_text(report)

    # Resetta cassa
    total = 0
    commissions = 0
    log = []

async def add_operator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if not is_operator(f"@{user}"):
        await update.message.reply_text("Non sei autorizzato!")
        return
    try:
        new_op = context.args[0]
        if new_op not in OPERATORS:
            OPERATORS.append(new_op)
            await update.message.reply_text(f"{new_op} aggiunto agli operatori!")
        else:
            await update.message.reply_text(f"{new_op} è già un operatore.")
    except:
        await update.message.reply_text("Uso corretto: /add_operatore @username")

async def remove_operator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if not is_operator(f"@{user}"):
        await update.message.reply_text("Non sei autorizzato!")
        return
    try:
        rem_op = context.args[0]
        if rem_op in OPERATORS:
            OPERATORS.remove(rem_op)
            await update.message.reply_text(f"{rem_op} rimosso dagli operatori!")
        else:
            await update.message.reply_text(f"{rem_op} non è un operatore.")
    except:
        await update.message.reply_text("Uso corretto: /rm_operatore @username")

# ===== Main =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("a", add))
    app.add_handler(CommandHandler("s", subtract))
    app.add_handler(CommandHandler("c", commission))
    app.add_handler(CommandHandler("total", show_total))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("add_operatore", add_operator))
    app.add_handler(CommandHandler("rm_operatore", remove_operator))

    print("Bot avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
