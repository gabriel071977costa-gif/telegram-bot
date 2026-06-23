# ============================================================
# ESTADÍSTICAS DE PERFORMANCE
# Winrate, drawdown y métricas calculadas sobre el historial
# completo de operaciones cerradas.
# Se integra con comandos.py
# ============================================================

# Importamos las funciones que ya existen en comandos.py
# para no duplicar código (leer de GitHub y enviar a Telegram)
from comandos import leer_json_github, enviar_a_telegram


def ejecutar_stats(chat_id):
    """
    Calcula y envía estadísticas de performance:
    winrate, ganancia/pérdida promedio, profit factor y drawdown máximo.
    """
    estado = leer_json_github("estado_simulacion.json")
    if not estado:
        enviar_a_telegram(chat_id, "❌ No pude leer el historial desde GitHub.")
        return

    historial = estado.get("historial", [])
    cap_ini = estado.get("capital_inicial", 1000)

    # Solo nos interesan las VENTAS, que son las que tienen resultado
    ventas = [op for op in historial if op.get("tipo") == "VENTA"]

    if not ventas:
        enviar_a_telegram(chat_id, "📊 Todavía no hay operaciones cerradas para calcular estadísticas.")
        return

    # --- WINRATE ---
    total_ops = len(ventas)
    ganadoras = [op for op in ventas if op.get("ganancia_usd", 0) >= 0]
    perdedoras = [op for op in ventas if op.get("ganancia_usd", 0) < 0]
    winrate = round(len(ganadoras) / total_ops * 100, 1)

    # --- GANANCIA / PÉRDIDA PROMEDIO ---
    ganancia_prom = round(sum(op.get("ganancia_usd", 0) for op in ganadoras) / len(ganadoras), 2) if ganadoras else 0
    perdida_prom = round(sum(op.get("ganancia_usd", 0) for op in perdedoras) / len(perdedoras), 2) if perdedoras else 0

    # --- PROFIT FACTOR ---
    # (suma de ganancias) / (suma de pérdidas en valor absoluto)
    suma_ganancias = sum(op.get("ganancia_usd", 0) for op in ganadoras)
    suma_perdidas = abs(sum(op.get("ganancia_usd", 0) for op in perdedoras))
    if suma_perdidas > 0:
        profit_factor = round(suma_ganancias / suma_perdidas, 2)
        pf_texto = f"{profit_factor}"
    else:
        pf_texto = "∞ (sin pérdidas)"

    # --- DRAWDOWN ---
    # Reconstruimos la curva de capital sumando cada ganancia/pérdida
    # en orden cronológico, arrancando desde el capital inicial.
    # Es una aproximación: solo capta los puntos donde se cierra
    # una operación, no las fluctuaciones intra-operación.
    curva_capital = [cap_ini]
    capital_actual = cap_ini
    for op in ventas:
        capital_actual += op.get("ganancia_usd", 0)
        curva_capital.append(capital_actual)

    pico = curva_capital[0]
    max_drawdown_usd = 0
    max_drawdown_pct = 0
    for valor in curva_capital:
        if valor > pico:
            pico = valor
        caida_usd = pico - valor
        caida_pct = (caida_usd / pico * 100) if pico > 0 else 0
        if caida_usd > max_drawdown_usd:
            max_drawdown_usd = caida_usd
            max_drawdown_pct = caida_pct

    # --- MENSAJE FINAL ---
    emoji_wr = "🟢" if winrate >= 50 else "🔴"
    enviar_a_telegram(chat_id,
        f"📊 <b>ESTADÍSTICAS DE PERFORMANCE</b>\n"
        f"──────────────────────\n"
        f"🎯 Operaciones cerradas: <b>{total_ops}</b>\n"
        f"{emoji_wr} Winrate: <b>{winrate}%</b> ({len(ganadoras)}G / {len(perdedoras)}P)\n"
        f"📈 Ganancia promedio: <b>${ganancia_prom:+.2f}</b>\n"
        f"📉 Pérdida promedio: <b>${perdida_prom:+.2f}</b>\n"
        f"⚖️ Profit factor: <b>{pf_texto}</b>\n"
        f"🔻 Drawdown máximo: <b>-${max_drawdown_usd:.2f} ({max_drawdown_pct:.1f}%)</b>\n"
        f"──────────────────────\n"
        f"<i>⚠️ Drawdown aproximado: calculado solo sobre los cierres de operación, "
        f"no sobre fluctuaciones intradiarias.</i>"
    )
