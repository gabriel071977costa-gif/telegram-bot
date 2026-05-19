# preguntas.py

def es_preguntas(texto: str) -> bool:
    texto = texto.lower()
    variantes = [
        "cómo te llamas",
        "como te llamas",
        "Como te llamas",
        "tu nombre",
        "Tu nombre",
        "tu nombre bot",
        "quién sos",
        "quien sos",
        "Quien sos",
        "cómo te dicen",
        "como te dicen",
        "cuál es tu nombre",
        "cual es tu nombre",
        "te llamas",
        "nombre del bot",
        "nombre del asistente"
    ]
    return any(frase in texto for frase in variantes)
