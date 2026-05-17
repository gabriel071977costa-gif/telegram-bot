# bot_binance.py
# ------------------------------------------------------------
# Lógica de inversión automática con Gemini y Binance.
# ------------------------------------------------------------

import os
import datetime
import time
from binance.client import Client
from binance.enums import *
from google import genai
from balance_diario import registrar_operacion, balance_diario

API_KEY = os.getenv("BINANCE_TEST_KEY")
API_SECRET = os.getenv("BINANCE_TEST_SECRET")

client = Client(API_KEY, API_SECRET, testnet=True)

# Sincronizar con servidor Binance
server_time = client.get_server_time()
client.TIME_OFFSET = server_time['serverTime'] - int(datetime.datetime.now().timestamp() * 1000)

# Cliente Gemini
G_KEY = os.getenv("GEMINI_KEY")
genai_client = genai.Client(api_key=G_KEY) if G_KEY else None

TOP_SYMBOLS = ["BTCUSDT","ETHUSDT","BNBUSDT","ADAUSDT","XRPUSDT","SOLUSDT","DOGEUSDT","DOTUSDT","MATICUSDT","LTCUSDT"]

def obtener_datos_historicos(symbol):
    fecha_inicio = (datetime.datetime.now() - datetime.timedelta(days=730)).strftime("%d %b %Y %H:%M:%S")
    klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, fecha_inicio)
    datos = []
    for k in klines:
        datos.append({
            "fecha": datetime.datetime.fromtimestamp(k[0]/1000).strftime("%Y-%m-%d"),
            "apertura": float(k[1]),
            "cierre": float(k[4]),
            "volumen": float(k[5])
        })
    return datos

def decision_inversion(symbol):
    datos = obtener_datos_historicos(symbol)
    prompt = f"""
    Analiza estos datos históricos de {symbol} de los últimos 2 años (día a día).
    Detecta caídas o subidas fuertes con volumen alto.
    Concluye si conviene COMPRAR o VENDER hoy para obtener ganancias.
    Datos: {datos}
    """
    if genai_client:
        respuesta = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return respuesta.text.lower()
    return "sin_decision"

def ejecutar_operacion(symbol="BTCUSDT", cantidad=0.001):
    decision = decision_inversion(symbol)
    if "comprar" in decision:
        orden = client.create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=cantidad,
            recvWindow=60000
        )
        registrar_operacion(symbol, "comprar", cantidad, float(orden["fills"][0]["price"]), float(orden["cummulativeQuoteQty"]))
        return f"✅ Compra ejecutada: {orden}"
    elif "vender" in decision:
        orden = client.create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=cantidad,
            recvWindow=60000
        )
        registrar_operacion(symbol, "vender", cantidad, float(orden["fills"][0]["price"]), float(orden["cummulativeQuoteQty"]))
        return f"✅ Venta ejecutada: {orden}"
    else:
        return "⚠️ Sin acción recomendada por Gemini."

def ciclo_diario():
    resultados = []
    for symbol in TOP_SYMBOLS:
        resultado = ejecutar_operacion(symbol, cantidad=0.001)
        resultados.append(resultado)
    return resultados
