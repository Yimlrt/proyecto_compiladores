import re


TIPOS_DATO = {"Entero", "Real", "Texto", "Logico"}

TOKENS_DEF = [
    ("CAPTURA_TIPO",   r'Captura\.(Entero|Real|Texto|Logico)\(\)'),
    ("MENSAJE_TEXTO",  r'Mensaje\.Texto\('),
    ("TIPO_DATO",      r'\b(Entero|Real|Texto|Logico)\b'),
    ("LOGICO_LIT",     r'\b(verdadero|falso|true|false)\b'),
    ("REAL_LIT",       r'\b\d+[.,]\d+\b'),
    ("ENTERO_LIT",     r'\b\d+\b'),
    ("TEXTO_LIT",      r'"[^"]*"'),
    ("IDENTIFICADOR",  r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ("OPERADOR",       r'[+\-*/]'),
    ("COMPARADOR",     r'(==|!=|<=|>=|<|>)'),
    ("ASIGNACION",     r'='),
    ("PARENTESIS_AP",  r'\('),
    ("PARENTESIS_CI",  r'\)'),
    ("PUNTO_COMA",     r';'),
    ("PUNTO",          r'\.'),
    ("COMA",           r','),
    ("ESPACIO",        r'\s+'),
    ("DESCONOCIDO",    r'.'),
]

PATRON_MAESTRO = re.compile(
    '|'.join(f'(?P<{nombre}>{patron})' for nombre, patron in TOKENS_DEF)
)


def tokenizar(linea: str) -> list[dict]:
    """
    Recorre la línea de izquierda a derecha y genera la lista de tokens.
    Retorna una lista de dicts: {tipo, valor, posicion}
    """
    tokens = []
    for m in PATRON_MAESTRO.finditer(linea):
        tipo = m.lastgroup
        valor = m.group()
        pos   = m.start()

        if tipo == "ESPACIO":          # ignorar blancos
            continue
        if tipo == "DESCONOCIDO":
            tokens.append({"tipo": "ERROR_LEXICO", "valor": valor, "posicion": pos})
            continue

        tokens.append({"tipo": tipo, "valor": valor, "posicion": pos})

    return tokens




def clasificar_sentencia(tokens: list[dict]) -> str:
    """Identifica de qué tipo de instrucción se trata."""
    tipos = [t["tipo"] for t in tokens]
    valores = [t["valor"] for t in tokens]

    if not tokens:
        return "LINEA_VACIA"

    
    if (len(tokens) >= 2
            and tipos[0] == "IDENTIFICADOR"
            and tipos[1] == "TIPO_DATO"):
        return "DECLARACION"

   
    if (len(tokens) >= 3
            and tipos[0] == "IDENTIFICADOR"
            and tipos[1] == "ASIGNACION"
            and tipos[2] == "CAPTURA_TIPO"):
        return "CAPTURA"

    
    if tipos[0] == "MENSAJE_TEXTO":
        return "SALIDA"

    
    if (len(tokens) >= 3
            and tipos[0] == "IDENTIFICADOR"
            and tipos[1] == "ASIGNACION"):
        return "ASIGNACION"

    return "DESCONOCIDO"




def analizar_codigo(codigo: str) -> None:
    """Procesa un bloque de código línea por línea."""
    lineas = codigo.strip().split("\n")
    print("=" * 60)
    print("  ANALIZADOR LÉXICO — Tokenizador")
    print("=" * 60)

    for num, linea in enumerate(lineas, start=1):
        linea = linea.strip()
        if not linea:
            continue

        tokens = tokenizar(linea)
        tipo_sent = clasificar_sentencia(tokens)

        print(f"\n[Línea {num}] {linea}")
        print(f"  Tipo de sentencia : {tipo_sent}")
        print(f"  {'Pos':<5} {'Token':<18} {'Valor'}")
        print("  " + "-" * 42)
        for t in tokens:
            print(f"  {t['posicion']:<5} {t['tipo']:<18} {t['valor']}")

    print("\n" + "=" * 60)
    print("  Análisis completado.")
    print("=" * 60)



if __name__ == "__main__":
    try:
        # Cambia "entrada.txt" por "prueba.txt" aquí:
        with open("prueba.txt", "r") as archivo:
            codigo_fuente = archivo.read()
        
        analizar_codigo(codigo_fuente)
        
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'prueba.txt'.")