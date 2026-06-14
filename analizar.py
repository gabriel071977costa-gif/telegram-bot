import os
import requests
import pandas as pd
import yfinance as yf

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
        print(f"[ERROR Telegram Analizar]: {e}")

def obtener_universo_activos():
    activos_maestro = {}
    for ticker, desc in ACTIVOS_YFINANZAS.items(): 
        activos_maestro[ticker] = desc
    for ticker in panel_lider:
        if ticker not in activos_maestro:
            activos_maestro[ticker] = f"{ticker.replace('.BA', '')} (Panel Líder)"
    for ticker in panel_general:
        if ticker not in activos_maestro:
            activos_maestro[ticker] = f"{ticker.replace('.BA', '')} (Panel General)"
    return activos_maestro

def mapear_argumento(argumento, activos_maestro):
    mapeo = {}
    for ticker in activos_maestro.keys():
        corto = ticker.replace(".BA", "").replace("-USD", "").replace("=F", "")
        mapeo[corto] = ticker
        mapeo[ticker] = ticker
    mapeo["YPF"] = "YPFD.BA"
    return mapeo.get(argumento)

def calcular_tendencia_porcentual(df, dias):
    """Calcula la variación del precio en una ventana de días específica"""
    if len(df) < dias:
        dias = len(df)
    sub_df = df.iloc[-dias:]
    if len(sub_df) < 2: return 0.0
    inicio = sub_df["Close"].iloc[0]
    fin = sub_df["Close"].iloc[-1]
    return ((fin - inicio) / inicio) * 100

