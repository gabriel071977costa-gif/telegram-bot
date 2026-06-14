import os
import json
import base64
import requests
import datetime

# --- IMPORTAMOS LAS LISTAS Y DICCIONARIOS DE TUS ARCHIVOS NATIVOS ---
from bot_merval import panel_lider, panel_general
from bot_yahooFinanzas import resumen_estadistico, ACTIVOS as ACTIVOS_YFINANZAS

TOKEN        = os.getenv("TOKEN_BOT")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "gabriel071977costa-gif/bot-yahooFinanzas")

def enviar_a_telegram(chat_id, texto):
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR Telegram]: {e}")

def escribir_json_github(nombre_archivo, datos_nuevos, mensaje_commit):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{nombre_archivo}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    sha = None
    try:
        r_get = requests.get(url, headers=headers, timeout=10)
        if r_get.status_code == 200:
            sha = r_get.json().get("sha")
    except: 
        pass

    json_string = json.dumps(datos_nuevos, indent=4, ensure_ascii=False)
    contenido_base64 = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    payload = {"message": mensaje_commit, "content": contenido_base64}
    if sha: 
        payload["sha"] = sha

    try:
        r_put = requests.put(url, headers=headers, json=payload, timeout=10)
        return r_put.status_code in [200, 201]
    except:
        return False

def ejecutar_inversion(argumento, chat_id):
    if not argumento:
        enviar_a_telegram(chat_id, "⚠️ <b>Uso correcto:</b> <code>/invertir [ACTIVO]</code>\nEjemplo: <code>/invertir GGAL</code>")
        return

    # --- CONSTRUCCIÓN DEL DICCIONARIO MAESTRO EN MEMORIA ---
    # Combinamos tus listas del merval y tu diccionario de yahoo finanzas para tener soporte total
    activos_maestro = {}

    # 1. Cargamos tus activos fijos de Yahoo Finanzas (Respetando tus nombres: YPF, BTC, SPY, CRES, MOLA, LEDE)
    for ticker, desc in ACTIVOS_YFINANZAS.items():
        activos_maestro[ticker] = desc

    # 2. Sumamos dinámicamente el panel líder de bot_merval si no existía en el paso anterior
    for ticker in panel_lider:
        if ticker not in activos_maestro:
            nombre_limpio = ticker.replace(".BA", "")
            activos_maestro[ticker] = f"{nombre_limpio} (Panel Líder Merval)"

    # 3. Sumamos dinámicamente el panel general de bot_merval
    for ticker in panel_general:
        if ticker not in activos_maestro:
            nombre_limpio = ticker.replace(".BA", "")
            activos_maestro[ticker] = f"{nombre_limpio} (Panel General Merval)"

    # --- MAPEO INTELIGENTE DE ATRAVESADOS (Para escribir sin el .BA o minúsculas) ---
    mapeo_tickers = {}
    for ticker in activos_maestro.keys():
        alias_corto = ticker.replace(".BA", "").replace("-USD", "").replace("=F", "")
        mapeo_tickers[alias_corto] = ticker
        mapeo_tickers[ticker] = ticker
    
    # Soporte específico para YPF local según tu corrección
    mapeo_tickers["YPF"] = "YPFD.BA"
    if "YPF.BA" in activos_maestro and argumento.upper() == "YPF":
        ticker_real = "YPFD.BA"
    else:
        ticker_real = mapeo_tickers.get(argumento)

    # Validamos si el activo solicitado existe en el universo de tus archivos
    if not ticker_real or (ticker_real not in activos_maestro and ticker_real != "YPFD.BA"):
        enviar_a_telegram(chat_id, f"❌ El activo <b>{argumento}</b> no se encuentra en tus listas de bot_merval ni Yahoo Finanzas.")
        return

    nombre_activo = activos_maestro.get(ticker_real, "YPF Clase D (Energía Argentina)")
    enviar_a_telegram(chat_id, f"⏳ <i>Ruk consultando Yahoo Finanzas para {ticker_real} y preparando orden...</i>")

    # Llamamos a tu función nativa de bot_yahooFinanzas.py
    # Como tu función requiere que el activo esté dentro del diccionario ACTIVOS de su propio archivo,
    # si elegiste una del panel general (como HAVA.BA), la agregamos temporalmente al diccionario original en tiempo de ejecución:
    if ticker_real not in ACTIVOS_YFINANZAS:
        ACTIVOS_YFINANZAS[ticker_real] = nombre_activo

    datos_vivos = resumen_estadistico(ticker_real)

    if not datos_vivos:
        enviar_a_telegram(chat_id, f"❌ No se pudieron obtener precios en vivo de Yahoo Finanzas para <code>{ticker_real}</code>.")
        return

    precio_actual = datos_vivos["ultimo_cierre"]
    promedio_2a   = datos_vivos["promedio_cierre"]
    ahora_str     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. ESTRUCTURA CON TU NUEVA DESCRIPCIÓN REQUERIDA
    orden_nueva = {
        "symbol": ticker_real,
        "descripcion": nombre_activo,
        "precio_solicitado": precio_actual,
        "fecha_orden": ahora_str,
        "estado": "PENDIENTE",
        "origen": "Telegram Bot (Ruk)"
    }

    # Grabamos/Actualizamos el archivo orden_compra.json en el repositorio de bY
    guardado_ok = escribir_json_github("orden_compra.json", orden_nueva, f"Nueva orden desde Telegram: {ticker_real}")

    if guardado_ok:
        status_envio = "🟢 <b>Orden de simulación guardada en GitHub.</b>\n🤖 <i>bY (Actions) la procesará en su ciclo diario.</i>"
    else:
        status_envio = "🔴 <b>Error de comunicación:</b> No se pudo actualizar el archivo en tu repositorio."

    moneda = "USD" if "-USD" in ticker_real or ticker_real in ["SPY", "NVDA", "GC=F"] else "$"

    enviar_a_telegram(chat_id, 
        f"🔍 <b>DATOS DE PRE-INVERSIÓN</b>\n"
        f"──────────────────────\n"
        f"📈 Activo: <b>{nombre_activo}</b>\n"
        f"💵 Último precio: <b>{moneda} {precio_actual:.2f}</b>\n"
        f"📊 Promedio (2a): {moneda} {promedio_2a:.2f}\n"
        f"──────────────────────\n"
        f"{status_envio}"
    )
