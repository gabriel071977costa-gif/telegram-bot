import os
import telebot
from google import genai

# 1. BUSCADOR DE VARIABLES (Busca las 4 variantes que mencionas)
# Esto evita el error NoneType porque siempre intentará encontrar algo
def buscar_token():
    # Buscamos en todas las formas que Railway ha inventado en tu panel
    opciones = [
        os.getenv("TOKEN_BOT"),
        os.getenv("BOT_TOKEN"),
        os.getenv("BOT DE TOKEN"),  # Por si vuelve a aparecer con espacios
        os.getenv("TOKEN")
    ]
    for valor in opciones:
        if valor:
            # .strip() quita espacios invisibles y .replace(" ", "") quita espacios en medio
            return valor.strip().replace(" ", "")
    return None

def buscar_gemini():
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

# Asignamos los valores limpios
TOKEN = buscar_token()
G_KEY = buscar_gemini()

# 2. VALIDACIÓN ANTES DE INICIAR (Para que no explote la línea 9)
if TOKEN is None:
    print("❌ ERROR: No se encontró el TOKEN en ninguna de las 4 variantes.")
    # Creamos un token falso temporal para que el código no dé error de compilación
    # pero el bot no funcionará hasta que Railway detecte la variable.
    TOKEN = "dummy_token" 

bot = telebot.TeleBot(TOKEN)

# 3. CONFIGURACIÓN DE IA (google-genai)
client = None
if G_KEY:
    try:
        client = genai.Client(api_key=G_KEY)
        print("✅ IA de Gemini configurada.")
    except Exception as e:
        print(f"❌ Error en Gemini: {e}")

# --- Handlers ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "¡Ruk activo! He revisado todas las variantes de las claves.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=message.text
            )
            bot.reply_to(message, response.text)
        except Exception as e:
            bot.reply_to(message, "Error al procesar con IA.")
    else:
        bot.reply_to(message, "Vivo, pero sin GEMINI_KEY.")

# --- Inicio Seguro ---
if TOKEN != "dummy_token":
    print("🚀 Iniciando el polling...")
    bot.polling(none_stop=True)
else:
    print("⚠️ El bot no inició porque el TOKEN sigue siendo None en Railway.")
