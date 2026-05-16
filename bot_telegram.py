import os
import telebot
from google import genai  # Nueva librería

# --- Tu lógica de claves que ya funciona ---
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("BOT DE TOKEN")
G_KEY = os.getenv("GEMINI_KEY") or os.getenv("GÉMINIS_KEY")

bot = telebot.TeleBot(TOKEN)

# --- Configuración de google-genai ---
client = None
if G_KEY:
    try:
        # Inicializamos el cliente moderno
        client = genai.Client(api_key=G_KEY)
        print("✅ IA de Gemini configurada con la nueva librería.")
    except Exception as e:
        print(f"❌ Error al configurar la IA: {e}")

# --- Handler para mensajes ---
@bot.message_handler(func=lambda message: True)
def chat_natural(message):
    if client:
        try:
            # Nueva forma de generar contenido
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=message.text
            )
            bot.reply_to(message, response.text)
        except Exception as e:
            print(f"Error en Gemini: {e}")
            bot.reply_to(message, "Tuve un error al procesar el mensaje con la IA.")
    else:
        # Respuesta si no hay clave de IA
        bot.reply_to(message, "Hola, recibí tu mensaje pero no tengo mi clave de IA configurada.")

# --- Inicio ---
if TOKEN:
    print("🚀 Bot encendido...")
    bot.polling()
