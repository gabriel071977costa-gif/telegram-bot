# ============================================================
# COMANDOS TELEGRAM
# Escucha y responde a comandos enviados desde el chat
# Se integra con bot_yahooFinanzas.py
# ============================================================

import os
import requests
from baseDeDatosFinanzas import resumen_estadistico, ACTIVOS
from logicaYahooFinanzas import cargar_estado, resetear_dia_si_corresponde, guardar_estado

TOKEN   = os.getenv("TOKEN_BOT")
CHAT_ID = os.getenv("CHAT_ID")

# ------------------------------------------------------------
# FUNCIÓN: enviar mensaje a Telegram
# ------------------------------------------------------------
def enviar_a_telegram(texto):
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "HTML"}
    r = requests.post(url, data=payload)
    print("Telegram status:", r.status_code)

# ------------------------------------------------------------
# FUNCIÓN: procesar comandos
# ------------------------------------------------------------
def procesar_comando(texto):
    texto = texto.strip().lower()

    if texto == "/ayuda":
        enviar_a_telegram(
            "📖 <b>Comandos disponibles</b>\n"
            "📡 /agro → Señales y acumulado de Cresud, Molinos Agro y Ledesma\n"
            "📊 /balance → Estado actual del capital simulado\n"
            "⚙️ /reset → Reinicia el estado de simulación\n"
            "🔍 /ypf → Señales solo de YPF\n"
            "🔍 /btc → Señales solo de Bitcoin\n"
            "⚙️ /ping → Verificar conexión\n"
            "➕ Podés agregar más comandos según necesidad"
        )

    elif texto == "/agro":
        mensaje = "🌱 <b>AGRO — Señales y acumulado</b>\n"
        for symbol in ["CRES.BA", "MOLA.BA", "LEDE.BA"]:
            res = resumen_estadistico(symbol)
            if res:
                mensaje += f"{symbol}: Último cierre ${res['ultimo_cierre']} | Promedio 2 años ${res['promedio_cierre']}\n"
        enviar_a_telegram(mensaje)

    elif texto == "/balance":
        estado = cargar_estado()
        estado = resetear_dia_si_corresponde(estado)
        patrimonio = estado.get("patrimonio_total", 0)
        enviar_a_telegram(f"📊 Balance actual: ${patrimonio:.2f} USD")

    elif texto == "/reset":
        estado = {"capital_total": 1000.0, "operaciones": []}
        guardar_estado(estado)
        enviar_a_telegram("⚙️ Estado de simulación reiniciado a $1000 USD")

    elif texto == "/ypf":
        res = resumen_estadistico("YPF.BA")
        if res:
            enviar_a_telegram(f"📡 YPF: Último cierre ${res['ultimo_cierre']} | Promedio 2 años ${res['promedio_cierre']}")

    elif texto == "/btc":
        res = resumen_estadistico("BTC-USD")
        if res:
            enviar_a_telegram(f"📡 Bitcoin: Último cierre ${res['ultimo_cierre']} | Promedio 2 años ${res['promedio_cierre']}")

    elif texto == "/ping":
        enviar_a_telegram("✅ Bot activo y conectado")

    else:
        enviar_a_telegram("❓ Comando no reconocido. Usá /ayuda para ver la lista.")
