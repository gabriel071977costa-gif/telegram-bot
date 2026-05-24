# ============================================================
# COMANDOS TELEGRAM
# Escucha y responde a comandos enviados desde el chat
# Se integra con bot_yahooFinanzas.py
# ============================================================

import os
import requests
from bot_yahooFinanzas import resumen_estadistico, ACTIVOS
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
            "📡 /activos → Lista de activos disponibles\n"
            "📡 /agro → Señales y acumulado de Cresud, Molinos Agro y Ledesma\n"
            "📊 /balance → Estado actual del capital simulado\n"
            "⚙️ /reset → Reinicia el estado de simulación\n"
            "🔍 /ypf → Señales solo de YPF\n"
            "🔍 /btc → Señales solo de Bitcoin\n"
            "⚙️ /ping → Verificar conexión\n"
            "➕ Podés agregar más comandos según necesidad"
        )

    elif texto == "/activos":
        mensaje = "📡 <b>Lista de activos disponibles</b>\n"
        for symbol, nombre in ACTIVOS.items():
            mensaje += f"{symbol} → {nombre}\n"
        enviar_a_telegram(mensaje)

    elif texto == "/agro":
        mensaje = "🌱 <b>AGRO — Señales y acumulado</b>\n"
        for symbol in ["CRES.BA", "MOLA.BA", "LEDE.BA"]:
            try:
                res = resumen_estadistico(symbol)
                if res:
                    mensaje += (
                        f"{symbol}: Último cierre ${res['ultimo_cierre']} | "
                        f"Promedio 2 años ${res['promedio_cierre']}\n"
                    )
                else:
                    mensaje += f"{symbol}: No se pudieron obtener datos\n"
            except Exception as e:
                mensaje += f"{symbol}: Error al obtener datos ({e})\n"
        enviar_a_telegram(mensaje)

    elif texto == "/balance":
        try:
            estado = cargar_estado()
            estado = resetear_dia_si_corresponde(estado)
            patrimonio = estado.get("patrimonio_total", 0)
            enviar_a_telegram(f"📊 Balance actual: ${patrimonio:.2f} USD")
        except Exception as e:
            enviar_a_telegram(f"📊 Error al obtener balance ({e})")

    elif texto == "/reset":
        try:
            estado = {"capital_total": 1000.0, "operaciones": []}
            guardar_estado(estado)
            enviar_a_telegram("⚙️ Estado de simulación reiniciado a $1000 USD")
        except Exception as e:
            enviar_a_telegram(f"⚙️ Error al reiniciar estado ({e})")

    elif texto == "/ypf":
        try:
            res = resumen_estadistico("YPF.BA")
            if res:
                enviar_a_telegram(
                    f"📡 YPF: Último cierre ${res['ultimo_cierre']} | "
                    f"Promedio 2 años ${res['promedio_cierre']}"
                )
            else:
                enviar_a_telegram("📡 YPF: No se pudieron obtener datos")
        except Exception as e:
            enviar_a_telegram(f"📡 YPF: Error al obtener datos ({e})")

    elif texto == "/btc":
        try:
            res = resumen_estadistico("BTC-USD")
            if res:
                enviar_a_telegram(
                    f"📡 Bitcoin: Último cierre ${res['ultimo_cierre']} | "
                    f"Promedio 2 años ${res['promedio_cierre']}"
                )
            else:
                enviar_a_telegram("📡 Bitcoin: No se pudieron obtener datos")
        except Exception as e:
            enviar_a_telegram(f"📡 Bitcoin: Error al obtener datos ({e})")

    elif texto == "/ping":
        enviar_a_telegram("✅ Bot activo y conectado")

    else:
        enviar_a_telegram("❓ Comando no reconocido. Usá /ayuda para ver la lista.")
