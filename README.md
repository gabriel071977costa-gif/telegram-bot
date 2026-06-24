# 🤖 Trading Señales — Bot de Simulación con Telegram

Sistema de bots conectados que analiza activos financieros (acciones, cripto, ETFs) y simula operaciones de compra/venta en tiempo real, publicando resultados automáticamente en un canal de Telegram.

📡 **Canal en vivo:** [@tradingSenalesArg](https://t.me/tradingSenalesArg)
👀 **Ejemplo de señal real:** [Ver mensaje](https://t.me/tradingSenalesArg/20)

> ⚠️ **Importante:** Este proyecto es una **simulación educativa**. No opera con dinero real y no constituye asesoramiento financiero de ningún tipo.

---

## 🧩 Arquitectura

El sistema está compuesto por tres bots que trabajan en conjunto:

```
┌─────────────────────┐       ┌──────────────────┐       ┌─────────────────────┐
│ bot_yahooFinanzas.py │──────▶│  GitHub (JSON)    │◀─────│   comandos.py        │
│ Analiza activos y    │       │  Estado de la      │      │  Responde comandos   │
│ simula compra/venta   │       │  simulación        │      │  en Telegram          │
└─────────────────────┘       └──────────────────┘       └─────────────────────┘
                                                                     │
                                                                     ▼
                                                          ┌─────────────────────┐
                                                          │  bot_telegram.py     │
                                                          │  Webhook (Flask)     │
                                                          │  Corre 24/7 en Render│
                                                          └─────────────────────┘
                                                                     │
                                                                     ▼
                                                          ┌─────────────────────┐
                                                          │  Canal de Telegram   │
                                                          │  @tradingSenalesArg  │
                                                          └─────────────────────┘
```

- **`bot_yahooFinanzas.py`** — Trae datos de Yahoo Finance, calcula indicadores (RSI) y decide señales de COMPRA/VENTA sobre una cartera simulada.
- **`bot_telegram.py`** — Corre 24/7 en [Render](https://render.com), recibe mensajes vía webhook (Flask) y publica las señales en el canal.
- **`comandos.py`** — Procesa los comandos que los usuarios escriben en Telegram, leyendo el estado actual desde GitHub.

## 🛠️ Stack técnico

- **Python 3**
- **Flask** — servidor webhook para recibir actualizaciones de Telegram
- **pyTelegramBotAPI** — integración con la API de Telegram
- **yfinance** — datos de mercado en tiempo real
- **Render** — hosting del bot principal (24/7)
- **GitHub API** — persistencia del estado de la simulación (JSON)

## 📋 Comandos disponibles

| Comando | Descripción |
|---|---|
| `/ayuda` | Lista de comandos disponibles |
| `/estado` | Posiciones abiertas y capital actual |
| `/historial` | Últimas 5 operaciones realizadas |
| `/balance` | Capital disponible y ganancia/pérdida total |
| `/stats` | Winrate, drawdown máximo y profit factor calculados sobre el historial completo |
| `/activos` | Lista de activos que opera el bot |
| `/agro` | Resumen de activos del sector agro |
| `/analizar [activo]` | Análisis puntual de un activo |
| `/buscar [nombre]` | Busca el código/ticker de un activo por nombre |
| `/ping` | Verifica que el bot esté activo |

### Ejemplo de salida — `/stats`

```
📊 ESTADÍSTICAS DE PERFORMANCE
──────────────────────
🎯 Operaciones cerradas: 24
🟢 Winrate: 58.3% (14G / 10P)
📈 Ganancia promedio: +$12.40
📉 Pérdida promedio: -$8.70
⚖️ Profit factor: 1.89
🔻 Drawdown máximo: -$33.20 (3.3%)
```

## 📊 Métricas calculadas

- **Winrate** — porcentaje de operaciones cerradas en ganancia.
- **Profit factor** — relación entre ganancias totales y pérdidas totales.
- **Drawdown máximo** — mayor caída de capital registrada, reconstruida a partir del historial de operaciones cerradas.

## 🚀 Sobre este repositorio

Este código es de **acceso público para lectura** — podés explorarlo y ver cómo está armado. El código **no cuenta con una licencia de uso abierto**: todos los derechos quedan reservados al autor. Si te interesa usar parte de esta lógica en tu propio proyecto, escribime primero.

## 👤 Autor

Desarrollado por **[@Gabriel_Dev_Arg](https://t.me/Gabriel_Dev_Arg)**

¿Buscás un bot a medida (trading, automatización, Telegram + IA)? Escribime por Telegram.
