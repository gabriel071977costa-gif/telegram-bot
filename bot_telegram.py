import os
from telegram.ext import Updater, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

# Saludo personalizado con el nombre del usuario
def start(update, context):
    user = update.message.from_user
    update.message.reply_text(f"Hola {user.first_name}, Ruk el bot de Gabriel.")

# Guardar información que el usuario envía con /guardar
def guardar(update, context):
    user = update.message.from_user
    texto = " ".join(context.args)
    if texto.strip() == "":
        update.message.reply_text("Tenés que escribir algo después de /guardar.")
        return
    with open("conversaciones.txt", "a", encoding="utf-8") as f:
        f.write(f"{user.id} ({user.first_name}): {texto}\n")
    update.message.reply_text("Guardé tu mensaje.")

# Recordar lo que el usuario dijo antes con /recordar
def recordar(update, context):
    user = update.message.from_user
    try:
        with open("conversaciones.txt", "r", encoding="utf-8") as f:
            lineas = f.readlines()
        recuerdos = [l for l in lineas if l.startswith(str(user.id))]
        if recuerdos:
            update.message.reply_text("Esto me contaste antes:\n" + "".join(recuerdos))
        else:
            update.message.reply_text("Todavía no me contaste nada.")
    except FileNotFoundError:
        update.message.reply_text("Todavía no tengo recuerdos.")

# Configuración del bot
updater = Updater(TOKEN)
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("guardar", guardar))
updater.dispatcher.add_handler(CommandHandler("recordar", recordar))

updater.start_polling()
updater.idle()
