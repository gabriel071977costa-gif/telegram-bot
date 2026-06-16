import os
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

TOKEN = os.getenv("TOKEN_BOT")

# ============================================================
# BASE DE DATOS MAESTRA UNIFICADA
# Mapea ticker → nombre descriptivo para mostrar en Telegram
# ============================================================
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

    # --- CRIPTOMONEDAS VOLÁTILES ---
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

    # --- STABLECOINS (siempre ~1 USD, no conviene analizar tendencias) ---
    "USDT-USD": "Tether USD (USDT)",
    "USDC-USD": "USD Coin (USDC)",
    "DAI-USD":  "Dai (DAI)",

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

# ============================================================
# FEEDS RSS POR TIPO DE ACTIVO
# Se usan para buscar noticias sin necesitar API key
# Infobae y Clarín para argentinas, CNN/NYT para internacionales
# ============================================================
RSS_ARGENTINA = [
    "https://www.infobae.com/feeds/rss/economia/",
    "https://www.clarin.com/rss/economia/",
    "https://www.cronista.com/files/rss/economia.xml",
    "https://www.ambito.com/rss/economia.xml",
]
RSS_INTERNACIONAL = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",       # Wall Street Journal Markets
    "https://feeds.content.dowjones.io/public/rss/mw-topstories",  # MarketWatch
    "https://rss.cnn.com/rss/money_news_international.rss", # CNN Money
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",  # Yahoo Finance (se formatea)
]

# Palabras clave positivas → señal de compra
PALABRAS_POSITIVAS = [
    "gana", "sube", "crece", "record", "récord", "maxim", "aumento", "aument",
    "rebota", "recupera", "mejora", "positiv", "beneficio", "ganancia", "inversion",
    "aprueba", "acuerdo", "expansion", "supera", "lidera", "profit", "gain",
    "growth", "rises", "surge", "beat", "record", "up", "bullish", "buy",
    "strong", "upgrade", "positive", "deal", "expand"
]

# Palabras clave negativas → señal de venta/precaución
PALABRAS_NEGATIVAS = [
    "cae", "baja", "pierde", "crisis", "deficit", "deuda", "riesgo", "alerta",
    "quiebra", "default", "cayó", "caida", "pérdida", "recorte", "suspende",
    "investig", "fraude", "multa", "sancion", "embargo", "falls", "drops",
    "loss", "decline", "bearish", "sell", "downgrade", "weak", "cut", "fraud",
    "bankrupt", "suspend", "fine", "penalty", "investigation"
]


def enviar_a_telegram(chat_id, texto):
    """Envía un mensaje HTML a Telegram. Usa parse_mode HTML para negritas y código."""
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR Telegram Analizar]: {e}")


def mapear_argumento(argumento):
    """
    Convierte alias cortos al ticker real de Yahoo Finance.
    Ej: 'ggal' → 'GGAL.BA', 'btc' → 'BTC-USD', 'ypf' → 'YPFD.BA'
    """
    arg_limpio = argumento.upper().strip()

    # Caso especial manual: YPF → YPFD.BA
    if arg_limpio == "YPF":
        return "YPFD.BA"

    # Busca coincidencia exacta quitando sufijos .BA, -USD, =F
    for ticker in UNIVERSO_ACTIVOS.keys():
        corto = ticker.replace(".BA", "").replace("-USD", "").replace("=F", "")
        if arg_limpio == corto or arg_limpio == ticker:
            return ticker

    return None


def calcular_tendencia_porcentual(df, dias):
    """
    Calcula la variación porcentual del precio de cierre
    en una ventana de N días hacia atrás desde hoy.
    Si hay menos datos que los días pedidos, usa todos los disponibles.
    """
    if len(df) < dias:
        dias = len(df)
    sub_df = df.iloc[-dias:]
    if len(sub_df) < 2:
        return 0.0
    inicio = sub_df["Close"].iloc[0]
    fin    = sub_df["Close"].iloc[-1]
    return ((fin - inicio) / inicio) * 100


