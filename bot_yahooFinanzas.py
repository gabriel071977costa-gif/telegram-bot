import yfinance as yf

ACTIVOS = {
    "YPF.BA": "YPF (Energía Argentina - Pesos)",
    "BTC-USD": "Bitcoin USD (Cripto)",
    "SPY": "S&P 500 ETF (Exterior)",
    "CRES.BA": "Cresud (Agro)",
    "MOLA.BA": "Molinos Agro (Agro)",
    "LEDE.BA": "Ledesma (Agro)"
}

def resumen_estadistico(symbol: str):
    """
    Devuelve un resumen estadístico real desde Yahoo Finanzas:
    último cierre y promedio de 2 años.
    """
    if symbol not in ACTIVOS:
        return None

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2y")

        if hist.empty:
            return None

        ultimo_cierre = hist["Close"].iloc[-1]
        promedio_cierre = hist["Close"].mean()

        return {
            "ultimo_cierre": round(float(ultimo_cierre), 2),
            "promedio_cierre": round(float(promedio_cierre), 2)
        }
    except Exception as e:
        print("Error en yfinance:", e)
        return None
