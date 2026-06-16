import os
from datetime import datetime
import pytz
import requests
import yfinance as yf

# ============================================================
# CONFIGURACIÓN DE HORA ARGENTINA
# GitHub Actions corre en UTC, pero nosotros convertimos acá
# para mostrar la hora correcta en el mensaje de Telegram
# ============================================================
argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")
hora_actual  = datetime.now(argentina_tz)
hora   = hora_actual.hour
minuto = hora_actual.minute
print(f"DEBUG: Hora Argentina detectada: {hora}:{minuto:02d}")

# ============================================================
# LISTAS DE ACCIONES
# Panel Líder: las 21 empresas del índice Merval principal
# Panel General: empresas de menor capitalización
# ============================================================
panel_lider = [
    "ALUA.BA","BBAR.BA","BMA.BA","BYMA.BA","CEPU.BA","COME.BA","EDN.BA","GGAL.BA",
    "IRSA.BA","LOMA.BA","METR.BA","MIRG.BA","PAMP.BA","SUPV.BA","TECO2.BA","TGNO4.BA",
    "TGSU2.BA","TRAN.BA","TXAR.BA","VALO.BA","YPFD.BA"
]
panel_general = [
    "AGRO.BA","AUSO.BA","BHIP.BA","BOLT.BA","BPAT.BA","CADO.BA","CAPX.BA","CARC.BA",
    "CECO2.BA","CELU.BA","CGPA2.BA","CTIO.BA","DGCU2.BA","FERR.BA","FIPL.BA","GAMI.BA",
    "GCDI.BA","GRIM.BA","HAVA.BA","INVJ.BA","LEDE.BA","LONG.BA","MOLA.BA","MOLI.BA",
    "MORI.BA","OEST.BA","PATA.BA","RICH.BA","RIGO.BA","SAMI.BA","SEMI.BA"
]

# ============================================================
# FUNCIÓN DE ENVÍO A TELEGRAM
# Usa Markdown para negritas y cursivas en el mensaje
# ============================================================
def enviar_telegram(mensaje):
    TOKEN   = os.environ["TOKEN_BOT"]
    CHAT_ID = os.environ["CHAT_ID"]
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    r = requests.post(url, data=payload)
    print(f"DEBUG: Telegram status: {r.status_code}")
    if r.status_code != 200:
        print(f"DEBUG: Telegram error: {r.text}")

# ============================================================
# FUNCIÓN PARA PROCESAR PANEL - CORREGIDA
#
# PROBLEMA ANTERIOR: period="2d" durante el horario de mercado
# a veces solo devuelve 1 fila (el cierre de ayer) porque Yahoo
# aún no cerró la vela del día actual → len(hist) < 2 → sin datos.
#
# SOLUCIÓN: Usar period="5d" para tener más filas disponibles,
# y además intentar obtener el precio en tiempo real (fast_info)
# como respaldo cuando el mercado está abierto.
# ============================================================
def procesar_panel(lista_tickers):
    resultados = {}

    for ticker in lista_tickers:
        try:
            asset = yf.Ticker(ticker)

            # --- Intento 1: historial de 5 días (más robusto que 2d) ---
            # Con 5d tenemos varias filas aunque Yahoo demore en cerrar la vela de hoy
            hist = asset.history(period="5d", interval="1d")

            precio_actual   = None
            precio_anterior = None

            if not hist.empty and len(hist) >= 2:
                precio_anterior = hist["Close"].iloc[-2]

                # Durante el mercado abierto, la última fila puede ser parcial.
                # Intentamos primero el precio en tiempo real (más preciso).
                try:
                    precio_rt = asset.fast_info.get("last_price", None)
                    if precio_rt and precio_rt > 0:
                        precio_actual = precio_rt
                    else:
                        precio_actual = hist["Close"].iloc[-1]
                except:
                    precio_actual = hist["Close"].iloc[-1]

            # --- Intento 2 (salvavidas): si hist sigue vacío, usar fast_info directo ---
            if precio_actual is None or precio_anterior is None:
                try:
                    fi = asset.fast_info
                    precio_actual        = fi.get("last_price", None)
                    precio_anterior_prev = fi.get("previous_close", None)
                    if precio_actual and precio_anterior_prev and precio_anterior_prev > 0:
                        precio_anterior = precio_anterior_prev
                    else:
                        print(f"DEBUG: Sin precio válido para {ticker} (fast_info)")
                        continue
                except Exception as e2:
                    print(f"DEBUG: fast_info falló para {ticker}: {e2}")
                    continue

            # Validación final antes de calcular
            if not precio_actual or not precio_anterior or precio_anterior == 0:
                print(f"DEBUG: Precio inválido para {ticker}: actual={precio_actual}, anterior={precio_anterior}")
                continue

            rendimiento = ((precio_actual - precio_anterior) / precio_anterior) * 100
            nombre_corto = ticker.replace(".BA", "")
            resultados[nombre_corto] = rendimiento
            print(f"DEBUG: {nombre_corto} → anterior={precio_anterior:.2f} actual={precio_actual:.2f} var={rendimiento:+.2f}%")

        except Exception as e:
            print(f"DEBUG: Error procesando {ticker}: {e}")
            continue

    return resultados

