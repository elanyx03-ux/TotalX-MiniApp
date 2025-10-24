import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openpyxl import Workbook, load_workbook

# Carica variabili d'ambiente
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Nome del file principale che salva tutti i dati
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

def crea_file_excel_utente(user_id: int):
    entrate, uscite, totale_entrate, totale_uscite, saldo = estratto_conto(user_id)
    
    wb_user = Workbook()
    ws_user = wb_user.active
    ws_user.title = "Estratto Conto"
    
    ws_user.append(["Tipo", "Importo"])
    
    for m in entrate:
        ws_user.append(["Entrata", m])
    for m in uscite:
        ws_user.append(["Uscita", m])
    
    ws_user.append([])
    ws_user.append(["Totale Entrate", totale_entrate])
    ws_user.append(["Totale Uscite", totale_uscite])
    ws_user.append(["Saldo Finale", saldo])
    
    filename = f"estratto_conto_{user_id}.xlsx"
    wb_user.save(filename)
    return filename

# Comandi del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Sono TotalX Estratto Conto Bot Avanzato.\n"
        "Comandi:\n"
        "/add numero - aggiunge un'entrata\n"
        "/subtract numero - aggiunge un'uscita\n"
        "/total - mostra il saldo totale\n"
        "/report - mostra l'estratto conto dettagliato\n"
        "/export - ricevi un file Excel con il tuo estratto conto"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = int(context.args[0])
        user_id = update.message.from_user.id
        salva_movimento(user_id, value)
        _, _, _, _, saldo = estratto_conto(user_id)
        await update.message.reply_text(f"Entrata registrata: +{value}\nSaldo attuale: {saldo}")
    except (IndexError, ValueError):
        await update.message.reply_text("Errore! Usa /add numero, esempio /add 100")

async def subtract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = int(context.args[0])
        user_id = update.message.from_user.id
        salva_movimento(user_id, -value)
        _, _, _, _, saldo = estratto_conto(user_id)
        await update.message.reply_text(f"Uscita registrata: -{value}\nSaldo attuale: {saldo}")
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

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    filename = crea_file_excel_utente(user_id)
    with open(filename, "rb") as file:
        await update.message.reply_document(file, filename=filename)

# Funzione principale
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("subtract", subtract))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("export", export))

    print("Bot avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
