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
        print(f"[ERROR Telegram Invertir]: {e}")

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

def obtener_universo_activos():
    """Junta todas tus fuentes de acciones en un único mapa en memoria"""
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
    return activos_maestro

def mapear_argumento(argumento, activos_maestro):
    """Traduce alias cortos (como ggal o ypf) al ticker oficial de Yahoo"""
    mapeo = {}
    for ticker in activos_maestro.keys():
        corto = ticker.replace(".BA", "").replace("-USD", "").replace("=F", "")
        mapeo[corto] = ticker
        mapeo[ticker] = ticker
    mapeo["YPF"] = "YPFD.BA"
    return mapeo.get(argumento)

def ejecutar_inversion(argumento, chat_id):
    if not argumento:
        enviar_a_telegram(chat_id, "⚠️ <b>Uso correcto:</b> <code>/invertir [ACTIVO]</code>\nEjemplo: <code>/invertir GGAL</code>")
        return

    activos_maestro = obtener_universo_activos()
    ticker_real = mapear_argumento(argumento, activos_maestro)

    if not ticker_real:
        enviar_a_telegram(chat_id, f"❌ El activo <b>{argumento}</b> no se encuentra registrado.")
        return

    nombre_activo = activos_maestro.get(ticker_real, ticker_real)
    enviar_a_telegram(chat_id, f"⏳ <i>Ruk procesando orden de compra real para {ticker_real}...</i>")

    if ticker_real not in ACTIVOS_YFINANZAS: 
        ACTIVOS_YFINANZAS[ticker_real] = nombre_activo

    datos_vivos = resumen_estadistico(ticker_real)
    
    if not datos_vivos:
        enviar_a_telegram(chat_id, f"❌ Error al consultar cotización de mercado para la compra.")
        return

    precio_actual = datos_vivos["ultimo_cierre"]
    ahora_str     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- ESTRUCTURA CON DESCRIPCIÓN DEL ACTIVO ---
    orden_nueva = {
        "symbol": ticker_real,
        "descripcion": nombre_activo,
        "precio_solicitado": precio_actual,
        "fecha_orden": ahora_str,
        "estado": "PENDIENTE",
        "origen": "Telegram Bot (Ruk)"
    }

    guardado_ok = escribir_json_github("orden_compra.json", orden_nueva, f"Compra ejecutada desde bot: {ticker_real}")

    if guardado_ok:
        enviar_a_telegram(chat_id, 
            f"🚀 <b>¡ORDEN DE COMPRA ENVIADA!</b>\n"
            f"──────────────────────\n"
            f"📈 Activo: <b>{nombre_activo}</b>\n"
            f"💵 Precio de Entrada: <b>{precio_actual:.2f}</b>\n"
            f"──────────────────────\n"
            f"🟢 <i>Se actualizó 'orden_compra.json' en tu repositorio. GitHub Actions procesará tu simulación diaria.</i>"
        )
    else:
        enviar_a_telegram(chat_id, "🔴 <b>Error de comunicación:</b> No se pudo guardar la orden en tu GitHub.")
