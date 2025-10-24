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

# Lista operatori
operatori = set()  # verranno aggiunti con i comandi

# Carica o crea file Excel
if os.path.exists(FILE_EXCEL):
    wb = load_workbook(FILE_EXCEL)
    ws = wb.active
else:
    wb = Workbook()
    ws = wb.active
    ws.append(["user", "movimento", "tipo"])  # intestazioni
    wb.save(FILE_EXCEL)

# Funzioni utilità
def salva_movimento(user: str, valore: int, tipo: str):
    ws.append([user, valore, tipo])
    wb.save(FILE_EXCEL)

def leggi_movimenti():
    movimenti = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        movimenti.append(row)
    return movimenti

def estratto_conto():
    entrate = [m[1] for m in leggi_movimenti() if m[1] > 0]
    uscite = [m[1] for m in leggi_movimenti() if m[1] < 0]
    commissioni = [m[1] for m in leggi_movimenti() if m[2] == "commissione"]
    totale_entrate = sum(entrate)
    totale_uscite = sum(uscite)
    totale_commissioni = sum(commissioni)
    saldo = totale_entrate + totale_uscite - totale_commissioni
    return entrate, uscite, commissioni, totale_entrate, totale_uscite, totale_commissioni, saldo

def crea_file_excel():
    entrate, uscite, commissioni, totale_entrate, totale_uscite, totale_commissioni, saldo = estratto_conto()
    wb_user = Workbook()
    ws_user = wb_user.active
    ws_user.title = "Estratto Conto"
    ws_user.append(["Tipo", "Importo", "Operatore"])
    for row in leggi_movimenti():
        ws_user.append([row[2], row[1], row[0]])
    ws_user.append([])
    ws_user.append(["Totale Entrate", totale_entrate])
    ws_user.append(["Totale Uscite", totale_uscite])
    ws_user.append(["Totale Commissioni", totale_commissioni])
    ws_user.append(["Saldo Finale", saldo])
    filename = "estratto_conto_completo.xlsx"
    wb_user.save(filename)
    return filename

# Controllo operatore
def is_operatore(user: str):
    return user in operatori

# Comandi bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Sono TotalX Estratto Conto Bot Avanzato.\n"
        "Comandi:\n"
        "/a numero - aggiunge un'entrata\n"
        "/s numero - sottrae un'uscita\n"
        "/c numero - aggiunge commissione/tassa\n"
        "/total - mostra il saldo totale\n"
        "/stop - chiude la cassa e resetta\n"
        "/add_operatore @username - aggiungi operatore\n"
        "/rm_operatore @username - rimuovi operatore"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    if not is_operatore(user):
        await update.message.reply_text("Non sei autorizzato a usare questo comando.")
        return
    try:
        value = int(context.args[0])
        salva_movimento(user, value, "entrata")
        _, _, _, _, _, _, saldo = estratto_conto()
        await update.message.reply_text(f"{user} ha aggiunto +{value}\nSaldo attuale: {saldo}")
    except:
        await update.message.reply_text("Errore! Usa /a numero")

async def subtract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    if not is_operatore(user):
        await update.message.reply_text("Non sei autorizzato a usare questo comando.")
        return
    try:
        value = int(context.args[0])
        salva_movimento(user, -value, "uscita")
        _, _, _, _, _, _, saldo = estratto_conto()
        await update.message.reply_text(f"{user} ha sottratto -{value}\nSaldo attuale: {saldo}")
    except:
        await update.message.reply_text("Errore! Usa /s numero")

async def commissione(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    if not is_operatore(user):
        await update.message.reply_text("Non sei autorizzato a usare questo comando.")
        return
    try:
        value = int(context.args[0])
        salva_movimento(user, value, "commissione")
        await update.message.reply_text(f"{user} ha registrato commissione/tassa: +{value}")
    except:
        await update.message.reply_text("Errore! Usa /c numero")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, _, _, _, _, _, saldo = estratto_conto()
    await update.message.reply_text(f"Saldo totale: {saldo}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = crea_file_excel()
    with open(filename, "rb") as file:
        await update.message.reply_document(file, filename=filename)
    # Reset cassa
    wb.active.delete_rows(2, ws.max_row)
    wb.save(FILE_EXCEL)
    await update.message.reply_text("Cassa chiusa e resettata.")

async def add_operatore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    if not is_operatore(user):
        await update.message.reply_text("Non sei autorizzato a gestire operatori.")
        return
    try:
        new_user = context.args[0].replace("@","")
        operatori.add(new_user)
        await update.message.reply_text(f"Operatore @{new_user} aggiunto.")
    except:
        await update.message.reply_text("Errore! Usa /add_operatore @username")

async def rm_operatore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    if not is_operatore(user):
        await update.message.reply_text("Non sei autorizzato a gestire operatori.")
        return
    try:
        remove_user = context.args[0].replace("@","")
        operatori.discard(remove_user)
        await update.message.reply_text(f"Operatore @{remove_user} rimosso.")
    except:
        await update.message.reply_text("Errore! Usa /rm_operatore @username")

# Main
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("a", add))
    app.add_handler(CommandHandler("s", subtract))
    app.add_handler(CommandHandler("c", commissione))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("add_operatore", add_operatore))
    app.add_handler(CommandHandler("rm_operatore", rm_operatore))
    print("Bot avviato...")
    app.run_polling()

if __name__ == "__main__":
    # Inserisci il tuo username come primo operatore
    operatori.add("elanyx")  
    main()
