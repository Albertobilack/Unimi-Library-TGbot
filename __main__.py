# todo: 
# - 
# - menu a scelta per prenota book_biblio e conferma avvenuta prenotazione
# - menu a scelta per freespot_biblio e display elenco in rispota
# - prenotazione con CF e email invece che USERNAME e PASSWORD -> come gestisco freespot senza il login?
# - integrazione DB 
# - integrazione di altre biblioteche, e scrape dei loro ID, per ora consideriamo solo BICF


import argparse
from easystaff import Easystaff
from datetime import datetime
from typing import Final
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler
#import asyncio
import config


TOKEN: Final = config.TOKEN
USERNAME: config.TESTUSERNAME
PASSWORD: config.TESTPASSWORD

BOT_USERNAME: Final = '@albeunimibot'

#da aggiugnere elenco comandi e spiegazione
async def startCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('3 funzioni principali: LIST FREESPOT e BOOK')

#lista tutti i posti disponibli dei giorni successivi della biblioteca selezionata,
#elenca anche fasce non disponibili perché prenotate 
async def listCommand(update: Update, context: ContextTypes.DEFAULT_TYPE)  -> None:
    risposta = list_biblio()
    await update.message.reply_text(risposta)

#prentotazione posto in biblioteca della biblio selezionata, giorno selezionato, piano selezionato, fascia selezionata
async def bookCommand(update: Update, context: ContextTypes.DEFAULT_TYPE)  -> None:
    await update.message.reply_text('book')

#elenco delle sole fasce orarie libere nella biblioteca selezionata per l'utente che deve essere loggato, non elenca 
#fasce non disponibili perché già prenotate
async def freespotCommand(update: Update, context: ContextTypes.DEFAULT_TYPE)  -> None:
    await update.message.reply_text('freespot')

#spiegazione dettagliata di ogni comando, DEVE essere presente per TGBOT
async def helpCommand(update: Update, context: ContextTypes.DEFAULT_TYPE)  -> None:
    await update.message.reply_text('help')

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE)  -> None:
    print(f'Update {update} caused error {context.error}')


#NON NECESSITA DI LOGIN, DA LEVARE ANCHE a
def list_biblio(): 
    a = Easystaff()
    #a.login(LOGIN.username, LOGIN.password)

    biblio = a.get_biblio(1)
    biblio = (biblio["schedule"])
    risposta = "PIANO TERRA"
    for i in biblio:
        risposta += "\ngiorno: " + str(i)
        contatore = 0
        for j in biblio[i]:
            risposta += "\n" + str(contatore) + " : " + str(j)
            contatore += 1

    biblio = a.get_biblio(2)
    if biblio["prima_disp"] == None:
        risposta += "\n\n0 POSTI PRENOTABILI AL PRIMO PIANO"
    else:
        biblio = (biblio["schedule"])
        risposta += "\n\nPRIMO PIANO"
        for i in biblio:
            risposta += "\ngiorno: " + str(i)
            contatore = 0
            for j in biblio[i]:
                risposta += "\n" + str(contatore) + str(contatore) + str(j)
                contatore += 1

    return risposta

#necessita di login
def freespot_biblio(args): 
    a = Easystaff()
    a.login(args.u, args.p)

    biblio = a.get_freespot(1)
    biblio = (biblio["schedule"])
    data = list(biblio.keys())[0]
    biblio = (biblio[data])
    print("PIANO TERRA, giorno:", data)
    for orario, slot in biblio.items():
        if slot["disponibili"] > 0:
            print(orario, "presente prenotazione:", slot["reserved"])


#necessita di login
def book_biblio(args):
    TS_DAY = datetime.strptime(args.day, "%Y-%m-%d")
    TS_ORAINZIO = datetime.strptime(args.inizo, "%Y-%m-%d")
    TS_ORAFINE = datetime.strptime(args.fine, "%Y-%m-%d")
    TS_INIZIO = TS_DAY+TS_ORAINZIO
    TS_FINE = TS_DAY+TS_ORAFINE

    a = Easystaff()
    a.login(args.u, args.p)
    a.book_bibio(TS_INIZIO, TS_FINE)
    print("ok")
    #da definire piano, per ora preimpostato su piano terra
    #da sistemare input per orario e giorno


#da integrare e finire menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE)  -> None:

    # context.bot.send_message(
    #     update.message.from_user.id,
    #     FIRST_MENU,
    #     parse_mode=ParseMode.HTML,
    #     reply_markup=FIRST_MENU_MARKUP
    # )
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
        ],
        [InlineKeyboardButton("Option 3", callback_data="3")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please choose:", reply_markup=reply_markup)


#azioni dei vari bottoni del menu
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    query = update.callback_query

    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")


if __name__ == "__main__":
    print("starting bot")
    app = Application.builder().token(TOKEN).build()

    #comandi
    app.add_handler(CommandHandler('start', startCommand))
    app.add_handler(CommandHandler('list', listCommand))
    app.add_handler(CommandHandler('book', bookCommand))
    app.add_handler(CommandHandler('freespot', freespotCommand))
    app.add_handler(CommandHandler('help', helpCommand))


    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button))

    
    #errori
    app.add_error_handler(error)

    print('test')
    app.run_polling(poll_interval=3, allowed_updates=Update.ALL_TYPES)
