import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openpyxl import Workbook, load_workbook

# Carica variabili d'ambiente
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# File Excel principale
FILE_EXCEL = "estratto_conto.xlsx"

# Lista operatori iniziale (puoi aggiungere ID Telegram)
operatori = []

# Carica o crea il file Excel
if os.path.exists(FILE_EXCEL):
    wb = load_workbook(FILE_EXCEL)
    ws = wb.active
else:
    wb = Workbook()
    ws = wb.active
    ws.append(["user_id", "nome", "movimento", "tipo"])  # intestazioni
    wb.save(FILE_EXCEL)

# Funzioni di utilità
def salva_movimento(user_id: int, nome: str, valore: int, tipo: str):
    ws.append([user_id, nome, valore, tipo])
    wb.save(FILE_EXCEL)

def leggi_movimenti():
    movimenti = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        movimenti.append({"user_id": row[0], "nome": row[1], "valore": row[2], "tipo": row[3]})
    return movimenti

def calcola_totale():
    movimenti = leggi_movimenti()
    totale = sum([m["valore"] for m in movimenti])
    return totale

def estratto_conto():
    movimenti = leggi_movimenti()
    report = "📄 Estratto Conto\n\n"
    if not movimenti:
        report += "Nessun movimento registrato."
        return report
    
    for m in movimenti:
        report += f"{m['nome']} - {m['tipo']}: {m['valore']}\n"
    
    report += f"\nSaldo totale: {calcola_totale()}"
    return report

def resetta_cassa():
    wb_new = Workbook()
    ws_new = wb_new.active
    ws_new.append(["user_id", "nome", "movimento", "tipo"])
    wb_new.save(FILE_EXCEL)
    global ws
    ws = wb_new.active

# Controlla se utente è operatore
def is_operatore(user_id: int):
    return user_id in operatori

# Comandi bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Bot Contabilità Condivisa.\n"
        "Comandi:\n"
        "/a numero - aggiungi entrata\n"
        "/s numero - sottrai uscita\n"
        "/c numero - registra commissioni/tasse\n"
        "/total - saldo totale\n"
        "/stop - chiusura cassa e reset\n"
        "/add_operatore @username - aggiungi operatore\n"
        "/rm_operatore @username - rimuovi operatore"
    )

async def a(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    nome = update.message.from_user.username or update.message.from_user.first_name
    if not is_operatore(user_id):
        await update.message.reply_text("Non sei autorizzato.")
        return
    try:
        valore = int(context.args[0])
        salva_movimento(user_id, nome, valore, "entrata")
        await update.message.reply_text(f"Entrata registrata: +{valore}\nSaldo totale: {calcola_totale()}")
    except (IndexError, ValueError):
        await update.message.reply_text("Errore! Usa /a numero")

async def s(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    nome = update.message.from_user.username or update.message.from_user.first_name
    if not is_operatore(user_id):
        await update.message.reply_text("Non sei autorizzato.")
        return
    try:
        valore = int(context.args[0])
        salva_movimento(user_id, nome, -valore, "uscita")
        await update.message.reply_text(f"Uscita registrata: -{valore}\nSaldo totale: {calcola_totale()}")
    except (IndexError, ValueError):
        await update.message.reply_text("Errore! Usa /s numero")

async def c(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    nome = update.message.from_user.username or update.message.from_user.first_name
    if not is_operatore(user_id):
        await update.message.reply_text("Non sei autorizzato.")
        return
    try:
        valore = int(context.args[0])
        salva_movimento(user_id, nome, -valore, "commissioni/tasse")
        await update.message.reply_text(f"Commissioni registrate: -{valore}\nSaldo totale: {calcola_totale()}")
    except (IndexError, ValueError):
        await update.message.reply_text("Errore! Usa /c numero")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Saldo totale: {calcola_totale()}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_operatore(user_id):
        await update.message.reply_text("Non sei autorizzato.")
        return
    report = estratto_conto()
    await update.message.reply_text(f"🔒 Chiusura cassa\n\n{report}")
    resetta_cassa()

async def add_operatore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_operatore(user_id):
        await update.message.reply_text("Non sei autorizzato.")
        return
    try:
        username = context.args[0].replace("@", "")
        # Qui dovresti tradurre username in user_id reale, per semplicità aggiungiamo username come "id fittizio"
        operatori.append(username)
        await update.message.reply_text(f"Operatore {username} aggiunto.")
    except IndexError:
        await update.message.reply_text("Errore! Usa /add_operatore @username")

async def rm_operatore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_operatore(user_id):
        await update.message.reply_text("Non sei autorizzato.")
        return
    try:
        username = context.args[0].replace("@", "")
        if username in operatori:
            operatori.remove(username)
            await update.message.reply_text(f"Operatore {username} rimosso.")
        else:
            await update.message.reply_text(f"{username} non è operatore.")
    except IndexError:
        await update.message.reply_text("Errore! Usa /rm_operatore @username")

# Funzione principale
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("a", a))
    app.add_handler(CommandHandler("s", s))
    app.add_handler(CommandHandler("c", c))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("add_operatore", add_operatore))
    app.add_handler(CommandHandler("rm_operatore", rm_operatore))

    print("Bot avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
