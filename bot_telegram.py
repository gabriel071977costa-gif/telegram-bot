import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = os.getenv("BOT_TOKEN")

# Saludo inicial con /start
def start(update, context):
    user = update.message.from_user
    update.message.reply_text(f"Hola {user.first_name}, Hola soy Ruk el bot de Gabriel. ¿Con quién hablo?")

# Conversación libre
def conversar(update, context):
    user = update.message.from_user
    texto = update.message.text.lower()

    # Guardar conversación en archivo
    with open("conversaciones.txt", "a", encoding="utf-8") as f:
        f.write(f"{user.id} ({user.first_name}): {texto}\n")

    # Respuestas personalizadas
    if "gabriel" in texto:
        update.message.reply_text("¡Sí! Sos mi creador Gabriel.")
        # Buscar recuerdos previos
        try:
            with open("conversaciones.txt", "r", encoding="utf-8") as f:
                lineas = f.readlines()
            recuerdos = [l for l in lineas if str(user.id) in l and "fútbol" in l]
            if recuerdos:
                update.message.reply_text("Me acuerdo que ayer hablamos de fútbol.")
        except FileNotFoundError:
            update.message.reply_text("Todavía no tengo recuerdos guardados.")
    elif "fútbol" in texto:
        update.message.reply_text("¡Qué bueno! Voy a recordar que te gusta hablar de fútbol.")
    else:
        update.message.reply_text(f"Hola {user.first_name}, gracias por contarme eso.")

# Configuración del bot
updater = Updater(TOKEN)
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(MessageHandler(Filters.text, conversar))

updater.start_polling()
updater.idle()
