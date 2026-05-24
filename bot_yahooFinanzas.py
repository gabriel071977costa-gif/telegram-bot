# bot_yahooFinanzas.py
# ------------------------------------------------------------
# Módulo mínimo para exponer activos y resumen estadístico
# ------------------------------------------------------------

# Diccionario de activos
ACTIVOS = {
    "YPF.BA": "YPF (Energía Argentina - Pesos)",
    "BTC-USD": "Bitcoin USD (Cripto)",
    "SPY": "S&P 500 ETF (Exterior)",
    "CRES.BA": "Cresud (Agro)",
    "MOLA.BA": "Molinos Agro (Agro)",
    "LEDE.BA": "Ledesma (Agro)"
}

# Función mínima para devolver datos de un activo
def resumen_estadistico(symbol: str):
    """
    Devuelve un resumen estadístico simulado para el activo.
    En producción podés reemplazar con yfinance o tu lógica real.
    """
    if symbol not in ACTIVOS:
        return None

    # Datos simulados (ejemplo)
    return {
        "ultimo_cierre": 100.0,   # valor ficticio
        "promedio_cierre": 95.0   # valor ficticio
    }
