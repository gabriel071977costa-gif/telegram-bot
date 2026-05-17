import os
import telebot
from google import genai
import time

# --- IMPORTAMOS LA LÓGICA DE INVERSIÓN ---
# Este módulo contiene la integración con Binance Testnet y Gemini
from invertir_binance import ejecutar_operacion


# --- BUSCADOR INTELIGENTE DE CLAVES (Tu lógica que funciona) ---
def buscar_clave_gemini():
    """
    Railway a veces guarda las variables con nombres distintos.
    Esta función busca todas las variantes posibles de la clave de Gemini.
    """
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

# --- CONFIGURACIÓN DE TOKENS ---
# Token del bot de Telegram (se guarda en Railway como BOT_TOKEN o TOKEN_BOT)
raw_token = os.getenv("TOKEN_BOT") or os.getenv("BOT_TOKEN")
TOKEN = raw_token.strip().replace(" ", "") if raw_token else None

# Clave de Gemini
G_KEY = buscar_clave_gemini()

# --- CONFIGURACIÓN DE CLIENTE GEMINI ---
client = None
if G_KEY:
    try:
        client = genai.Client(api_key=G_KEY)
        print("✅ IA configurada correctamente.")
    except Exception as e:
        print(f"❌ Error de configuración: {e}")

# --- INICIO DEL BOT TELEGRAM ---
if TOKEN:
    bot = telebot.TeleBot(TOKEN)
else:
    print("❌ ERROR: No se encontró el TOKEN_BOT en Railway.")
    exit(1)

# --- COMANDO /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Mensaje inicial cuando el usuario escribe /start.
    """
    bot.reply_to(message, "¡Ruk activo! Ya reconozco tus claves y estoy listo para hablar, Gabriel.")

# --- COMANDO /invertir ---
@bot.message_handler(commands=['invertir'])
def invertir_handler(message):
    """
    Ejecuta la lógica de inversión en Binance Testnet usando Gemini.
    Llama a la función ejecutar_operacion() del archivo invertir.py
    y devuelve el resultado al chat de Telegram.
    """
    resultado = ejecutar_operacion()
    bot.reply_to(message, resultado)

# --- CHAT GENERAL ---
@bot.message_handler(func=lambda message: True)
def chat(message):
    """
    Responde cualquier mensaje usando Gemini.
    Si Gemini falla, intenta con otro modelo como fallback.
    """
    if client:
        try:
            # Modelo más moderno y rápido
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=message.text
            )
            bot.reply_to(message, response.text)
        except Exception as e:
            # Fallback automático si falla el modelo 2.5
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=message.text
                )
                bot.reply_to(message, response.text)
            except Exception as e2:
                print(f"Error en Gemini: {e2}")
                bot.reply_to(message, "Error de IA: revisa si tu clave de Google AI Studio está activa o si superaste el límite gratuito.")
    else:
        bot.reply_to(message, "No tengo configurada la clave de Gemini (G_KEY es None).")

# --- INICIO SEGURO DEL BOT ---
if __name__ == "__main__":
    try:
        print("🚀 Limpiando conexión previa...")
        bot.remove_webhook()
        time.sleep(2)  # Pausa para evitar error 409 Conflict
        print("🚀 Ruk iniciando polling... ¡Ya puedes escribirle!")
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"❌ Error al arrancar el bot: {e}")
