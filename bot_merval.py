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

# 2. Listas separadas de acciones
panel_lider = [
    "ALUA.BA", "BBAR.BA", "BMA.BA", "BYMA.BA", "CEPU.BA", "COME.BA", 
    "EDN.BA", "GGAL.BA", "IRSA.BA", "LOMA.BA", "METR.BA", "MIRG.BA", 
    "PAMP.BA", "SUPV.BA", "TECO2.BA", "TGNO4.BA", "TGSU2.BA", "TRAN.BA", 
    "TXAR.BA", "VALO.BA", "YPFD.BA"
]

panel_general = [
    "AGRO.BA", "AUSO.BA", "BHIP.BA", "BOLT.BA", "BPAT.BA", "CADO.BA", 
    "CAPX.BA", "CARC.BA", "CECO2.BA", "CELU.BA", "CGPA2.BA", "CTIO.BA", 
    "DGCU2.BA", "FERR.BA", "FIPL.BA", "GAMI.BA", "GCDI.BA", "GRIM.BA", 
    "HAVA.BA", "INVJ.BA", "LEDE.BA", "LONG.BA", "MOLA.BA", "MOLI.BA", 
    "MORI.BA", "OEST.BA", "PATA.BA", "RICH.BA", "RIGO.BA", "SAMI.BA", "SEMI.BA"
]

def enviar_telegram(mensaje):
    TOKEN = os.environ["TOKEN_BOT"]
    CHAT_ID = os.environ["CHAT_ID"]
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# --- FUNCIÓN PARA OBTENER VARIACIONES DE UN PANEL ---
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
            
        except Exception:
            continue
    return resultados

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

# CASO B: Alertas Horarias y Resumen Final (Dividido por Paneles)
else:
    # Procesar ambos paneles por separado
    datos_lider = procesar_panel(panel_lider)
    datos_general = procesar_panel(panel_general)

    # Definir el título del mensaje según la hora
    if hora == 17:
        mensaje = "🏁 *CIERRE DE MERCADO | Resumen Final del Día* 🏁\n\n"
    else:
        mensaje = f"📊 *Merval | Top Subas ({hora}:{minuto:02d} hs)*\n\n"

    # --- AGREGAR PANEL LÍDER (Top 3) ---
    mensaje += "💎 *PANEL LÍDER (Top 3):*\n"
    if datos_lider:
        top_lider = sorted(datos_lider.items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (ticker, var) in enumerate(top_lider, 1):
            emoji = "🟢" if var >= 0 else "🔴"
            signo = "+" if var >= 0 else ""
            mensaje += f"{i}. *{ticker}* {emoji} {signo}{var:.2f}%\n"
    else:
        mensaje += "Sin datos disponibles.\n"

    mensaje += "\n"

    # --- AGREGAR PANEL GENERAL (Top 3) ---
    mensaje += "🏭 *PANEL GENERAL (Top 3):*\n"
    if datos_general:
        top_general = sorted(datos_general.items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (ticker, var) in enumerate(top_general, 1):
            emoji = "🟢" if var >= 0 else "🔴"
            signo = "+" if var >= 0 else ""
            mensaje += f"{i}. *{ticker}* {emoji} {signo}{var:.2f}%\n"
    else:
        mensaje += "Sin datos disponibles.\n"

    # Cierre del pie de mensaje
    if hora == 17:
        mensaje += "\n👏 ¡Fin de la jornada financiera! Mañana volvemos."
    else:
        mensaje += "\n📈 _Actualización automática por paneles._"

    # Enviar si hay algún dato cargado
    if datos_lider or datos_general:
        enviar_telegram(mensaje)
