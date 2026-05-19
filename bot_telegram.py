# bot_telegram.py
# ------------------------------------------------------------
# Bot de Telegram que controla todo con Gemini.
# Incluye:
#   - Lógica de claves y fallback de Gemini (tu versión estable)
#   - Comando /balance con CSV real
#   - Ciclo automático diario (sin Binance en Render)
#   - Comando /id para obtener tu chat ID
#   - Preguntas específicas (ej: nombre del bot) importadas de preguntas.py
# ------------------------------------------------------------

import os
import telebot
import threading
import time
from preguntas import es_preguntas
from google import genai

# --- IMPORTAMOS LA LÓGICA DE BALANCE ---
from balance_diario import balance_diario, calcular_balance, balance_hoy

# --- BUSCADOR INTELIGENTE DE CLAVES ---
def buscar_clave_gemini():
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
    print("❌ ERROR: No se encontró el TOKEN_BOT en Render.")
    exit(1)

# --- CHAT_ID FIJO PARA CICLO AUTOMÁTICO ---
CHAT_ID = os.getenv("CHAT_ID") or "TU_CHAT_ID_AQUI"  # reemplazá con tu chat ID real

# --- COMANDO /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Ruk activo! Ya reconozco tus claves y estoy listo para hablar, Gabriel.")

# --- COMANDO /balance ---
@bot.message_handler(commands=['balance'])
def balance_handler(message):
    ganancia_total = calcular_balance()
    ganancia_hoy = balance_hoy()
    bot.reply_to(message, f"📊 Ganancia acumulada: {ganancia_total:.2f} USDT\n📅 Ganancia de hoy: {ganancia_hoy:.2f} USDT")

# --- COMANDO /id ---
@bot.message_handler(commands=['id'])
def send_id(message):
    bot.reply_to(message, f"Tu chat ID es: {message.chat.id}")

# --- CHAT GENERAL (Gemini conversacional + preguntas específicas) ---
@bot.message_handler(func=lambda message: True)
def chat(message):
    texto = message.text

    # Primero chequeamos si es una pregunta de nombre
    if es_pregunta(texto):
        bot.reply_to(message, "Me llamo Ruk 🤖, EL bot inteligente de Gabriel.")
        return  # IMPORTANTE: salir aquí para que no pase a Gemini

    # Si no, seguimos con Gemini
    if client:
        try:
            # Primer intento con gemini-flash-lite-latest
            response = client.models.generate_content(
                model="models/gemini-flash-lite-latest",
                contents=texto
            )
            bot.reply_to(message, response.text)
        except Exception as e:
            print(f"Error en Gemini (flash-lite-latest): {e}")
            try:
                # Fallback automático a gemini-2.0-flash-lite
                response = client.models.generate_content(
                    model="models/gemini-2.0-flash-lite",
                    contents=texto
                )
                bot.reply_to(message, response.text)
            except Exception as e2:
                print(f"Error en Gemini (2.0-flash-lite): {e2}")
                bot.reply_to(message, "⚠️ Sin cuota disponible en Gemini. Revisá tu plan o billing en Google AI Studio.")
    else:
        bot.reply_to(message, "No tengo configurada la clave de Gemini (G_KEY es None).")

# --- CICLO AUTOMÁTICO DIARIO ---
def modo_automatico():
    while True:
        # 🚫 Binance deshabilitado en Render
        # resultados = ciclo_diario()   # comentado porque Render no usa Binance
        resumen = "Binance deshabilitado en Render"
        ganancia_hoy = balance_hoy()

        mensaje = f"⏱️ Resultados diarios:\n{resumen}\n📅 Ganancia del día: {ganancia_hoy:.2f} USDT"

        # Si el mensaje es demasiado largo, lo partimos en bloques de 4000 caracteres
        max_len = 4000
        for i in range(0, len(mensaje), max_len):
            bot.send_message(CHAT_ID, mensaje[i:i+max_len])

        time.sleep(86400)  # espera 1 día

threading.Thread(target=modo_automatico, daemon=True).start()

# --- INICIO SEGURO DEL BOT ---
if __name__ == "__main__":
    try:
        print("🚀 Limpiando conexión previa...")
        bot.remove_webhook()
        time.sleep(2)
        print("🚀 Ruk iniciando polling... ¡Ya puedes escribirle!")
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"❌ Error al arrancar el bot: {e}")
