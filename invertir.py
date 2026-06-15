import os
import json
import base64
import requests
import datetime

# --- IMPORTAMOS LA FUNCIÓN DE COTIZACIÓN NATIVA ---
from bot_yahooFinanzas import resumen_estadistico

TOKEN        = os.getenv("TOKEN_BOT")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "gabriel071977costa-gif/bot-yahooFinanzas")

# BASE DE DATOS MAESTRA UNIFICADA (Para validar y mapear las órdenes)
UNIVERSO_ACTIVOS = {
    # --- PANEL LÍDER MERVAL (ARGENTINA) ---
    "ALUA.BA":  "Aluar (Aluminio)",
    "BBAR.BA":  "Banco BBVA Argentina",
    "BMA.BA":   "Banco Macro",
    "BYMA.BA":  "Bolsas y Mercados Argentinos",
    "CEPU.BA":  "Central Puerto",
    "COME.BA":  "Sociedad Comercial del Plata",
    "EDN.BA":   "Edenor",
    "GGAL.BA":  "Grupo Financiero Galicia",
    "IRSA.BA":  "IRSA",
    "LOMA.BA":  "Loma Negra",
    "METR.BA":  "Metrogas",
    "MIRG.BA":  "Mirgor",
    "PAMP.BA":  "Pampa Energía",
    "SUPV.BA":  "Banco Supervielle",
    "TECO2.BA": "Telecom Argentina",
    "TGNO4.BA": "Transportadora Gas del Norte",
    "TGSU2.BA": "Transportadora Gas del Sur",
    "TRAN.BA":  "Transener",
    "TXAR.BA":  "Ternium Argentina",
    "VALO.BA":  "Banco de Valores",
    "YPFD.BA":  "YPF Clase D",
    
    # --- CRIPTOMONEDAS ---
    "BTC-USD":  "Bitcoin USD",
    "ETH-USD":  "Ethereum USD",
    "BNB-USD":  "Binance Coin USD",
    "SOL-USD":  "Solana USD",
    "XRP-USD":  "Ripple USD",
    "ADA-USD":  "Cardano USD",
    "AVAX-USD": "Avalanche USD",
    "DOT-USD":  "Polkadot USD",
    "LINK-USD": "Chainlink USD",
    "DOGE-USD": "Dogecoin USD",
    
    # --- SECTOR AGRO ---
    "CRES.BA":  "Cresud",
    "MOLA.BA":  "Molinos Agro",
    "LEDE.BA":  "Ledesma",

    # --- MERCADO INTERNACIONAL ---
    "GC=F":     "Oro Futuros",
    "GOLD":     "Barrick Gold",
    "FCX":      "Freeport-McMoRan (Cobre)",
    "ALB":      "Albemarle Corp (Litio)",
    "VALE":     "Vale S.A. (Hierro)",
    "NVDA":     "NVIDIA Corporation",
    "AAPL":     "Apple Inc.",
    "MSFT":     "Microsoft Corporation",
    "AMD":      "Advanced Micro Devices",
    "TSM":      "Taiwan Semiconductor",
    "XOM":      "Exxon Mobil",
    "CVX":      "Chevron Corporation",
    "SHEL":     "Shell plc",
    "BP":       "BP plc",
    "GOOGL":    "Alphabet Inc. (Google)",
    "META":     "Meta Platforms",
    "NFLX":     "Netflix Inc.",
    "DIS":      "The Walt Disney Company",
    "TSLA":     "Tesla Inc.",
    "BYDDF":    "BYD Company",
    "NIO":      "NIO Inc.",
    "F":        "Ford Motor Company",
    "GM":       "General Motors",
    "TM":       "Toyota Motor Corp",
    "RACE":     "Ferrari N.V.",
    "SPY":      "S&P 500 ETF"
}

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

def mapear_argumento(argumento):
    """Traduce alias cortos (como ggal, btc, tsla) al ticker oficial de Yahoo de forma inteligente"""
    arg_limpio = argumento.upper().strip()
    
    # Atajo estético manual
    if arg_limpio == "YPF": return "YPFD.BA"
    
    # Búsqueda por alias cortos o ticker completo
    for ticker in UNIVERSO_ACTIVOS.keys():
        corto = ticker.replace(".BA", "").replace("-USD", "").replace("=F", "")
        if arg_limpio == corto or arg_limpio == ticker:
            return ticker
    return None

def ejecutar_inversion(argumento, chat_id):
    if not argumento:
        enviar_a_telegram(chat_id, "⚠️ <b>Uso correcto:</b> <code>/invertir [ACTIVO]</code>\nEjemplo: <code>/invertir GGAL</code>")
        return

    ticker_real = mapear_argumento(argumento)

    if not ticker_real:
        enviar_a_telegram(chat_id, f"❌ El activo <b>{argumento}</b> no se encuentra registrado en el universo de inversión.")
        return

    nombre_activo = UNIVERSO_ACTIVOS.get(ticker_real, ticker_real)
    enviar_a_telegram(chat_id, f"⏳ <i>Ruk procesando orden de compra simulada para {ticker_real}...</i>")

    # Obtenemos los datos en vivo utilizando tu función nativa
    datos_vivos = resumen_estadistico(ticker_real)
    
    if not datos_vivos or "ultimo_cierre" not in datos_vivos:
        enviar_a_telegram(chat_id, f"❌ Error al consultar la cotización en vivo de <code>{ticker_real}</code> para procesar la orden.")
        return

    precio_actual = datos_vivos["ultimo_cierre"]
    ahora_str     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- ESTRUCTURA CON DESCRIPCIÓN ACTUALIZADA ---
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
        # Formateamos la moneda según el mercado
        es_merval_puro = ticker_real.endswith(".BA") and ticker_real not in ["CRES.BA", "MOLA.BA", "LEDE.BA"]
        moneda = "$" if es_merval_puro else "USD"

        enviar_a_telegram(chat_id, 
            f"🚀 <b>¡ORDEN DE COMPRA ENVIADA!</b>\n"
            f"──────────────────────\n"
            f"📈 Activo: <b>{nombre_activo}</b> ({ticker_real})\n"
            f"💵 Precio de Entrada: <b>{moneda} {precio_actual:.2f}</b>\n"
            f"──────────────────────\n"
            f"🟢 <i>Se actualizó 'orden_compra.json' en tu repositorio de GitHub. Tu estrategia automatizada se encargará del resto.</i>"
        )
    else:
        enviar_a_telegram(chat_id, "🔴 <b>Error de comunicación:</b> No se pudo guardar ni confirmar la orden en tu GitHub.")
