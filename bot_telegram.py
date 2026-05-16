import os
import telebot
from google import genai

# --- BUSCADOR INTELIGENTE DE CLAVES ---
def buscar_clave_gemini():
    # Buscamos todas las variantes que Railway suele inventar
    opciones = [
        os.getenv("GEMINI_KEY"),
        os.getenv("GÉMINIS_KEY"),
        os.getenv("GEMINIS_KEY"),
        os.getenv("GÉMINI_KEY")
    ]
    for valor in opciones:
        if valor:
            return valor.strip()
    return None

# Buscamos el Token (que ya te funciona) y la Key
TOKEN = os.getenv("TOKEN_BOT") or os.getenv("BOT_TOKEN")
G_KEY = buscar_clave_gemini()

bot = telebot.TeleBot(TOKEN)

# --- CONFIGURACIÓN DE IA ---
client = None
if G_KEY:
    try:
        client = genai.Client(api_key=G_KEY)
        print("✅ IA configurada correctamente.")
    except Exception as e:
        print(f"❌ Error de configuración: {e}")

@bot.message_handler(func=lambda message: True)
def chat(message):
    if client:
        try:
            # Importante: Usar el modelo flash para evitar errores de permisos
            response = client.models.generate_content(
                model="gemini-1.5-flash", 
                contents=message.text
            )
            bot.reply_to(message, response.text)
        except Exception as e:
            print(f"Error en Gemini: {e}")
            bot.reply_to(message, f"Error de IA: Revisa si tu clave de Google AI Studio está activa.")
    else:
        bot.reply_to(message, "No tengo configurada la clave de Gemini (G_KEY es None).")

if TOKEN:
    bot.polling(none_stop=True)
