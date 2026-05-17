# balance_diario.py
# ------------------------------------------------------------
# Registro de operaciones y cálculo de balance diario.
# ------------------------------------------------------------

import csv
import os
from datetime import datetime

ARCHIVO_BALANCE = "balance_diario.csv"

# Inicializar archivo si no existe
if not os.path.exists(ARCHIVO_BALANCE):
    with open(ARCHIVO_BALANCE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["fecha", "symbol", "accion", "cantidad", "precio", "total_usdt"])

def registrar_operacion(symbol, accion, cantidad, precio, total_usdt):
    """Guarda una operación en el archivo CSV"""
    with open(ARCHIVO_BALANCE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), symbol, accion, cantidad, precio, total_usdt])

def calcular_balance():
    """Calcula ganancias/pérdidas acumuladas"""
    total = 0.0
    with open(ARCHIVO_BALANCE, mode="r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["accion"].lower() == "comprar":
                total -= float(row["total_usdt"])
            elif row["accion"].lower() == "vender":
                total += float(row["total_usdt"])
    return total

def balance_diario():
    """Devuelve balance del día actual"""
    hoy = datetime.now().strftime("%Y-%m-%d")
    total = 0.0
    with open(ARCHIVO_BALANCE, mode="r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["fecha"].startswith(hoy):
                if row["accion"].lower() == "comprar":
                    total -= float(row["total_usdt"])
                elif row["accion"].lower() == "vender":
                    total += float(row["total_usdt"])
    return total
