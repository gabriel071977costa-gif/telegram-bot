import os
from datetime import datetime
import pytz
import requests
import yfinance as yf

# 1. Configurar la hora de Argentina
argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")
hora_actual = datetime.now(argentina_tz)
hora = hora_actual.hour
minuto = hora_actual.minute

# 2. Lista COMPLETA de todas las acciones del Panel Líder del Merval
tickers = [
    "ALUA.BA", "BBAR.BA", "BMA.BA", "BYMA.BA", "CEPU.BA", "COME.BA", 
    "EDN.BA", "GGAL.BA", "IRSA.BA", "LOMA.BA", "METR.BA", "MIRG.BA", 
    "PAMP.BA", "SUPV.BA", "TECO2.BA", "TGNO4.BA", "TGSU2.BA", "TRAN.BA", 
    "TXAR.BA", "VALO.BA", "YPFD.BA"
]

def enviar_telegram(mensaje):
    TOKEN = os.environ["TOKEN_BOT"]
    CHAT_ID = os.environ["CHAT_ID"]
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# CASO A: Mensaje de Apertura (10:50 AM)
if hora == 10 and minuto >= 45:
    noticia_texto = ""
    try:
        ggal = yf.Ticker("GGAL.BA")
        news = ggal.news
        if news:
            noticia_texto = f"📰 *Noticia destacada:* [{news[0]['title']}]({news[0]['link']})"
    except Exception:
        pass
    
    mensaje_apertura = (
        "🔔 *¡BUENOS DÍAS! EL MERCADO ESTÁ POR ABRIR* 🔔\n\n"
        "🚀 Prepará tus pantallas. En 10 minutos arranca la rueda del Merval.\n"
        "👀 Agendate las alertas horarias para no perderte ninguna oportunidad hoy.\n\n"
    )
    if noticia_texto:
        mensaje_apertura += noticia_texto + "\n"
        
    enviar_telegram(mensaje_apertura)

# CASO B: Alertas Horarias y Resumen Final (11:05 AM hasta las 17:00 PM)
else:
    variaciones = {}
    for ticker in tickers:
        try:
            asset = yf.Ticker(ticker)
            hist = asset.history(period="2d") 
            if len(hist) >= 2:
                precio_anterior = hist['Close'].iloc[-2]
                precio_actual = hist['Close'].iloc[-1]
                rendimiento = ((precio_actual - precio_anterior) / precio_anterior) * 100
                variaciones[ticker.replace(".BA", "")] = rendimiento
        except Exception:
            continue

    top_5 = sorted(variaciones.items(), key=lambda x: x[1], reverse=True)[:5]

    if hora == 17:
        mensaje = "🏁 *CIERRE DE MERCADO | Resumen Final del Día* 🏁\n\n"
        mensaje += "Así terminaron las 5 acciones que más ganaron hoy:\n\n"
    else:
        mensaje = f"📊 *Merval | Top 5 Mayores Subas ({hora}:{minuto:02d} hs):*\n\n"

    for i, (ticker, var) in enumerate(top_5, 1):
        emoji = "🟢" if var >= 0 else "🔴"
        signo = "+" if var >= 0 else ""
        mensaje += f"{i}. *{ticker}* {emoji} {signo}{var:.2f}%\n"

    if hora == 17:
        mensaje += "\n👏 ¡Fin de la jornada financiera! Mañana volvemos con más."
    else:
        mensaje += "\n📈 _Actualización horaria automática._"

    enviar_telegram(mensaje)
