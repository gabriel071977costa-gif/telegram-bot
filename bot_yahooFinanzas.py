# ============================================================
# BOT YAHOO FINANZAS - ORQUESTADOR PRINCIPAL
# Corre cada hora via GitHub Actions (bot.yml)
# Horario: 10:00 a 18:00 hora Argentina (UTC-3)
# Importa: baseDeDatosFinanzas.py y logicaYahooFinanzas.py
# El bot.yml hace git pull al inicio y git push al final
# para que cache_finanzas.json y estado_simulacion.json
# persistan entre ejecuciones (GitHub Actions no tiene disco)
# ============================================================

# ------------------------------------------------------------
# IMPORTS Y CONFIGURACIÓN
# TOKEN_BOT y CHAT_ID vienen de Secrets de GitHub Actions
# ------------------------------------------------------------
import os
import datetime
import requests

from baseDeDatosFinanzas import actualizar_todos, ACTIVOS
from logicaYahooFinanzas  import (
    generar_señal,
    ejecutar_operacion,
    calcular_acumulado,
    cargar_estado,
    guardar_estado,
    resetear_dia_si_corresponde,
)

TOKEN   = os.getenv("TOKEN_BOT")
CHAT_ID = os.getenv("CHAT_ID")

# ------------------------------------------------------------
# FUNCIÓN: enviar mensaje a Telegram
# parse_mode HTML para negritas y formato
# ------------------------------------------------------------
def enviar_a_telegram(texto):
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "HTML"}
    r = requests.post(url, data=payload)
    print("Telegram status:", r.status_code)
    if r.status_code != 200:
        print("Telegram error:", r.text)

# ------------------------------------------------------------
# FUNCIÓN: formatear mensaje de una operación individual
# ------------------------------------------------------------
def formatear_operacion(op):
    if op is None:
        return None
    if op["tipo"] == "COMPRA":
        return (
            f"🟢 <b>COMPRA SIMULADA</b>\n"
            f"   Activo:     {op['symbol']}\n"
            f"   Precio:     ${op['precio']:.4f}\n"
            f"   Invertido:  ${op['inversion_usd']:.2f} USD\n"
            f"   Cantidad:   {op['cantidad']:.6f}\n"
            f"   Capital disp: ${op['capital_restante']:.2f}"
        )
    if op["tipo"] == "VENTA":
        emoji = "📈" if op["ganancia_usd"] >= 0 else "📉"
        return (
            f"🔴 <b>VENTA SIMULADA</b>\n"
            f"   Activo:    {op['symbol']}\n"
            f"   Entrada:   ${op['precio_entrada']:.4f}\n"
            f"   Salida:    ${op['precio_salida']:.4f}\n"
            f"   {emoji} Resultado: ${op['ganancia_usd']:+.2f} ({op['ganancia_pct']:+.2f}%)\n"
            f"   Capital total: ${op['capital_total']:.2f}"
        )
    return None

# ------------------------------------------------------------
# FUNCIÓN: formatear bloque de acumulado horario
# ------------------------------------------------------------
def formatear_acumulado(acum, hora_str):
    emoji = "🟢" if acum["ganancia_total_usd"] >= 0 else "🔴"
    posiciones = (
        ", ".join(acum["posiciones_abiertas"])
        if acum["posiciones_abiertas"] else "ninguna"
    )
    return (
        f"📊 <b>ACUMULADO {hora_str} hs</b>\n"
        f"──────────────────────\n"
        f"   Capital disp:        ${acum['capital_disponible']:.2f}\n"
        f"   Valor pos. abiertas: ${acum['valor_posiciones']:.2f}\n"
        f"   <b>Patrimonio:    ${acum['patrimonio_total']:.2f}</b>\n"
        f"   {emoji} Gan/Pérd:  ${acum['ganancia_total_usd']:+.2f} ({acum['ganancia_total_pct']:+.2f}%)\n"
        f"   Realizado hoy:       ${acum['ganancia_realizada']:+.2f}\n"
        f"   Ops. hoy:            {acum['operaciones_hoy']}\n"
        f"   Posiciones:          {posiciones}\n"
        f"──────────────────────"
    )

