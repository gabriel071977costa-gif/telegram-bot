import os
import telebot # Usaremos esta que es más ligera para Railway
import google.generativeai as genai

# Configuración de Tokens
TOKEN = os.getenv("TOKEN_BOT")
GEMINI_KEY = os.getenv("GEMINI_KEY") # Saca tu clave en aistudio.google.com

# Configurar la IA
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"Hola {message.from_user.first_name}, soy Ruk, el bot de Gabriel. ¿De qué quieres hablar hoy?")

@bot.message_handler(func=lambda message: True)
def chat_natural(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    texto_usuario = message.text

    # 1. Guardar en el archivo (Recuerda que en Railway esto es temporal)
    with open("conversaciones.txt", "a", encoding="utf-8") as f:
        f.write(f"{user_name}: {texto_usuario}\n")

    # 2. Leer los últimos recuerdos para darle contexto a la IA
    contexto = ""
    if os.path.exists("conversaciones.txt"):
        with open("conversaciones.txt", "r", encoding="utf-8") as f:
            # Leemos las últimas 10 líneas para que no se sature
            contexto = "".join(f.readlines()[-10:])

    # 3. Pedirle a la IA que responda siendo "Ruk"
    prompt = f"Eres Ruk, un bot creado por Gabriel. Tu historial reciente es:\n{contexto}\nUsuario dice: {texto_usuario}\nResponde de forma natural y breve:"
    
    try:
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "Estoy procesando mucha info, ¡háblame de nuevo!")

bot.polling()
