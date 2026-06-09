import os
from datetime import datetime
import pytz
import requests
import yfinance as yf

# --- CONFIGURACIÓN DE HORA ARGENTINA ---
argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")
hora_actual = datetime.now(argentina_tz)
hora = hora_actual.hour
minuto = hora_actual.minute
print("DEBUG: Hora Argentina detectada:", hora, ":", minuto)

# --- LISTAS DE ACCIONES ---
panel_lider = [
    "ALUA.BA","BBAR.BA","BMA.BA","BYMA.BA","CEPU.BA","COME.BA","EDN.BA","GGAL.BA",
    "IRSA.BA","LOMA.BA","METR.BA","MIRG.BA","PAMP.BA","SUPV.BA","TECO2.BA","TGNO4.BA",
    "TGSU2.BA","TRAN.BA","TXAR.BA","VALO.BA","YPFD.BA"
]

panel_general = [
    "AGRO.BA","AUSO.BA","BHIP.BA","BOLT.BA","BPAT.BA","CADO.BA","CAPX.BA","CARC.BA",
    "CECO2.BA","CELU.BA","CGPA2.BA","CTIO.BA","DGCU2.BA","FERR.BA","FIPL.BA","GAMI.BA",
    "GCDI.BA","GRIM.BA","HAVA.BA","INVJ.BA","LEDE.BA","LONG.BA","MOLA.BA","MOLI.BA",
    "MORI.BA","OEST.BA","PATA.BA","RICH.BA","RIGO.BA","SAMI.BA","SEMI.BA"
]

# --- FUNCIÓN DE ENVÍO A TELEGRAM ---
def enviar_telegram(mensaje):
    TOKEN = os.environ["TOKEN_BOT"]
    CHAT_ID = os.environ["CHAT_ID"]
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    r = requests.post(url, data=payload)
    print("DEBUG: Mensaje enviado desde bot_merval.py a Telegram")  # <-- agregado
    print("DEBUG: Telegram status:", r.status_code, r.text)

# --- FUNCIÓN PARA PROCESAR PANEL ---
def procesar_panel(lista_tickers):
    resultados = {}
    for ticker in lista_tickers:
        try:
            asset = yf.Ticker(ticker)
            hist = asset.history(period="2d")
            if hist.empty or len(hist) < 2:
                continue
            precio_anterior = hist['Close'].iloc[-2]
            precio_actual = hist['Close'].iloc[-1]
            if precio_anterior == 0:
                continue
            rendimiento = ((precio_actual - precio_anterior) / precio_anterior) * 100
            resultados[ticker.replace(".BA", "")] = rendimiento
        except Exception as e:
            print(f"DEBUG: Error procesando {ticker}: {e}")
            continue
    return resultados

# --- BLOQUE DE EJECUCIÓN (siempre que GitHub Actions dispare) ---
datos_lider = procesar_panel(panel_lider)
datos_general = procesar_panel(panel_general)

if hora == 17:
    mensaje = "🏁 *CIERRE DE MERCADO | Resumen Final del Día* 🏁\n\n"
else:
    mensaje = f"📊 *Merval | Top Subas ({hora}:{minuto:02d} hs)*\n\n"

mensaje += "💎 *BOT MERVAL :*\n"
mensaje += "💎 *PANEL LÍDER (Top 3):*\n"
if datos_lider:
    top_lider = sorted(datos_lider.items(), key=lambda x: x[1], reverse=True)[:3]
    for i, (ticker, var) in enumerate(top_lider, 1):
        emoji = "🟢" if var >= 0 else "🔴"
        signo = "+" if var >= 0 else ""
        mensaje += f"{i}. *{ticker}* {emoji} {signo}{var:.2f}%\n"
else:
    mensaje += "Sin datos disponibles.\n"

mensaje += "\n🏭 *PANEL GENERAL (Top 3):*\n"
if datos_general:
    top_general = sorted(datos_general.items(), key=lambda x: x[1], reverse=True)[:3]
    for i, (ticker, var) in enumerate(top_general, 1):
        emoji = "🟢" if var >= 0 else "🔴"
        signo = "+" if var >= 0 else ""
        mensaje += f"{i}. *{ticker}* {emoji} {signo}{var:.2f}%\n"
else:
    mensaje += "Sin datos disponibles.\n"

if hora == 17:
    mensaje += "\n👏 ¡Fin de la jornada financiera! Mañana volvemos."
else:
    mensaje += "\n📈 _Actualización automática por paneles._"

if not datos_lider and not datos_general:
    mensaje = "🔧 Prueba de conexión Merval Bot (feriado). El bot está activo y conectado."

enviar_telegram(mensaje)
