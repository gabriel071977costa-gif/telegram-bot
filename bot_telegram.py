# bot_telegram.py
# ------------------------------------------------------------
# Bot de Telegram que controla todo con Gemini y Binance.
# Incluye:
#   - Lógica de claves y fallback de Gemini (tu versión estable)
#   - Comando /invertir manual
#   - Comando /balance con CSV real
#   - Ciclo automático diario con 10 criptos principales
# ------------------------------------------------------------

import os
import telebot
import threading
import time
from google import genai

# --- IMPORTAMOS LA LÓGICA DE INVERSIÓN ---
from bot_binance import ciclo_diario, ejecutar_operacion
from balance_diario import balance_diario, calcular_balance

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
    print("❌ ERROR: No se encontró el TOKEN_BOT en Railway.")
    exit(1)

# --- COMANDO /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Ruk activo! Ya reconozco tus claves y estoy listo para hablar, Gabriel.")

# --- COMANDO /invertir manual ---
@bot.message_handler(commands=['invertir'])
def invertir_handler(message):
    resultado = ejecutar_operacion("BTCUSDT", cantidad=0.001)
    bot.reply_to(message, resultado)

# --- COMANDO /balance ---
@bot.message_handler(commands=['balance'])
def balance_handler(message):
    ganancia_total = calcular_balance()
    ganancia_hoy = balance_diario()
    bot.reply_to(message, f"📊 Ganancia acumulada: {ganancia_total:.2f} USDT\n📅 Ganancia de hoy: {ganancia_hoy:.2f} USDT")

# --- CHAT GENERAL (Gemini conversacional) ---
@bot.message_handler(func=lambda message: True)
def chat(message):
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=message.text
            )
            bot.reply_to(message, response.text)
        except Exception as e:
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash", 
                    contents=message.text
                )
                bot.reply_to(message, response.text)
            except Exception as e2:
                print(f"Error en Gemini: {e2}")
                bot.reply_to(message, "Error de IA: revisa si tu clave de Google AI Studio está activa o si superaste el límite gratuito.")
    else:
        bot.reply_to(message, "No tengo configurada la clave de Gemini (G_KEY es None).")

# --- CICLO AUTOMÁTICO DIARIO ---
def modo_automatico():
    while True:
        resultados = ciclo_diario()
        resumen = "\n".join(resultados)
        ganancia_hoy = balance_diario()
        bot.send_message(message.chat.id, f"⏱️ Resultados diarios:\n{resumen}\n📅 Ganancia del día: {ganancia_hoy:.2f} USDT")
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
