import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openpyxl import Workbook, load_workbook
from datetime import datetime

# Carica token da .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# File Excel
FILE_EXCEL = os.path.join(os.getcwd(), "estratto_conto.xlsx")

# ✅ Assicura che il file Excel esista
def ensure_excel():
    if not os.path.exists(FILE_EXCEL):
        wb = Workbook()
        ws = wb.active
        ws.title = "Movimenti"
        ws.append(["Data", "Ora", "Utente", "Tipo", "Importo"])  # intestazioni
        wb.save(FILE_EXCEL)

# 🧾 Salva movimento nel file
def salva_movimento(username: str, tipo: str, valore: float):
    ensure_excel()
    wb = load_workbook(FILE_EXCEL)
    ws = wb.active

    data = datetime.now().strftime("%d/%m/%Y")
    ora = datetime.now().strftime("%H:%M:%S")

    ws.append([data, ora, username, tipo, valore])
    wb.save(FILE_EXCEL)

# 📖 Leggi movimenti
def leggi_movimenti():
    ensure_excel()
    wb = load_workbook(FILE_EXCEL)
    ws = wb.active
    movimenti = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        movimenti.append(row)
    return movimenti

# 💰 Calcola saldo totale
def calcola_saldo():
    movimenti = leggi_movimenti()
    return sum([m[4] for m in movimenti]) if movimenti else 0

# ♻️ Reset file
def reset_excel():
    if os.path.exists(FILE_EXCEL):
        os.remove(FILE_EXCEL)
    ensure_excel()

# ↩️ Undo ultima operazione
def undo_ultima_operazione():
    ensure_excel()
    wb = load_workbook(FILE_EXCEL)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) > 1:
        ws.delete_rows(len(rows))
        wb.save(FILE_EXCEL)
        return rows[-1]
    return None

# 🚀 --- COMANDI DEL BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Ciao! Sono *TotalX Bot* 💰\n\n"
        "Comandi disponibili:\n"
        "/add numero → aggiunge un'entrata\n"
        "/subtract numero → aggiunge un'uscita\n"
        "/total → mostra il saldo totale\n"
        "/report → mostra gli ultimi movimenti\n"
        "/export → invia il file Excel\n"
        "/undo → elimina l'ultima operazione\n"
        "/reset → azzera tutto e ricrea il file",
        parse_mode="Markdown"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = float(context.args[0])
        username = update.message.from_user.first_name
        salva_movimento(username, "Entrata", value)
        saldo = calcola_saldo()
        await update.message.reply_text(f"✅ {username} ha aggiunto +{value:.2f}€\n💰 Totale attuale: {saldo:.2f}€")
    except (IndexError, ValueError):
        await update.message.reply_text("❗ Usa: /add 100")

async def subtract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = float(context.args[0])
        username = update.message.from_user.first_name
        salva_movimento(username, "Uscita", -value)
        saldo = calcola_saldo()
        await update.message.reply_text(f"💸 {username} ha speso -{value:.2f}€\n💰 Totale attuale: {saldo:.2f}€")
    except (IndexError, ValueError):
        await update.message.reply_text("❗ Usa: /subtract 50")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saldo = calcola_saldo()
    await update.message.reply_text(f"💰 Totale complessivo: {saldo:.2f}€")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movimenti = leggi_movimenti()
    if not movimenti:
        await update.message.reply_text("📂 Nessun movimento registrato.")
        return

    report_lines = []
    for m in movimenti[-20:]:
        data, ora, utente, tipo, importo = m
        report_lines.append(f"{data} {ora} | {utente} | {tipo} {importo:.2f}€")

    saldo = calcola_saldo()
    testo = "📄 Ultimi movimenti:\n\n" + "\n".join(report_lines) + f"\n\n💰 Totale: {saldo:.2f}€"
    await update.message.reply_text(testo)

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_excel()
    with open(FILE_EXCEL, "rb") as file:
        await update.message.reply_document(file, filename="estratto_conto.xlsx")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_excel()
    await update.message.reply_text("♻️ Tutto azzerato! Nuovo file creato.")

async def undo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last = undo_ultima_operazione()
    if last:
        data, ora, utente, tipo, importo = last
        saldo = calcola_saldo()
        await update.message.reply_text(
            f"🗑️ Eliminata ultima operazione:\n{data} {ora} | {utente} | {tipo} {importo:.2f}€\n💰 Totale ora: {saldo:.2f}€"
        )
    else:
        await update.message.reply_text("⚠️ Nessuna operazione da eliminare.")

# MAIN
def main():
    ensure_excel()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("subtract", subtract))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("undo", undo))

    print("🤖 Bot avviato correttamente su Termux!")
    app.run_polling()

if __name__ == "__main__":
    main()
