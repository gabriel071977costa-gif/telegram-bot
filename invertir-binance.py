# invertir.py
import os
from binance.client import Client
from binance.enums import *
from google import genai  # librería para Gemini, según tu setup

# Configuración Binance Testnet
API_KEY = os.getenv("CLAVE DE PRUEBA DE BINANCE")
API_SECRET = os.getenv("BINANCE_TEST_SECRET")
client = Client(API_KEY, API_SECRET, testnet=True)

# Configuración Gemini
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def decision_inversion(datos_mercado):
    """
    Usa Gemini para decidir si comprar o vender.
    """
    prompt = f"Con estos datos de mercado {datos_mercado}, ¿conviene comprar o vender?"
    respuesta = genai_client.generate_text(prompt=prompt)
    return respuesta.text.lower()

def ejecutar_operacion(symbol="BTCUSDT", cantidad=0.001):
    """
    Ejecuta operación en Binance Testnet según decisión AI.
    """
    # Ejemplo: obtener precio actual
    ticker = client.get_symbol_ticker(symbol=symbol)
    datos = {"precio": ticker["price"], "symbol": symbol}

    decision = decision_inversion(datos)

    if "comprar" in decision:
        orden = client.create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=cantidad
        )
        return f"Compra ejecutada: {orden}"
    elif "vender" in decision:
        orden = client.create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=cantidad
        )
        return f"Venta ejecutada: {orden}"
    else:
        return "Sin acción recomendada."
