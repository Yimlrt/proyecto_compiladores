import re
from dataclasses import dataclass, field
from typing import Optional


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


@dataclass
class Token:
    tipo: str
    valor: str
    posicion: int
    linea: int = 0

    def __repr__(self):
        return f"Token({self.tipo}, {self.valor!r}, pos={self.posicion})"


def tokenizar(linea: str, num_linea: int = 0) -> tuple[list[Token], list[str]]:
    """
    Tokeniza una línea. Retorna (tokens_validos, errores_lexicos).
    """
    tokens = []
    errores = []
    for m in PATRON_MAESTRO.finditer(linea):
        tipo  = m.lastgroup
        valor = m.group()
        pos   = m.start()
        if tipo == "ESPACIO":
            continue
        if tipo == "DESCONOCIDO":
            errores.append(f"  ERROR LÉXICO en posición {pos}: carácter inesperado '{valor}'")
            continue
        tokens.append(Token(tipo, valor, pos, num_linea))
    return tokens, errores




@dataclass
class Simbolo:
    nombre: str
    tipo: str
    valor: Optional[str] = None
    linea_declaracion: int = 0
    inicializado: bool = False


class TablaSimbolos:
    def __init__(self):
        self._tabla: dict[str, Simbolo] = {}

    def declarar(self, nombre: str, tipo: str, linea: int) -> tuple[bool, str]:
        if nombre in self._tabla:
            return False, f"Variable '{nombre}' ya fue declarada en línea {self._tabla[nombre].linea_declaracion}"
        self._tabla[nombre] = Simbolo(nombre, tipo, linea_declaracion=linea)
        return True, f"Variable '{nombre}' de tipo {tipo} registrada."

    def asignar(self, nombre: str, valor: str) -> tuple[bool, str]:
        if nombre not in self._tabla:
            return False, f"Variable '{nombre}' no declarada."
        self._tabla[nombre].valor = valor
        self._tabla[nombre].inicializado = True
        return True, "OK"

    def existe(self, nombre: str) -> bool:
        return nombre in self._tabla

    def obtener(self, nombre: str) -> Optional[Simbolo]:
        return self._tabla.get(nombre)

    def imprimir(self):
        if not self._tabla:
            print("  (tabla vacía)")
            return
        print(f"  {'Nombre':<15} {'Tipo':<10} {'Inicializado':<14} {'Valor':<20} {'Línea'}")
        print("  " + "-" * 65)
        for s in self._tabla.values():
            val = s.valor if s.valor is not None else "—"
            print(f"  {s.nombre:<15} {s.tipo:<10} {'Sí' if s.inicializado else 'No':<14} {val:<20} {s.linea_declaracion}")




