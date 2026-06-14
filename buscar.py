import os
import requests

# --- IMPORTAMOS LAS LISTAS Y DICCIONARIOS DE TUS ARCHIVOS NATIVOS ---
from bot_merval import panel_lider, panel_general
from bot_yahooFinanzas import ACTIVOS as ACTIVOS_YFINANZAS

TOKEN = os.getenv("TOKEN_BOT")

def enviar_a_telegram(chat_id, texto):
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
    try: 
        requests.post(url, data=payload, timeout=10)
    except Exception as e: 
        print(f"[ERROR Telegram Buscar]: {e}")

def ejecutar_busqueda(argumento, chat_id):
    if not argumento:
        enviar_a_telegram(chat_id, "⚠️ <b>Uso correcto:</b> <code>/buscar [nombre de empresa o activo]</code>\nEjemplo: <code>/buscar galicia</code> o <code>/buscar oro</code>")
        return

    # Pasamos la búsqueda a minúsculas para que no importe si escribís con mayúsculas
    termino_busqueda = argumento.lower()

    # --- CONSTRUCCIÓN DEL UNIVERSO DE BÚSQUEDA ---
    activos_maestro = {}
    for ticker, desc in ACTIVOS_YFINANZAS.items(): 
        activos_maestro[ticker] = desc
        
    for ticker in panel_lider:
        if ticker not in activos_maestro:
            nombre_limpio = ticker.replace(".BA", "")
            activos_maestro[ticker] = f"{nombre_limpio} (Panel Líder Merval)"
            
    for ticker in panel_general:
        if ticker not in activos_maestro:
            nombre_limpio = ticker.replace(".BA", "")
            activos_maestro[ticker] = f"{nombre_limpio} (Panel General Merval)"

    # Forzamos compatibilidad manual de YPF por su ticker compuesto
    activos_maestro["YPFD.BA"] = "YPF Clase D (Energía Argentina)"

    # --- ESCÁNER DE COINCIDENCIAS ---
    resultados = []
    for ticker, descripcion in activos_maestro.items():
        # Buscamos si el término está en el ticker (ej: GGAL) o en la descripción (ej: Galicia)
        if termino_busqueda in ticker.lower() or termino_busqueda in descripcion.lower():
            # Sacamos el formato limpio para que el usuario solo tenga que tocar el código
            alias_corto = ticker.replace(".BA", "").replace("-USD", "").replace("=F", "")
            if alias_corto == "YPFD": alias_corto = "YPF" # Compatibilidad corta para YPF
            
            resultados.append(f"🔍 <b>{descripcion}</b>\n• Comando: <code>/analizar {alias_corto}</code>")

    # --- RESPUESTA A TELEGRAM ---
    if not resultados:
        enviar_a_telegram(chat_id, f"❌ No encontré ningún activo que coincida con '<b>{argumento}</b>' en tus listas actuales.")
    else:
        # Unimos los resultados con una línea divisoria
        separador = "\n──────────────────────\n"
        mensaje_final = f"✨ <b>RESULTADOS PARA: '{argumento}'</b>\n──────────────────────\n" + separador.join(resultados)
        enviar_a_telegram(chat_id, mensaje_final)
