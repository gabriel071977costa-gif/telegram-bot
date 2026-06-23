 bot_telegram.py
# ------------------------------------------------------------
# Bot de Telegram que controla todo con Gemini.
# Incluye:
#   - Lógica de claves y fallback de Gemini (tu versión estable)
#   - Comando /balance con CSV real
#   - Ciclo automático diario (sin Binance en Render) [DESACTIVADO]
#   - Comando /id para obtener tu chat ID
#   - Preguntas específicas (ej: nombre del bot) importadas de preguntas.py
#   - Webhook con Flask para Render (plan gratuito)
#   - Integración con comandos.py para manejar /agro, /ayuda, etc.
#   - Publicación de señales en el canal de Telegram (Traiding Señales)
# ------------------------------------------------------------

import os
import telebot
import threading
import time
from preguntas import es_preguntas
from google import genai
from comandos import procesar_comando   # <-- agregado
from flask import Flask, request

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

# --- ACA CONECTA AL CANAL ---
# CANAL_ID es el chat_id del canal "Traiding Señales" donde el bot (Ruk)
# fue agregado como administrador con permiso de publicar mensajes.
# Se puede sobreescribir desde una variable de entorno en Render (CANAL_ID),
# o usar el username público del canal como valor por defecto.
CANAL_ID = os.getenv("CANAL_ID") or "@traidingSenalesArg"

def publicar_en_canal(texto):
    """Publica un mensaje en el canal de señales (Traiding Señales)."""
    try:
        bot.send_message(CANAL_ID, texto)
        print(f"✅ Publicado en canal: {texto[:50]}...")
    except Exception as e:
        print(f"❌ Error al publicar en canal: {e}")

# --- COMANDO /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "¡Ruk activo! Ya reconozco tus claves y estoy listo para hablar, Gabriel.")

# --- COMANDO /balance ---
@bot.message_handler(commands=['balance'])
def balance_handler(message):
    ganancia_total = calcular_balance()
    ganancia_hoy = balance_hoy()
    bot.send_message(message.chat.id, f"📊 Ganancia acumulada: {ganancia_total:.2f} USDT\n📅 Ganancia de hoy: {ganancia_hoy:.2f} USDT")

# --- COMANDO /id ---
@bot.message_handler(commands=['id'])
def send_id(message):
    bot.send_message(message.chat.id, f"Tu chat ID es: {message.chat.id}")

# --- CHAT GENERAL (Gemini conversacional + preguntas específicas + comandos) ---
@bot.message_handler(func=lambda message: True)
def chat(message):
    texto = message.text

    # 1. Si es un comando, lo procesamos en comandos.py
    if texto.startswith("/"):
        procesar_comando(texto, message.chat.id)   # <-- integración con comandos.py
        return

    # 2. Si es una pregunta de nombre
    if es_preguntas(texto):
        bot.send_message(message.chat.id, "Me llamo Ruk 🤖, EL bot inteligente de Gabriel.")
        return

    # 3. Si no, seguimos con Gemini
    if client:
        try:
            response = client.models.generate_content(
                model="models/gemini-flash-lite-latest",
                contents=texto
            )
            bot.send_message(message.chat.id, response.text)
        except Exception as e:
            print(f"Error en Gemini (flash-lite-latest): {e}")
            try:
                response = client.models.generate_content(
                    model="models/gemini-2.0-flash-lite",
                    contents=texto
                )
                bot.send_message(message.chat.id, response.text)
            except Exception as e2:
                print(f"Error en Gemini (2.0-flash-lite): {e2}")
                bot.send_message(message.chat.id, "⚠️ Sin cuota disponible en Gemini. Revisá tu plan o billing en Google AI Studio.")
    else:
        bot.send_message(message.chat.id, "No tengo configurada la clave de Gemini (G_KEY es None).")

# --- CICLO AUTOMÁTICO DIARIO (DESACTIVADO) ---
# def modo_automatico():
#     while True:
#         resumen = "Binance deshabilitado en Render"
#         ganancia_hoy = balance_hoy()
#         mensaje = f"⏱️ Resultados diarios:\n{resumen}\n📅 Ganancia del día: {ganancia_hoy:.2f} USDT"
#         bot.send_message(CHAT_ID, mensaje)
#         time.sleep(86400)
#
# --MANDA SMS A TELEGRAM---
# threading.Thread(target=modo_automatico, daemon=True).start()

# --- WEBHOOK CON FLASK ---
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    print("DEBUG: Mensaje recibido por bot_telegram.py vía webhook")  # <-- agregado
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# --- ENDPOINT PARA RECIBIR SEÑALES DE bot_yahooFinanzas.py ---
# bot_yahooFinanzas.py corre en GitHub Actions y no tiene un proceso
# corriendo permanentemente, así que en lugar de "conectarse" directo,
# le hace un POST a este endpoint con el mensaje ya armado.
# Ese mensaje se reenvía automáticamente al canal "Traiding Señales".
@app.route('/senal', methods=['POST'])
def recibir_senal():
    data = request.get_json()
    if not data or "mensaje" not in data:
        return "Falta el campo 'mensaje'", 400

    mensaje = data["mensaje"]
    publicar_en_canal(mensaje)   # <-- ACA CONECTA AL CANAL
    return "OK", 200

if __name__ == "__main__":
    try:
        print("🚀 Configurando webhook en Render...")
        bot.remove_webhook()
        bot.set_webhook(url=os.getenv("WEBHOOK_URL"))
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    except Exception as e:
        print(f"❌ Error al arrancar el bot: {e}")