# ============================================================
# BLOQUE DE EJECUCIÓN PRINCIPAL
# Se activa cada vez que GitHub Actions dispara el workflow
#
# NOTA SOBRE EL CRON Y LAS DEMORAS:
# GitHub Actions puede demorar hasta 15-30 min en ejecutar
# los cron jobs (especialmente en horarios pico).
# Por eso el cron está configurado ~3 min antes de cada hora AR.
# No hay forma de eliminar esa demora desde el código.
# ============================================================
datos_lider   = procesar_panel(panel_lider)
datos_general = procesar_panel(panel_general)

print(f"DEBUG: Panel Líder procesado: {len(datos_lider)} acciones")
print(f"DEBUG: Panel General procesado: {len(datos_general)} acciones")

# Armar mensaje según si es cierre (17 hs) o actualización horaria
if hora == 17:
    mensaje = "🏁 *CIERRE DE MERCADO | Resumen Final del Día* 🏁\n\n"
else:
    mensaje = f"📊 *Merval | Actualización ({hora}:{minuto:02d} hs AR)*\n\n"

# --- Bloque Panel Líder ---
mensaje += "💎 *PANEL LÍDER (Top 5 Subas):*\n"
if datos_lider:
    # Mostrar top 5 en lugar de top 3 para más información
    top_lider = sorted(datos_lider.items(), key=lambda x: x[1], reverse=True)[:5]
    for i, (ticker, var) in enumerate(top_lider, 1):
        emoji = "🟢" if var >= 0 else "🔴"
        signo = "+" if var >= 0 else ""
        mensaje += f"{i}. *{ticker}* {emoji} {signo}{var:.2f}%\n"
else:
    mensaje += "⚠️ Sin datos del Panel Líder (mercado cerrado o feriado).\n"

# --- Bloque Panel General ---
mensaje += "\n🏭 *PANEL GENERAL (Top 3):*\n"
if datos_general:
    top_general = sorted(datos_general.items(), key=lambda x: x[1], reverse=True)[:3]
    for i, (ticker, var) in enumerate(top_general, 1):
        emoji = "🟢" if var >= 0 else "🔴"
        signo = "+" if var >= 0 else ""
        mensaje += f"{i}. *{ticker}* {emoji} {signo}{var:.2f}%\n"
else:
    mensaje += "⚠️ Sin datos del Panel General.\n"

# --- Pie del mensaje ---
if hora == 17:
    mensaje += "\n👏 ¡Fin de la jornada! Mañana seguimos."
else:
    mensaje += "\n📈 _Actualización automática. Próxima en ~1 hora._"

# Si absolutamente todo falló → mensaje de diagnóstico
if not datos_lider and not datos_general:
    mensaje = (
        f"🔧 *Bot Merval activo* ({hora}:{minuto:02d} hs AR)\n"
        "⚠️ Sin datos de Yahoo Finance.\n"
        "Posibles causas: feriado, mercado cerrado o bloqueo temporal de Yahoo."
    )

enviar_telegram(mensaje)