class AnalizadorSintactico:
    """
    Gramática soportada:
      S  → DECLARACION | CAPTURA | ASIGNACION | SALIDA
      DECLARACION → IDENTIFICADOR TIPO_DATO PUNTO_COMA
      CAPTURA     → IDENTIFICADOR ASIGNACION CAPTURA_TIPO PUNTO_COMA
      ASIGNACION  → IDENTIFICADOR ASIGNACION EXPR PUNTO_COMA
      SALIDA      → MENSAJE_TEXTO TEXTO_LIT PARENTESIS_CI PUNTO_COMA
      EXPR        → TERMINO (OPERADOR TERMINO)*
      TERMINO     → IDENTIFICADOR | ENTERO_LIT | REAL_LIT | TEXTO_LIT
                  | LOGICO_LIT | PARENTESIS_AP EXPR PARENTESIS_CI
    """

    def __init__(self, tabla: TablaSimbolos):
        self.tabla = tabla
        self.tokens: list[Token] = []
        self.pos = 0
        self.errores: list[str] = []

    def actual(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consumir(self, tipo_esperado: str) -> Optional[Token]:
        t = self.actual()
        if t and t.tipo == tipo_esperado:
            self.pos += 1
            return t
        esperado = tipo_esperado
        obtenido = f"{t.tipo}('{t.valor}')" if t else "fin de línea"
        self.errores.append(f"  ERROR SINTÁCTICO: se esperaba {esperado}, se obtuvo {obtenido}")
        return None

    def analizar(self, tokens: list[Token]) -> tuple[str, list[str]]:
        """
        Intenta reconocer la sentencia. Retorna (tipo_sentencia, errores).
        """
        self.tokens = tokens
        self.pos = 0
        self.errores = []

        if not tokens:
            return "LINEA_VACIA", []

        t = self.actual()
        if t is None:
            return "DESCONOCIDO", []

        # Declaración: IDENTIFICADOR TIPO_DATO PUNTO_COMA
        if t.tipo == "IDENTIFICADOR" and self._ver_siguiente("TIPO_DATO"):
            return self._declaracion()

        # Captura / Asignación: IDENTIFICADOR ASIGNACION ...
        if t.tipo == "IDENTIFICADOR" and self._ver_siguiente("ASIGNACION"):
            nombre_var = t.valor
            self.pos += 2  # saltar ID y =
            sig = self.actual()
            self.pos = 0  # resetear para re-parse correcto
            if sig and sig.tipo == "CAPTURA_TIPO":
                return self._captura()
            else:
                return self._asignacion()

       
        if t.tipo == "MENSAJE_TEXTO":
            return self._salida()

        self.errores.append(f"  ERROR SINTÁCTICO: sentencia no reconocida, empieza con {t.tipo}('{t.valor}')")
        return "DESCONOCIDO", self.errores

    def _ver_siguiente(self, tipo: str) -> bool:
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1].tipo == tipo
        return False

   
    def _declaracion(self) -> tuple[str, list[str]]:
        id_tok  = self.consumir("IDENTIFICADOR")
        tip_tok = self.consumir("TIPO_DATO")
        self.consumir("PUNTO_COMA")
        if not self.errores and id_tok and tip_tok:
            ok, msg = self.tabla.declarar(id_tok.valor, tip_tok.valor, id_tok.linea)
            if not ok:
                self.errores.append(f"  ERROR SEMÁNTICO: {msg}")
        return "DECLARACION", self.errores

    def _captura(self) -> tuple[str, list[str]]:
        id_tok  = self.consumir("IDENTIFICADOR")
        self.consumir("ASIGNACION")
        cap_tok = self.consumir("CAPTURA_TIPO")
        self.consumir("PUNTO_COMA")
        if not self.errores and id_tok and cap_tok:
            # verificar que la variable esté declarada
            if not self.tabla.existe(id_tok.valor):
                self.errores.append(f"  ERROR SEMÁNTICO: variable '{id_tok.valor}' no declarada antes de usarla.")
            else:
                # verificar compatibilidad de tipo
                tipo_captura = re.search(r'\.(Entero|Real|Texto|Logico)', cap_tok.valor).group(1)
                sim = self.tabla.obtener(id_tok.valor)
                if sim.tipo != tipo_captura:
                    self.errores.append(
                        f"  ADVERTENCIA TIPO: '{id_tok.valor}' es {sim.tipo} "
                        f"pero se captura como {tipo_captura}."
                    )
                self.tabla.asignar(id_tok.valor, f"Captura.{tipo_captura}()")
        return "CAPTURA", self.errores

    def _asignacion(self) -> tuple[str, list[str]]:
        id_tok = self.consumir("IDENTIFICADOR")
        self.consumir("ASIGNACION")
        expr_val = self._expr()
        self.consumir("PUNTO_COMA")
        if not self.errores and id_tok:
            if not self.tabla.existe(id_tok.valor):
                self.errores.append(
                    f"  ADVERTENCIA: variable '{id_tok.valor}' no declarada "
                    f"(asignación implícita no recomendada)."
                )
            else:
                self.tabla.asignar(id_tok.valor, expr_val)
        return "ASIGNACION", self.errores

    def _salida(self) -> tuple[str, list[str]]:
        self.consumir("MENSAJE_TEXTO")
        txt = self.consumir("TEXTO_LIT")
        self.consumir("PARENTESIS_CI")
        self.consumir("PUNTO_COMA")
        return "SALIDA", self.errores

    def _expr(self) -> str:
        """Parsea una expresión y retorna su representación textual."""
        partes = [self._termino()]
        while self.actual() and self.actual().tipo == "OPERADOR":
            op = self.consumir("OPERADOR")
            partes.append(op.valor if op else "?")
            partes.append(self._termino())
        return " ".join(str(p) for p in partes)

    def _termino(self) -> str:
        t = self.actual()
        if t is None:
            self.errores.append("  ERROR SINTÁCTICO: se esperaba un término, pero la línea terminó.")
            return "?"
        if t.tipo in ("IDENTIFICADOR", "ENTERO_LIT", "REAL_LIT",
                       "TEXTO_LIT", "LOGICO_LIT"):
            self.pos += 1
            return t.valor
        if t.tipo == "PARENTESIS_AP":
            self.consumir("PARENTESIS_AP")
            val = self._expr()
            self.consumir("PARENTESIS_CI")
            return f"({val})"
        self.errores.append(
            f"  ERROR SINTÁCTICO: término inesperado {t.tipo}('{t.valor}')"
        )
        return "?"



def compilar(codigo: str) -> None:
    tabla   = TablaSimbolos()
    parser  = AnalizadorSintactico(tabla)
    lineas  = codigo.strip().split("\n")

    print("=" * 65)
    print("  COMPILADOR – Fase 1 (Léxico) + Fase 2 (Sintáctico)")
    print("=" * 65)

    total_errores = 0

    for num, linea in enumerate(lineas, start=1):
        linea = linea.strip()
        if not linea:
            continue

        tokens, err_lex = tokenizar(linea, num)

     
        tipo_sent, err_sint = parser.analizar(tokens)

        todos_errores = err_lex + err_sint
        total_errores += len(todos_errores)

        estado = "✓ OK" if not todos_errores else f"✗ {len(todos_errores)} error(es)"
        print(f"\n[Línea {num:>2}] [{tipo_sent:<12}] {estado}")
        print(f"  Código : {linea}")

        # Mostrar tokens
        token_str = " → ".join(f"{t.tipo}({t.valor!r})" for t in tokens)
        print(f"  Tokens : {token_str}")

        for e in todos_errores:
            print(e)

    print("\n" + "=" * 65)
    print("  TABLA DE SÍMBOLOS")
    print("=" * 65)
    tabla.imprimir()

    
    estado_final = "Bacano" if total_errores == 0 else f"{total_errores} errores , BARRO"
    print(f"  Resultado: {estado_final}")
    print("=" * 65)




if __name__ == "__main__":
    codigo_prueba = """

    

A Entero;    
suma Entero;
pi Real;
num2 Entero;
num3 Entero;    

num1 Entero;
nombre Texto;
n1 Real;
asis Logico;
nombre= Captura.Texto();
n1= Captura.Real();
num1= Captura.Entero();
asis=Captura.Logico();
A=b;
suma=num1+(num2*num3);
nombre="Alejandra";
pi=3.1416;
Mensaje.Texto("Esto es una prueba");
Mensaje.Texto("Hola mundo");
"""
    compilar(codigo_prueba)