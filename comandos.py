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
    texto = texto.strip().lower()

    # --------------------------------------------------------
    # /ayuda → lista de comandos disponibles
    # --------------------------------------------------------
    if texto == "/ayuda":
        enviar_a_telegram(chat_id,
            "📖 <b>Comandos disponibles</b>\n\n"
            "📊 /estado → Posiciones abiertas y capital actual\n"
            "📈 /historial → Últimas 5 operaciones realizadas\n"
            "🌱 /agro → Resumen de activos agro\n"
            "📡 /activos → Lista de activos que opera el bot\n"
            "🔍 /ypf → Info de YPF\n"
            "🔍 /btc → Info de Bitcoin\n"
            "⚙️ /ping → Verificar que Ruk está activo\n"
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
                entrada  = pos.get("precio_entrada", 0)
                inversion = pos.get("inversion_usd", 0)
                fecha    = pos.get("fecha_entrada", "?")
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
            f"💰 Capital disponible: <b>${capital:.2f}</b>\n"
            f"{emoji} Ganancia/Pérdida: <b>${ganancia:+.2f}</b>\n"
            f"📂 Posiciones abiertas:\n{bloque_pos}\n"
            f"──────────────────────\n"
            f"🕐 Última actualización: {ultima_act}"
        )

    # --------------------------------------------------------
    # /historial → últimas 5 operaciones del historial
    # --------------------------------------------------------
    elif texto == "/historial":
        estado = leer_json_github("estado_simulacion.json")
        if not estado:
            enviar_a_telegram(chat_id, "❌ No pude leer el historial desde GitHub.")
            return

        historial = estado.get("historial", [])
        if not historial:
            enviar_a_telegram(chat_id, "📋 Sin operaciones registradas todavía.")
            return

        ultimas = historial[-5:][::-1]  # últimas 5, más reciente primero
        lineas  = ["📋 <b>ÚLTIMAS OPERACIONES</b>\n"]
        for op in ultimas:
            tipo = op.get("tipo", "?")
            sym  = op.get("symbol", "?")
            hora = op.get("hora", "?")
            if tipo == "COMPRA":
                precio    = op.get("precio", 0)
                inversion = op.get("inversion_usd", 0)
                lineas.append(f"🟢 <b>COMPRA</b> {sym} @ ${precio:.4f} | ${inversion:.2f} | {hora}")
            elif tipo == "VENTA":
                ganancia = op.get("ganancia_usd", 0)
                pct      = op.get("ganancia_pct", 0)
                motivo   = op.get("motivo", "señal")
                emoji    = "📈" if ganancia >= 0 else "📉"
                lineas.append(f"🔴 <b>VENTA</b> {sym} {emoji} ${ganancia:+.2f} ({pct:+.2f}%) | {motivo} | {hora}")

        enviar_a_telegram(chat_id, "\n".join(lineas))

    # --------------------------------------------------------
    # /agro → resumen de activos agro desde cache
    # --------------------------------------------------------
    elif texto == "/agro":
        cache = leer_json_github("cache_finanzas.json")
        if not cache:
            enviar_a_telegram(chat_id, "❌ No pude leer el cache desde GitHub.")
            return

        msg = "🌱 <b>ACTIVOS AGRO</b>\n──────────────────────\n"
        for symbol in ["CRES.BA", "MOLA.BA", "LEDE.BA"]:
            datos = cache.get(symbol, [])
            if datos:
                ultimo = datos[-1]["cierre"]
                cierres = [d["cierre"] for d in datos if d["cierre"] > 0]
                promedio = round(sum(cierres) / len(cierres), 2)
                msg += f"<b>{symbol}</b>: ${ultimo} | Promedio 2a: ${promedio}\n"
            else:
                msg += f"<b>{symbol}</b>: Sin datos\n"
        enviar_a_telegram(chat_id, msg)

    # --------------------------------------------------------
    # /activos → lista de activos
    # --------------------------------------------------------
    elif texto == "/activos":
        msg = "📡 <b>Activos que opera el bot</b>\n"
        for symbol, nombre in ACTIVOS.items():
            msg += f"  • {symbol} → {nombre}\n"
        enviar_a_telegram(chat_id, msg)

    # --------------------------------------------------------
    # /ypf y /btc → info rápida desde cache
    # --------------------------------------------------------
    elif texto in ["/ypf", "/btc"]:
        symbol = "YPFD.BA" if texto == "/ypf" else "BTC-USD"
        cache  = leer_json_github("cache_finanzas.json")
        if not cache:
            enviar_a_telegram(chat_id, "❌ No pude leer el cache desde GitHub.")
            return
        datos = cache.get(symbol, [])
        if datos:
            ultimo   = datos[-1]["cierre"]
            cierres  = [d["cierre"] for d in datos if d["cierre"] > 0]
            promedio = round(sum(cierres) / len(cierres), 2)
            nombre   = ACTIVOS.get(symbol, symbol)
            enviar_a_telegram(chat_id,
                f"📡 <b>{nombre}</b>\n"
                f"Último cierre: <b>${ultimo}</b>\n"
                f"Promedio 2 años: ${promedio}"
            )
        else:
            enviar_a_telegram(chat_id, f"❌ Sin datos para {symbol}")

    # --------------------------------------------------------
    # /balance → capital disponible y ganancia total
    # --------------------------------------------------------
    elif texto == "/balance":
        estado = leer_json_github("estado_simulacion.json")
        if not estado:
            enviar_a_telegram(chat_id, "❌ No pude leer el balance desde GitHub.")
            return
        capital  = estado.get("capital_usd", 0)
        cap_ini  = estado.get("capital_inicial", 1000)
        ganancia = round(capital - cap_ini, 2)
        emoji    = "🟢" if ganancia >= 0 else "🔴"
        enviar_a_telegram(chat_id,
            f"📊 <b>BALANCE SIMULADO</b>\n"
            f"💰 Capital disponible: <b>${capital:.2f}</b>\n"
            f"🏦 Capital inicial: ${cap_ini:.2f}\n"
            f"{emoji} Ganancia/Pérdida: <b>${ganancia:+.2f}</b>"
        )
      elif comando_base == "/analizar":
           ejecutar_analisis(argumento, chat_id)

      elif comando_base == "/invertir":
           ejecutar_inversion(argumento, chat_id)
    
    # --------------------------------------------------------
    # /reset → NO lo hacemos desde bt porque requeriría
    # escribir en el repo de bY, lo cual es peligroso.
    # Informamos que se hace desde GitHub Actions.
    # --------------------------------------------------------
    elif texto == "/reset":
        enviar_a_telegram(chat_id,
            "⚙️ <b>Reset no disponible desde Telegram</b>\n\n"
            "Para reiniciar la simulación, borrá manualmente "
            "<code>estado_simulacion.json</code> desde el repo "
            "<b>bot-yahooFinanzas</b> en GitHub.\n"
            "En el próximo ciclo bY creará uno nuevo con $1000."
        )

    # --------------------------------------------------------
    # /ping → verificar que bt está activo
    # --------------------------------------------------------
    elif texto == "/ping":
        enviar_a_telegram(chat_id, "✅ Ruk activo y conectado 🤖")

    # --------------------------------------------------------
    # Comando desconocido
    # --------------------------------------------------------
    else:
        enviar_a_telegram(chat_id, "❓ Comando no reconocido. Usá /ayuda para ver la lista.")
