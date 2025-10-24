import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openpyxl import Workbook, load_workbook

# Carica variabili d'ambiente
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Nome del file Excel
FILE_EXCEL = "estratto_conto.xlsx"

# Carica o crea il file Excel
if os.path.exists(FILE_EXCEL):
    wb = load_workbook(FILE_EXCEL)
    ws = wb.active
else:
    wb = Workbook()
    ws = wb.active
    ws.append(["user_id", "movimento"])  # intestazioni
    wb.save(FILE_EXCEL)

# Funzioni di utilità
def salva_movimento(user_id: int, valore: int):
    ws.append([user_id, valore])
    wb.save(FILE_EXCEL)

def leggi_movimenti(user_id: int):
    movimenti = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] == user_id:
            movimenti.append(row[1])
    return movimenti

def estratto_conto(user_id: int):
    movimenti = leggi_movimenti(user_id)
    entrate = [m for m in movimenti if m > 0]
    uscite = [m for m in movimenti if m < 0]
    totale_entrate = sum(entrate)
    totale_uscite = sum(uscite)
    saldo = totale_entrate + totale_uscite
    return entrate, uscite, totale_entrate, totale_uscite, saldo

# Comandi del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Sono TotalX Estratto Conto Bot.\n"
        "Comandi:\n"
        "/add numero - aggiunge un'entrata\n"
        "/subtract numero - aggiunge un'uscita\n"
        "/total - mostra il saldo totale\n"
        "/report - mostra l'estratto conto dettagliato"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = int(context.args[0])
        user_id = update.message.from_user.id
        salva_movimento(user_id, value)
        entrate, uscite, totale_entrate, totale_uscite, saldo = estratto_conto(user_id)
        await update.message.reply_text(
            f"Entrata registrata: +{value}\nSaldo attuale: {saldo}"
        )
    except (IndexError, ValueError):
        await update.message.reply_text("Errore! Usa /add numero, esempio /add 100")

async def subtract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = int(context.args[0])
        user_id = update.message.from_user.id
        salva_movimento(user_id, -value)
        entrate, uscite, totale_entrate, totale_uscite, saldo = estratto_conto(user_id)
        await update.message.reply_text(
            f"Uscita registrata: -{value}\nSaldo attuale: {saldo}"
        )
    except (IndexError, ValueError):
        await update.message.reply_text("Errore! Usa /subtract numero, esempio /subtract 50")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    _, _, _, _, saldo = estratto_conto(user_id)
    await update.message.reply_text(f"Saldo totale: {saldo}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    entrate, uscite, totale_entrate, totale_uscite, saldo = estratto_conto(user_id)
    
    if not entrate and not uscite:
        await update.message.reply_text("Nessun movimento registrato.")
        return
    
    report_text = "📄 Estratto Conto\n\n"
    if entrate:
        report_text += "Entrate:\n" + "\n".join([f"+{m}" for m in entrate]) + f"\nTotale Entrate: {totale_entrate}\n\n"
    if uscite:
        report_text += "Uscite:\n" + "\n".join([f"{m}" for m in uscite]) + f"\nTotale Uscite: {totale_uscite}\n\n"
    report_text += f"Saldo: {saldo}"
    
    await update.message.reply_text(report_text)

# Funzione principale
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("subtract", subtract))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("report", report))

    print("Bot avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