def detectar_patron_minmax(df, ventana_dias, nombre_ventana):
    """
    Detecta si el activo está cerca de su mínimo o máximo histórico
    dentro de la ventana dada. Útil para encontrar puntos de entrada/salida.

    Retorna:
        - texto con el diagnóstico
        - puntos: +1 si está cerca de mínimo (oportunidad), -1 si está cerca de máximo (riesgo)
    """
    sub = df.tail(ventana_dias)
    if len(sub) < 5:
        return "", 0

    precio_actual = sub["Close"].iloc[-1]
    minimo        = sub["Low"].min()
    maximo        = sub["High"].max()
    rango         = maximo - minimo

    if rango == 0:
        return "", 0

    # Posición relativa del precio actual dentro del rango (0% = mínimo, 100% = máximo)
    posicion = ((precio_actual - minimo) / rango) * 100

    if posicion <= 20:
        # Está muy cerca del mínimo → posible rebote → oportunidad de compra
        return f"📍 {nombre_ventana}: cerca del MÍNIMO ({posicion:.0f}% del rango) → oportunidad", 1
    elif posicion >= 80:
        # Está muy cerca del máximo → posible techo → riesgo de caída
        return f"⚠️ {nombre_ventana}: cerca del MÁXIMO ({posicion:.0f}% del rango) → precaución", -1
    else:
        # Zona media → sin señal clara
        return f"⚖️ {nombre_ventana}: zona media ({posicion:.0f}% del rango)", 0


def buscar_noticias(ticker_real, nombre_activo):
    """
    Busca noticias en RSS de medios económicos (sin API key).
    Analiza si el título/descripción contiene palabras positivas o negativas.

    Retorna:
        - resumen_texto: string con las últimas noticias encontradas
        - puntos_noticias: +N positivas, -N negativas (máx ±3)
        - emoji_noticias: 🟢 / 🔴 / 🟡
    """
    # Nombre de empresa para buscar en los títulos (limpio, sin sufijos)
    nombre_busqueda = nombre_activo.split("(")[0].strip().lower()
    ticker_corto    = ticker_real.replace(".BA", "").replace("-USD", "").replace("=F", "").lower()

    # Elegir feeds según si es activo argentino o internacional
    es_argentino = ticker_real.endswith(".BA")
    feeds = RSS_ARGENTINA if es_argentino else RSS_INTERNACIONAL

    noticias_encontradas = []
    puntos_noticias      = 0

    headers = {"User-Agent": "Mozilla/5.0 (compatible; RukBot/1.0)"}

    for feed_url in feeds:
        # Para Yahoo Finance RSS se formatea el ticker en la URL
        url_final = feed_url.replace("{ticker}", ticker_real)

        try:
            resp = requests.get(url_final, headers=headers, timeout=8)
            if resp.status_code != 200:
                continue

            # Parseo manual del XML RSS (sin feedparser para no agregar dependencia)
            contenido = resp.text.lower()

            # Buscar bloques <item> en el XML
            items = resp.text.split("<item>")
            for item in items[1:]:  # El primero es el header del feed
                # Extraer título
                titulo = ""
                if "<title>" in item:
                    titulo = item.split("<title>")[1].split("</title>")[0]
                    titulo = titulo.replace("<![CDATA[", "").replace("]]>", "").strip()

                # Extraer descripción corta
                desc = ""
                if "<description>" in item:
                    desc = item.split("<description>")[1].split("</description>")[0]
                    desc = desc.replace("<![CDATA[", "").replace("]]>", "").strip()[:200]

                texto_noticia = (titulo + " " + desc).lower()

                # Filtrar solo noticias que mencionen el activo o empresa
                if nombre_busqueda not in texto_noticia and ticker_corto not in texto_noticia:
                    continue

                # Contar palabras positivas y negativas en la noticia
                pts_pos = sum(1 for p in PALABRAS_POSITIVAS if p in texto_noticia)
                pts_neg = sum(1 for p in PALABRAS_NEGATIVAS if p in texto_noticia)
                balance = pts_pos - pts_neg

                if balance > 0:
                    emoji = "🟢"
                    puntos_noticias += 1
                elif balance < 0:
                    emoji = "🔴"
                    puntos_noticias -= 1
                else:
                    emoji = "🟡"

                # Guardamos máximo 3 noticias para no saturar el mensaje
                if len(noticias_encontradas) < 3:
                    titulo_corto = titulo[:80] + "..." if len(titulo) > 80 else titulo
                    noticias_encontradas.append(f"{emoji} {titulo_corto}")

        except Exception as e:
            # Si un feed falla lo ignoramos silenciosamente
            print(f"[RSS Error] {url_final}: {e}")
            continue

    # Limitar puntos de noticias a ±3 para no distorsionar el veredicto final
    puntos_noticias = max(-3, min(3, puntos_noticias))

    if not noticias_encontradas:
        resumen = "📰 Sin noticias recientes encontradas en medios económicos."
        emoji_general = "🟡"
    else:
        resumen = "\n".join(noticias_encontradas)
        if puntos_noticias > 0:
            emoji_general = "🟢"
        elif puntos_noticias < 0:
            emoji_general = "🔴"
        else:
            emoji_general = "🟡"

    return resumen, puntos_noticias, emoji_general


