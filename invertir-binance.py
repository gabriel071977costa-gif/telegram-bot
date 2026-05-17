# invertir-binance.py
# ------------------------------------------------------------
# Este módulo maneja la lógica de inversión del bot Ruk.
# Se conecta a Binance Testnet usando las claves guardadas en Railway
# y usa Gemini para analizar datos históricos y decidir comprar o vender.
# ------------------------------------------------------------

import os
from binance.client import Client
from binance.enums import *
from google import genai
import datetime

# ------------------------------------------------------------
# CONFIGURACIÓN DE CLAVES (Railway)
# Las claves se guardan en Railway como variables de entorno:
# BINANCE_TEST_KEY = <tu API Key>
# BINANCE_TEST_SECRET = <tu API Secret>
# ------------------------------------------------------------
API_KEY = os.getenv("BINANCE_TEST_KEY")
API_SECRET = os.getenv("BINANCE_TEST_SECRET")

# Cliente Binance Testnet
client = Client(API_KEY, API_SECRET, testnet=True)

# Cliente Gemini
G_KEY = os.getenv("GEMINI_KEY")
genai_client = genai.Client(api_key=G_KEY) if G_KEY else None

# ------------------------------------------------------------
# FUNCIÓN: obtener datos históricos
# Descarga velas (candlesticks) de los últimos 2 años, intervalo diario.
# ------------------------------------------------------------
def obtener_datos_historicos(symbol="BTCUSDT"):
    # Fecha de inicio: hace 2 años
    fecha_inicio = (datetime.datetime.now() - datetime.timedelta(days=730)).strftime("%d %b %Y %H:%M:%S")
    # Velas diarias
    klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, fecha_inicio)
    
    # Procesamos datos relevantes: fecha, apertura, cierre, volumen
    datos = []
    for k in klines:
        datos.append({
            "fecha": datetime.datetime.fromtimestamp(k[0]/1000).strftime("%Y-%m-%d"),
            "apertura": float(k[1]),
            "cierre": float(k[4]),
            "volumen": float(k[5])
        })
    return datos

# ------------------------------------------------------------
# FUNCIÓN: decisión de inversión con Gemini
# Analiza los datos históricos y detecta:
# - Bajadas o subidas fuertes
# - Volumen alto (muchos participantes)
# - Horarios pico de actividad
# ------------------------------------------------------------
def decision_inversion(symbol="BTCUSDT"):
    datos = obtener_datos_historicos(symbol)
    prompt = f"""
    Analiza estos datos históricos de {symbol} de los últimos 2 años (día a día).
    Detecta:
    - Bajadas o subidas fuertes con volumen alto
    - Horarios pico de actividad
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

# ------------------------------------------------------------
# FUNCIÓN: ejecutar operación
# Según la decisión de Gemini, ejecuta una orden de compra o venta en Testnet.
# ------------------------------------------------------------
def ejecutar_operacion(symbol="BTCUSDT", cantidad=0.001):
    decision = decision_inversion(symbol)
    if "comprar" in decision:
        orden = client.create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=cantidad
        )
        return f"✅ Compra ejecutada: {orden}"
    elif "vender" in decision:
        orden = client.create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=cantidad
        )
        return f"✅ Venta ejecutada: {orden}"


    if __name__ == "__main__":
    # Probar conexión y obtener saldo de prueba
    try:
        info = client.get_account()
        print("✅ Conexión correcta a Binance Testnet.")
        print("Balances:", info["balances"])
    except Exception as e:
        print("❌ Error de conexión:", e)

    else:
        return "⚠️ Sin acción recomendada por Gemini."
