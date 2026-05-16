import os
import telebot
from google import genai

# Leemos las variables exactas
TOKEN = os.getenv("BOT_TOKEN")
G_KEY = os.getenv("GÉMINI_KEY")

# Validación para que tú veas el error en los Logs si algo falta
if not TOKEN:
    print("❌ ERROR: BOT_TOKEN no encontrado.")
if not G_KEY:
    print("⚠️ AVISO: GEMINI_KEY no encontrada. El bot no tendrá IA.")

# Iniciar Bot
bot = telebot.TeleBot(TOKEN)
# Iniciar IA (usando la librería nueva que pusiste en requirements)
client = genai.Client(api_key=G_KEY) if G_KEY else None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "¡Ruk ha renacido! Proyecto limpio y funcionando.")

@bot.message_handler(func=lambda message: True)
def responder(message):
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=message.text
            )
            bot.reply_to(message, response.text)
        except Exception as e:
            bot.reply_to(message, "Error al pensar con la IA.")
    else:
        bot.reply_to(message, "Estoy vivo, pero no tengo configurada mi IA.")

bot.polling()