# ------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ------------------------------------------------------------
def main(forzar_envio=False):
    # Hora Argentina (UTC-3)
    ahora_utc = datetime.datetime.utcnow()
    ahora_arg = (ahora_utc.hour - 3) % 24
    hora_str  = f"{ahora_arg:02d}:00"
    fecha_str = ahora_utc.strftime("%d/%m/%Y")

    en_horario = 10 <= ahora_arg < 18

    if not (en_horario or forzar_envio):
        print(f"⏸ Fuera de horario — hora Argentina: {hora_str}")
        return

    print(f"[INFO] Hora Argentina: {hora_str} | Iniciando ciclo")

    # 1. Actualizar datos históricos (descarga solo si falta el día de hoy)
    print("[INFO] Actualizando base de datos histórica...")
    actualizar_todos()

    # 2. Cargar estado de simulación (viene del repo via git pull en bot.yml)
    estado = cargar_estado()
    estado = resetear_dia_si_corresponde(estado)

    # 3. Analizar activos y ejecutar operaciones simuladas
    ops_ejecutadas = []
    lineas_señales = ["<b>📡 Señales este ciclo:</b>"]

    for symbol in ACTIVOS:
        print(f"[INFO] Analizando {symbol}...")
        res    = generar_señal(symbol)
        señal  = res["señal"]
        dk     = res["datos_clave"]
        precio = dk.get("ultimo_cierre", 0)

        emoji_señal = {"COMPRAR": "🟢", "VENDER": "🔴", "MANTENER": "⚪", "SIN DATOS": "❓"}.get(señal, "❓")
        lineas_señales.append(
            f"{emoji_señal} {symbol}: {señal} ({res['confianza']}%)"
            f" | RSI:{dk.get('rsi','?')} | {dk.get('tendencia','?')}"
            f" | ${precio}"
        )

        if precio > 0:
            op = ejecutar_operacion(symbol, señal, precio, estado)
            if op:
                ops_ejecutadas.append(op)
                print(f"  → {op['tipo']} ejecutado: {symbol}")

    # 4. Guardar estado actualizado (bot.yml lo commitea al repo después)
    guardar_estado(estado)

    # 5. Calcular acumulado
    acumulado = calcular_acumulado(estado)

    # 6. Armar mensaje completo para Telegram
    encabezado = (
        f"🤖 <b>Bot Yahoo Finanzas</b>\n"
        f"📅 {fecha_str} — {hora_str} hs ARG\n"
    )

    bloque_señales = "\n".join(lineas_señales)

    if ops_ejecutadas:
        msgs_ops   = [formatear_operacion(op) for op in ops_ejecutadas if op]
        bloque_ops = "\n\n" + "\n\n".join(m for m in msgs_ops if m)
    else:
        bloque_ops = "\n\n⏳ Sin operaciones nuevas este ciclo"

    bloque_acum = "\n\n" + formatear_acumulado(acumulado, hora_str)

    mensaje = encabezado + "\n" + bloque_señales + bloque_ops + bloque_acum

    enviar_a_telegram(mensaje)
    print("[OK] Mensaje enviado a Telegram")

# ------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE PRUEBA (comentada - solo para testear)
# ------------------------------------------------------------
"""
def main(forzar_envio=False):
    # Ajuste de hora UTC a hora Argentina (UTC-3)
    ahora = (datetime.datetime.utcnow().hour - 3) % 24
    if forzar_envio or (10 <= ahora < 18):  # horario de mercado argentino
        symbol = "GGAL.BA"
        decision = decision_inversion(symbol)
        mensaje = f"📊 Bot Yahoo Finanzas\nAcción: {symbol}\nDecisión: {decision.upper()}"
        enviar_a_telegram(mensaje)
    else:
        print("⏸ Fuera del horario de simulación")
# 👇 Este bloque va al final del archivo
if __name__ == "__main__":
    main(forzar_envio=True)   # para probar ahora mismo
"""

# ------------------------------------------------------------
# EJECUCIÓN DEL SCRIPT
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