def ejecutar_analisis(argumento, chat_id):
    """
    Función principal que ejecuta el análisis completo de un activo:
    1. Descarga 2 años de historial desde Yahoo Finance
    2. Calcula tendencias multi-temporales (2 años → 2 semanas)
    3. Detecta patrones de mínimos/máximos en cada ventana
    4. Analiza flujo de volumen (compradores vs vendedores)
    5. Busca noticias en RSS de medios económicos
    6. Combina todo en un puntaje y emite veredicto final
    """
    if not argumento:
        enviar_a_telegram(chat_id, "⚠️ <b>Uso correcto:</b> <code>/analizar [ACTIVO]</code>\n\n💡 Ejemplos:\n• <code>/analizar ggal</code>\n• <code>/analizar btc</code>\n• <code>/analizar ypf</code>")
        return

    ticker_real = mapear_argumento(argumento)

    if not ticker_real:
        enviar_a_telegram(chat_id, f"❌ El activo <b>{argumento}</b> no está registrado en tus paneles de análisis.\n\n💡 Usá <code>/buscar [término]</code> para encontrar activos disponibles.")
        return

    nombre_activo = UNIVERSO_ACTIVOS.get(ticker_real, ticker_real)
    enviar_a_telegram(chat_id, f"📊 <i>Analizando {nombre_activo}... (datos + noticias web)</i>")

    try:
        # --------------------------------------------------------
        # DESCARGA DE HISTORIAL DESDE YAHOO FINANCE (2 años)
        # Primero con sesión simulada para evitar bloqueos del Merval
        # --------------------------------------------------------
        try:
            sesion = requests.Session()
            sesion.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            ticker_yf = yf.Ticker(ticker_real, session=sesion)
            df = ticker_yf.history(period="2y")
        except:
            df = pd.DataFrame()

        # Salvavidas: si falló la sesión, descarga directa
        if df.empty:
            ticker_yf = yf.Ticker(ticker_real)
            df = ticker_yf.history(period="2y")

        if df.empty or len(df) < 14:
            enviar_a_telegram(chat_id, f"❌ No hay historial suficiente en Yahoo Finance para <code>{ticker_real}</code>.")
            return

        # --------------------------------------------------------
        # 1. TENDENCIAS MULTI-TEMPORALES
        # Períodos: 2 años, 12, 10, 8, 5, 4, 3, 2 meses, 30 días, 2 semanas
        # --------------------------------------------------------
        t_2anos    = calcular_tendencia_porcentual(df, 504)  # ~2 años hábiles
        t_12meses  = calcular_tendencia_porcentual(df, 252)  # 12 meses
        t_10meses  = calcular_tendencia_porcentual(df, 210)  # 10 meses
        t_8meses   = calcular_tendencia_porcentual(df, 168)  # 8 meses
        t_5meses   = calcular_tendencia_porcentual(df, 105)  # 5 meses
        t_4meses   = calcular_tendencia_porcentual(df, 84)   # 4 meses
        t_3meses   = calcular_tendencia_porcentual(df, 63)   # 3 meses
        t_2meses   = calcular_tendencia_porcentual(df, 42)   # 2 meses
        t_30dias   = calcular_tendencia_porcentual(df, 21)   # ~30 días hábiles
        t_2semanas = calcular_tendencia_porcentual(df, 10)   # ~2 semanas hábiles

        # Última semana día por día (muestra evolución reciente diaria)
        df_semana = df.tail(6)
        linea_semana = []
        for i in range(1, len(df_semana)):
            cierre_hoy  = df_semana["Close"].iloc[i]
            cierre_ayer = df_semana["Close"].iloc[i - 1]
            var_dia     = ((cierre_hoy - cierre_ayer) / cierre_ayer) * 100
            emoji_dia   = "🔺" if var_dia >= 0 else "🔻"
            linea_semana.append(f"{emoji_dia} d{i}: {var_dia:+.2f}%")
        semana_str = " | ".join(linea_semana)

        # Sistema de puntos por tendencias: +1 si sube más de 2%, -1 si baja más de 2%
        puntos_tendencia  = 0
        listado_tendencias = [t_2anos, t_12meses, t_10meses, t_8meses,
                               t_5meses, t_4meses, t_3meses, t_2meses, t_30dias, t_2semanas]
        for t in listado_tendencias:
            if t > 2:  puntos_tendencia += 1
            if t < -2: puntos_tendencia -= 1

        # --------------------------------------------------------
        # 2. PATRONES DE MÍNIMOS Y MÁXIMOS
        # Detecta si el precio está cerca de un piso (comprar) o techo (vender)
        # Especialmente útil para criptos con alta volatilidad
        # --------------------------------------------------------
        patrones = []
        puntos_patrones = 0

        ventanas = [
            (504, "2 Años"),
            (252, "12 Meses"),
            (105, "5 Meses"),
            (63,  "3 Meses"),
            (21,  "30 Días"),
            (10,  "2 Semanas"),
        ]

        for dias_v, nombre_v in ventanas:
            texto_p, pts_p = detectar_patron_minmax(df, dias_v, nombre_v)
            if texto_p:
                patrones.append(texto_p)
                puntos_patrones += pts_p

        # Limitar impacto de patrones a ±3 en el puntaje total
        puntos_patrones = max(-3, min(3, puntos_patrones))

        # --------------------------------------------------------
        # 3. FLUJO DE VOLUMEN (compradores vs vendedores)
        # Compara volumen de hoy con el promedio de los últimos 10 días
        # --------------------------------------------------------
        volumen_actual         = df["Volume"].iloc[-1]
        volumen_promedio_corto = df["Volume"].tail(10).mean()
        precio_sube_hoy        = df["Close"].iloc[-1] > df["Close"].iloc[-2]
        volumen_alto           = volumen_actual > volumen_promedio_corto * 1.15

        puntos_volumen = 0
        if precio_sube_hoy and volumen_alto:
            fuerza_operadores = "🔥 <b>COMPRADORES FUERTES</b> (Inyección de capital institucional)"
            puntos_volumen = 2
        elif not precio_sube_hoy and volumen_alto:
            fuerza_operadores = "⚠️ <b>VENDEDORES FUERTES</b> (Distribución / Salida de operadores)"
            puntos_volumen = -2
        elif precio_sube_hoy and not volumen_alto:
            fuerza_operadores = "📈 Suba sin fuerza (Pocos operadores participando)"
            puntos_volumen = 1
        else:
            fuerza_operadores = "📉 Baja sin fuerza (Apatía generalizada)"
            puntos_volumen = -1

        # --------------------------------------------------------
        # 4. NOTICIAS WEB EN TIEMPO REAL
        # Busca en RSS de Infobae, Clarín, CNN, MarketWatch, Yahoo Finance
        # Clasifica cada noticia como positiva 🟢 o negativa 🔴
        # --------------------------------------------------------
        noticias_texto, puntos_noticias, emoji_noticias = buscar_noticias(ticker_real, nombre_activo)

        # --------------------------------------------------------
        # 5. PUNTAJE TOTAL Y VEREDICTO FINAL
        # Suma tendencias + patrones + volumen + noticias
        # --------------------------------------------------------
        puntaje_total = puntos_tendencia + puntos_patrones + puntos_volumen + puntos_noticias
        precio_final  = df["Close"].iloc[-1]

        # Detectar moneda: .BA puro usa $, resto USD
        es_merval_puro = ticker_real.endswith(".BA") and ticker_real not in ["CRES.BA", "MOLA.BA", "LEDE.BA"]
        moneda = "$" if es_merval_puro else "USD"

        # Umbral de veredicto: ≥6 comprar, ≤-4 vender, resto esperar
        if puntaje_total >= 6:
            veredicto      = "🟢 <b>CONVIENE COMPRAR</b>\n🎯 <i>Tendencias alcistas + patrones favorables + noticias positivas.</i>"
            sugerencia_cmd = f"<code>/invertir {argumento.lower()}</code>"
        elif puntaje_total <= -4:
            veredicto      = "🔴 <b>CONVIENE VENDER / EVITAR</b>\n⚠️ <i>Presión vendedora + deterioro técnico + noticias negativas.</i>"
            sugerencia_cmd = "<i>No se sugiere compra. Monitorear.</i>"
        else:
            veredicto      = "🟡 <b>ZONA NEUTRA (Esperar confirmación)</b>\n⚖️ <i>Señales mixtas. Aguardar alineación de todos los indicadores.</i>"
            sugerencia_cmd = f"<i>Podés forzar con:</i> <code>/invertir {argumento.lower()}</code>"

        # --------------------------------------------------------
        # 6. REPORTE FINAL A TELEGRAM
        # --------------------------------------------------------
        patrones_str = "\n".join(patrones) if patrones else "Sin patrones destacados."

        reporte = (
            f"📊 <b>ANÁLISIS ESTRATÉGICO: {nombre_activo}</b>\n"
            f"🏷️ <code>{ticker_real}</code> | Precio: <b>{moneda} {precio_final:.2f}</b>\n"
            f"──────────────────────\n"
            f"📈 <b>TENDENCIAS HISTÓRICAS:</b>\n"
            f"• 2 Años: <code>{t_2anos:+.1f}%</code>  | 12 Meses: <code>{t_12meses:+.1f}%</code>\n"
            f"• 10 Meses: <code>{t_10meses:+.1f}%</code> | 8 Meses: <code>{t_8meses:+.1f}%</code>\n"
            f"• 5 Meses: <code>{t_5meses:+.1f}%</code>  | 4 Meses: <code>{t_4meses:+.1f}%</code>\n"
            f"• 3 Meses: <code>{t_3meses:+.1f}%</code>  | 2 Meses: <code>{t_2meses:+.1f}%</code>\n"
            f"• 30 Días: <code>{t_30dias:+.1f}%</code>  | 2 Semanas: <code>{t_2semanas:+.1f}%</code>\n"
            f"──────────────────────\n"
            f"📅 <b>ÚLTIMA SEMANA (Día a Día):</b>\n"
            f"<code>{semana_str}</code>\n"
            f"──────────────────────\n"
            f"🔍 <b>PATRONES MÍNIMOS/MÁXIMOS:</b>\n"
            f"{patrones_str}\n"
            f"──────────────────────\n"
            f"👥 <b>FLUJO DE OPERADORES:</b>\n"
            f"{fuerza_operadores}\n"
            f"──────────────────────\n"
            f"📰 <b>NOTICIAS WEB:</b> {emoji_noticias}\n"
            f"{noticias_texto}\n"
            f"──────────────────────\n"
            f"📋 <b>DIAGNÓSTICO FINAL</b> (Puntaje: {puntaje_total:+d}):\n"
            f"{veredicto}\n\n"
            f"💡 <b>Acción sugerida:</b> {sugerencia_cmd}"
        )

        enviar_a_telegram(chat_id, reporte)

    except Exception as e:
        print(f"[ERROR Analizar]: {e}")
        enviar_a_telegram(chat_id, f"❌ Error al analizar <code>{ticker_real}</code>. Intentá de nuevo en unos minutos.")
