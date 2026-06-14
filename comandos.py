# ============================================================
# COMANDOS TELEGRAM
# Escucha y responde a comandos enviados desde el chat
# Se integra con bot_yahooFinanzas.py
# ============================================================

import os
import json
import base64
import requests

from analizar import ejecutar_analisis
from invertir import ejecutar_inversion
from buscar import ejecutar_busqueda

# ------------------------------------------------------------
# CONFIGURACIÓN
# Estas variables vienen de Render → Environment
# ------------------------------------------------------------
TOKEN        = os.getenv("TOKEN_BOT")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "gabriel071977costa-gif/bot-yahooFinanzas")

ACTIVOS = {
    "YPF.BA":  "YPF (Energía Argentina - Pesos)",
    "BTC-USD": "Bitcoin USD (Cripto)",
    "SPY":     "S&P 500 ETF (Exterior)",
    "NVDA":    "NVIDIA (Exterior)",
    "GC=F":    "Oro Futuros (Refugio)",
    "CRES.BA": "Cresud (Agro)",
    "MOLA.BA": "Molinos Agro (Agro)",
    "LEDE.BA": "Ledesma (Agro)"
}

# ------------------------------------------------------------
# FUNCIÓN: enviar mensaje a Telegram
# ------------------------------------------------------------
def enviar_a_telegram(chat_id, texto):
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        print(f"[ERROR Telegram] {r.text}")

# ------------------------------------------------------------
# FUNCIÓN: leer un archivo JSON del repo privado de bY
# Usa la API de GitHub con el token de lectura
# ------------------------------------------------------------
def leer_json_github(nombre_archivo):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{nombre_archivo}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            contenido = r.json().get("content", "")
            datos = json.loads(base64.b64decode(contenido).decode("utf-8"))
            return datos
        else:
            print(f"[ERROR GitHub] {r.status_code}: {r.text}")
            return None
    except Exception as e:
        print(f"[ERROR] leer_json_github: {e}")
        return None

# ------------------------------------------------------------
# FUNCIÓN PRINCIPAL: procesar comandos
# Llamada desde bot_telegram.py con el texto y el chat_id
# ------------------------------------------------------------
def procesar_comando(texto, chat_id):
    texto_limpio = texto.strip()
    
    # Separamos el comando del argumento (ej: /analizar ggal -> comando_base="/analizar", argumento="ggal")
    partes = texto_limpio.split(maxsplit=1)
    comando_base = partes[0].lower() if partes else ""
    argumento = partes[1].lower() if len(partes) > 1 else ""

    # Usamos texto en minúsculas para los comandos puros sin argumentos
    texto = texto_limpio.lower()

    # --------------------------------------------------------
    # /ayuda → lista de comandos disponibles
    # --------------------------------------------------------
    if texto == "/ayuda":
        enviar_a_telegram(chat_id,
            "📖 <b>Comandos disponibles</b>\n\n"
            "📡 /activos → Lista de activos que opera el bot\n"
            "🌱 /agro → Resumen de activos agro\n"
            "📊 /analizar [activo] → Analiza si conviene comprar o vender\n"
            "🔍 /btc → Info de Bitcoin\n"
            "🔍 /buscar [nombre] → Busca el código exacto de una empresa\n"
            "📊 /estado → Posiciones abiertas y capital actual\n"
            "📈 /historial → Últimas 5 operaciones realizadas\n"
            "🚀 /invertir [activo] → Envía la orden de compra real a GitHub\n"
            "⚙️ /ping → Verificar que Ruk está activo\n"
            "🔍 /ypf → Info de YPF\n"
        )

    # --------------------------------------------------------
    # /estado → lee estado_simulacion.json desde GitHub
    # Muestra capital, posiciones abiertas y ganancia total
    # --------------------------------------------------------
    elif texto == "/estado":
        estado = leer_json_github("estado_simulacion.json")
        if not estado:
            enviar_a_telegram(chat_id, "❌ No pude leer el estado desde GitHub. Verificá el token.")
            return

        capital    = estado.get("capital_usd", 0)
        cap_ini    = estado.get("capital_inicial", 1000)
        posiciones = estado.get("posiciones", {})
        ultima_act = estado.get("ultima_actualizacion", "?")
        ganancia   = round(capital - cap_ini, 2)

        if posiciones:
            lineas_pos = []
            for symbol, pos in posiciones.items():
                entrada   = pos.get("precio_entrada", 0)
                inversion = pos.get("inversion_usd", 0)
                fecha     = pos.get("fecha_entrada", "?")
                lineas_pos.append(
                    f"  • <b>{symbol}</b>\n"
                    f"    Entrada: ${entrada:.4f} | Invertido: ${inversion:.2f}\n"
                    f"    Desde: {fecha}"
                )
            bloque_pos = "\n".join(lineas_pos)
        else:
            bloque_pos = "  Ninguna"

        emoji = "🟢" if ganancia >= 0 else "🔴"
        enviar_a_telegram(chat_id,
            f"📊 <b>ESTADO DE SIMULACIÓN</b>\n"
            f"──────────────────────\n"
            f"💰 Capital disponible: <b>${capital:.2f}"
