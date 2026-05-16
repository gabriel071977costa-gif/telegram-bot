import os
import telebot
from google import genai
import time

# --- BUSCADOR INTELIGENTE DE CLAVES (Tu lógica que funciona) ---
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
# Añadimos limpieza de espacios al Token por si acaso
raw_token = os.getenv("TOKEN_BOT") or os.getenv("BOT_TOKEN")
TOKEN = raw_token.strip().replace(" ", "") if raw_token else None
G_KEY = buscar_clave_gemini()

# --- CONFIGURACIÓN DE IA ---
client = None
if G_KEY:
    try:
        client = genai.Client(api_key=G_KEY)
        print("✅ IA configurada correctamente.")
    except Exception as e:
        print(f"❌ Error de configuración: {e}")

# Evitamos que el código explote si el Token no se encuentra antes de iniciar telebot
if TOKEN:
    bot = telebot.TeleBot(TOKEN)
else:
    print("❌ ERROR: No se encontró el TOKEN_BOT en Railway.")
    exit(1)

# --- RESPUESTAS DEL BOT ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Ruk activo! Ya reconozco tus claves y estoy listo para hablar, Gabriel.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    if client:
        try:
            # Usamos gemini-2.5-flash que es el más moderno y rápido
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=message.text
            )
            bot.reply_to(message, response.text)
        except Exception as e:
            # Si el 2.0 falla por algo, intenta con el 1.5-flash automáticamente
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=message.text
                )
                bot.reply_to(message, response.text)
            except Exception as e2:
                print(f"Error en Gemini: {e2}")
                bot.reply_to(message, "Error de IA: Revisa si tu clave de Google AI Studio está activa o si superaste el límite gratuito.")
    else:
        bot.reply_to(message, "No tengo configurada la clave de Gemini (G_KEY es None).")

# --- INICIO SEGURO (Evita Error 409 Conflict) ---
if __name__ == "__main__":
    try:
        print("🚀 Limpiando conexión previa...")
        bot.remove_webhook()
        time.sleep(2) # Pausa de seguridad para que Telegram cierre la sesión vieja
        print("🚀 Ruk iniciando polling... ¡Ya puedes escribirle!")
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"❌ Error al arrancar el bot: {e}")
