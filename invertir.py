import os
import datetime
import requests

# Importamos la función mágica que ya tenés hecha en tu bot_yahooFinanzas.py
from bot_yahooFinanzas import resumen_estadistico

TOKEN = os.getenv("TOKEN_BOT")

def enviar_a_telegram(chat_id, texto):
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] No se pudo enviar mensaje a Telegram: {e}")

def ejecutar_inversion(argumento, chat_id, lista_activos):
    """
    Busca los datos reales del activo mediante yfinance y simula la pre-inversión
    """
    if not argumento:
        enviar_a_telegram(chat_id, "⚠️ <b>Uso correcto:</b> <code>/invertir [ACTIVO]</code>\nEjemplo: <code>/invertir YPFD</code> o <code>/invertir BTC</code>")
        return

    # 1. Mapeo inteligente de alias rápidos
    mapeo_tickers = {}
    for ticker in lista_activos.keys():
        alias_corto = ticker.replace(".BA", "").replace("-USD", "").replace("=F", "")
        mapeo_tickers[alias_corto] = ticker
        mapeo_tickers[ticker] = ticker
    
    # Forzamos compatibilidad con YPF local
    mapeo_tickers["YPF"] = "YPFD.BA"
    
    ticker_real = mapeo_tickers.get(argumento)

    if not ticker_real or ticker_real not in lista_activos:
        enviar_a_telegram(chat_id, f"❌ El activo <b>{argumento}</b> no está registrado en tus listas de seguimiento.")
        return

    nombre_activo = lista_activos.get(ticker_real, ticker_real)
    enviar_a_telegram(chat_id, f"⏳ <i>Ruk consultando Yahoo Finanzas para {ticker_real}... Espere por favor.</i>")

    # 2. Llamamos directamente a TU FUNCIÓN en bot_yahooFinanzas.py
    # NOTA: Como en tu bot_yahooFinanzas.py actual el diccionario ACTIVOS solo tiene 6 elementos,
    # pasamos temporalmente el ticker_real mapeado para verificar si yfinance responde.
    datos_vivos = resumen_estadistico(ticker_real)

    if not datos_vivos:
        # Intento de contingencia si no estaba en el diccionario estático de tu bot_yahooFinanzas.py
        try:
            import yfinance as yf
            ticker_yf = yf.Ticker(ticker_real)
            hist = ticker_yf.history(period="2y")
            if not hist.empty:
                datos_vivos = {
                    "ultimo_cierre": round(float(hist["Close"].iloc[-1]), 2),
                    "promedio_cierre": round(float(hist["Close"].mean()), 2)
                }
        except Exception as e:
            print(f"Error alternativo yfinance: {e}")

    if not datos_vivos:
        enviar_a_telegram(chat_id, f"❌ No se pudieron obtener datos en tiempo real de Yahoo Finanzas para <code>{ticker_real}</code>.")
        return

    # 3. Extraemos los resultados devueltos por la lógica
    precio_actual = datos_vivos["ultimo_cierre"]
    promedio_2a   = datos_vivos["promedio_cierre"]
    moneda        = "USD" if "-USD" in ticker_real or ticker_real in ["SPY", "NVDA", "GC=F"] else "$"

    # 4. Construcción del informe estético para Telegram
    enviar_a_telegram(chat_id,
        f"🔍 <b>DATOS DE PRE-INVERSIÓN EN VIVO</b>\n"
        f"──────────────────────\n"
        f"📈 Activo: <b>{nombre_activo}</b>\n"
        f"🏷️ Ticker Yahoo: <code>{ticker_real}</code>\n"
        f"💵 Último precio: <b>{moneda} {precio_actual:.2f}</b>\n"
        f"📊 Promedio (2 años): {moneda} {promedio_2a:.2f}\n"
        f"──────────────────────\n"
        f"🟢 <b>Simulación Exitosa:</b>\n"
        f"Se calculó la entrada para operar con precios reales de mercado."
    )
