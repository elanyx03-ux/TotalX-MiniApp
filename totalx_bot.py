from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Variabili globali per tenere traccia dei movimenti
movimenti = []
totale = 0

# Funzione per aggiungere
def aggiungi(update: Update, context: CallbackContext):
    global totale, movimenti
    if len(context.args) != 1:
        update.message.reply_text("Usa /+numero (es: /+5)")
        return
    try:
        valore = int(context.args[0])
        totale += valore
        movimenti.append(f"+{valore}")
        update.message.reply_text(f"Ho aggiunto {valore}. Totale attuale: {totale}")
    except ValueError:
        update.message.reply_text("Inserisci un numero valido.")

# Funzione per sottrarre
def sottrai(update: Update, context: CallbackContext):
    global totale, movimenti
    if len(context.args) != 1:
        update.message.reply_text("Usa /-numero (es: /-3)")
        return
    try:
        valore = int(context.args[0])
        totale -= valore
        movimenti.append(f"-{valore}")
        update.message.reply_text(f"Ho sottratto {valore}. Totale attuale: {totale}")
    except ValueError:
        update.message.reply_text("Inserisci un numero valido.")

# Funzione per mostrare il totale
def mostra_totale(update: Update, context: CallbackContext):
    global totale
    update.message.reply_text(f"Totale: {totale}")

# Funzione per il report
def report(update: Update, context: CallbackContext):
    global totale, movimenti
    if not movimenti:
        update.message.reply_text("Non ci sono movimenti.")
        return
    testo = "Movimenti:\n" + "\n".join(movimenti) + f"\nTotale: {totale}"
    update.message.reply_text(testo)

# Funzione help
def help_command(update: Update, context: CallbackContext):
    testo = (
        "/+numero → aggiungi un numero\n"
        "/-numero → sottrai un numero\n"
        "/tot → mostra il totale\n"
        "/report → mostra tutti i movimenti"
    )
    update.message.reply_text(testo)

# Setup del bot
def main():
    TOKEN = "7380640185:AAG2BsPcTxA1rV91yv2nZuyOQ5O6jdCLsIo"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("+", aggiungi))
    dp.add_handler(CommandHandler("-", sottrai))
    dp.add_handler(CommandHandler("tot", mostra_totale))
    dp.add_handler(CommandHandler("report", report))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
