# balance_diario.py
# ------------------------------------------------------------
# Registro y cálculo de balance diario del bot Ruk.
# Guarda cada operación en un archivo CSV y calcula ganancias.
# ------------------------------------------------------------

import csv
import os
import datetime

ARCHIVO = "operaciones.csv"

# ------------------------------------------------------------
# FUNCIÓN: guardar operación
# ------------------------------------------------------------
def balance_diario(symbol, resultado, cantidad, precio):
    """Guarda una operación en el archivo CSV"""
    existe = os.path.isfile(ARCHIVO)
    with open(ARCHIVO, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["fecha", "symbol", "accion", "cantidad", "precio"])
        writer.writerow([
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            resultado,
            cantidad,
            precio
        ])

# ------------------------------------------------------------
# FUNCIÓN: calcular balance acumulado
# ------------------------------------------------------------
def calcular_balance():
    """Calcula ganancias/pérdidas acumuladas"""
    if not os.path.isfile(ARCHIVO):
        return 0.0

    balance = 0.0
    with open(ARCHIVO, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            accion = row["accion"]
            cantidad = float(row["cantidad"])
            precio = float(row["precio"])
            if "compra" in accion.lower():
                balance -= cantidad * precio
            elif "venta" in accion.lower():
                balance += cantidad * precio

    return balance

# ------------------------------------------------------------
# FUNCIÓN: balance del día actual
# ------------------------------------------------------------
def balance_hoy():
    """Devuelve balance del día actual"""
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    total = 0.0
    if not os.path.isfile(ARCHIVO):
        return total
    with open(ARCHIVO, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["fecha"].startswith(hoy):
                accion = row["accion"].lower()
                cantidad = float(row["cantidad"])
                precio = float(row["precio"])
                if "compra" in accion:
                    total -= cantidad * precio
                elif "venta" in accion:
                    total += cantidad * precio
    return total