def ejecutar_analisis(argumento, chat_id):
    if not argumento:
        enviar_a_telegram(chat_id, "⚠️ <b>Uso correcto:</b> <code>/analizar [ACTIVO]</code>")
        return

    activos_maestro = obtener_universo_activos()
    ticker_real = mapear_argumento(argumento, activos_maestro)

    if not ticker_real:
        enviar_a_telegram(chat_id, f"❌ El activo <b>{argumento}</b> no está en tus paneles.")
        return

    nombre_activo = activos_maestro.get(ticker_real, ticker_real)
    enviar_a_telegram(chat_id, f"📊 <i>Ruk ejecutando Escáner Multi-Temporal y de Volumen para {ticker_real}...</i>")

    try:
        # Descargamos los últimos 2 años de datos diarios directamente
        ticker_yf = yf.Ticker(ticker_real)
        df = ticker_yf.history(period="2y")

        if df.empty or len(df) < 30:
            enviar_a_telegram(chat_id, f"❌ No hay historial suficiente en Yahoo Finanzas para analizar <code>{ticker_real}</code>.")
            return

        # --------------------------------------------------------
        # 1. BLOQUE DE ANÁLISIS MULTI-TEMPORAL (Tendencias)
        # --------------------------------------------------------
        # Aproximamos los meses asumiendo 21 días hábiles de bolsa por mes
        t_2anos   = calcular_tendencia_porcentual(df, 504)
        t_1ano    = calcular_tendencia_porcentual(df, 252)
        t_10meses = calcular_tendencia_porcentual(df, 210)
        t_8meses  = calcular_tendencia_porcentual(df, 168)
        t_5meses  = calcular_tendencia_porcentual(df, 105)
        t_4meses  = calcular_tendencia_porcentual(df, 84)
        t_3meses  = calcular_tendencia_porcentual(df, 63)
        t_2meses  = calcular_tendencia_porcentual(df, 42)
        t_1mes    = calcular_tendencia_porcentual(df, 21)
        t_20dias  = calcular_tendencia_porcentual(df, 20)
        
        # Última semana día por día (Rueda de los últimos 5-7 días hábiles)
        df_semana = df.tail(6)
        linea_semana = []
        for i in range(1, len(df_semana)):
            cierre_hoy = df_semana["Close"].iloc[i]
            cierre_ayer = df_semana["Close"].iloc[i-1]
            var_dia = ((cierre_hoy - cierre_ayer) / cierre_ayer) * 100
            emoji_dia = "🔺" if var_dia >= 0 else "🔻"
            linea_semana.append(f"{emoji_dia} d{i}: {var_dia:+.2f}%")
        semana_str = " | ".join(linea_semana)

        # --------------------------------------------------------
        # 2. BLOQUE DE VOLUMEN Y FLUJO DE OPERADORES
        # --------------------------------------------------------
        volumen_actual = df["Volume"].iloc[-1]
        volumen_promedio_corto = df["Volume"].tail(10).mean() # Promedio últimas 2 semanas
        
        # Medimos la presión: precio sube + volumen sube = Operadores Comprando Fuertes
        precio_sube_hoy = df["Close"].iloc[-1] > df["Close"].iloc[-2]
        volumen_alto = volumen_actual > volumen_promedio_corto * 1.15 # 15% arriba de la media
        
        fuerza_operadores = "⚖️ Volumen Normal"
        puntos_volumen = 0 # Balance de fuerza compradores vs vendedores
        
        if precio_sube_hoy and volumen_alto:
            fuerza_operadores = "🔥 <b>COMPRADORES FUERTES</b> (Inyección de capital institucional)"
            puntos_volumen = 2
        elif not precio_sube_hoy and volumen_alto:
            fuerza_operadores = "⚠️ <b>VENDEDORES FUERTES</b> (Distribución / Salida de operadores)"
            puntos_volumen = -2
        elif precio_sube_hoy and not volumen_alto:
            fuerza_operadores = "📈 Suba sin fuerza (Pocos operadores participando)"
            puntos_volumen = 1
        elif not precio_sube_hoy and not volumen_alto:
            fuerza_operadores = "📉 Baja sin fuerza (Apatía generalizada)"
            puntos_volumen = -1

        # --------------------------------------------------------
        # 3. SISTEMA DE PUNTAJE Y VEREDICTO FINAL
        # --------------------------------------------------------
        # Evaluamos las tendencias de corto, mediano y largo plazo
        puntos_tendencia = 0
        listado_tendencias = [t_2anos, t_1ano, t_10meses, t_8meses, t_5meses, t_4meses, t_3meses, t_2meses, t_1mes, t_20dias]
        
        for t in listado_tendencias:
            if t > 2: puntos_tendencia += 1   # Tendencia alcista suma puntos
            if t < -2: puntos_tendencia -= 1  # Tendencia bajista resta puntos
            
        puntaje_total = puntos_tendencia + puntos_volumen
        precio_final = df["Close"].iloc[-1]
        moneda = "USD" if "-USD" in ticker_real or ticker_real in ["SPY", "NVDA", "GC=F"] else "$"

        # Clasificación del Veredicto Técnico
        if puntaje_total >= 6:
            veredicto = "🟢 <b>CONVIENE COMPRAR</b>\n🎯 <i>Tendencia multi-temporal firmemente alcista alineada con el ingreso de operadores con volumen fuerte.</i>"
            sugerencia_comando = f"<code>/invertir {argumento}</code>"
        elif puntaje_total <= -4:
            veredicto = "🔴 <b>CONVIENE VENDER / EVITAR</b>\n⚠️ <i>Presión vendedora dominante y deterioro estructural de las tendencias en múltiples plazos.</i>"
            sugerencia_comando = "<i>No se sugiere compra. Monitorear estabilidad.</i>"
        else:
            veredicto = "🟡 <b>ZONA NEUTRA (Esperar Confirmación)</b>\n⚖️ <i>Señales mixtas entre plazos temporales o falta de volumen acompañando el movimiento.</i>"
            sugerencia_comando = f"<i>Podés forzar la orden si querés con:</i> <code>/invertir {argumento}</code>"

        # --------------------------------------------------------
        # 4. REPORTE VISUAL A TELEGRAM
        # --------------------------------------------------------
        reporte = (
            f"📊 <b>ESCANER ESTRATÉGICO: {nombre_activo}</b>\n"
            f"🏷️ Ticker: <code>{ticker_real}</code> | Precio: <b>{moneda} {precio_final:.2f}</b>\n"
            f"──────────────────────\n"
            f"📈 <b>TENDENCIAS HISTÓRICAS:</b>\n"
            f"• 2 Años: <code>{t_2anos:+.1f}%</code> | 1 Año: <code>{t_1ano:+.1f}%</code>\n"
            f"• 10 Meses: <code>{t_10meses:+.1f}%</code> | 8 Meses: <code>{t_8meses:+.1f}%</code>\n"
            f"• 5 Meses: <code>{t_5meses:+.1f}%</code> | 4 Meses: <code>{t_4meses:+.1f}%</code>\n"
            f"• 3 Meses: <code>{t_3meses:+.1f}%</code> | 2 Meses: <code>{t_2meses:+.1f}%</code>\n"
            f"• 1 Mes: <code>{t_1mes:+.1f}%</code> | 20 Días: <code>{t_20dias:+.1f}%</code>\n"
            f"──────────────────────\n"
            f"📅 <b>ÚLTIMA SEMANA (Día a Día):</b>\n"
            f"<code>{semana_str}</code>\n"
            f"──────────────────────\n"
            f"👥 <b>FLUJO DE OPERADORES:</b>\n"
            f"{fuerza_operadores}\n"
            f"──────────────────────\n"
            f"📋 <b>DIAGNÓSTICO TÉCNICO:</b>\n"
            f"{veredicto}\n\n"
            f"💡 <b>Acción sugerida:</b> {sugerencia_comando}"
        )

        enviar_a_telegram(chat_id, reporte)

    except Exception as e:
        print(f"[ERROR Analizar Algoritmo]: {e}")
        enviar_a_telegram(chat_id, f"❌ Ocurrió un error al procesar el análisis matemático de <code>{ticker_real}</code>.")
