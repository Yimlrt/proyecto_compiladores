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
                # intentar evaluar numéricamente sustituyendo valores conocidos
                valor_evaluado = self._evaluar_expr(expr_val)
                self.tabla.asignar(id_tok.valor, valor_evaluado)
        return "ASIGNACION", self.errores

    def _evaluar_expr(self, expr: str) -> str:
        """
        Intenta evaluar una expresión sustituyendo variables por sus valores
        numéricos conocidos en la tabla de símbolos. Si no puede, devuelve
        la expresión original como texto.
        """
        expr_eval = expr
        # sustituir cada identificador por su valor numérico si está disponible
        for nombre, sim in self.tabla._tabla.items():
            if sim.valor is not None:
                val = sim.valor.replace(",", ".")
                try:
                    float(val)  # solo sustituir si el valor es numérico
                    # reemplazar palabra completa
                    expr_eval = re.sub(rf'\b{re.escape(nombre)}\b', val, expr_eval)
                except ValueError:
                    pass
        # normalizar comas decimales a puntos para eval
        expr_eval_norm = expr_eval.replace(",", ".")
        try:
            resultado = eval(expr_eval_norm)  # noqa: S307
            # formatear: entero si no tiene decimales
            if isinstance(resultado, float) and resultado == int(resultado):
                return str(int(resultado))
            return str(resultado)
        except Exception:
            return expr  # si no se puede evaluar, guardar la expresión textual

    def _salida(self) -> tuple[str, list[str]]:
        self.consumir("MENSAJE_TEXTO")
        # acepta: TEXTO_LIT | IDENTIFICADOR | TEXTO_LIT , IDENTIFICADOR
        argumentos = []
        t = self.actual()
        while t and t.tipo != "PARENTESIS_CI" and t.tipo != "PUNTO_COMA":
            if t.tipo in ("TEXTO_LIT", "IDENTIFICADOR", "ENTERO_LIT", "REAL_LIT", "LOGICO_LIT"):
                argumentos.append(t)
                self.pos += 1
            elif t.tipo == "COMA":
                self.pos += 1  # separador, ignorar
            else:
                break
            t = self.actual()
        self.consumir("PARENTESIS_CI")
        self.consumir("PUNTO_COMA")

        # validar que variables usadas estén declaradas
        for arg in argumentos:
            if arg.tipo == "IDENTIFICADOR" and not self.tabla.existe(arg.valor):
                self.errores.append(
                    f"  ADVERTENCIA: variable '{arg.valor}' usada en Mensaje.Texto() no está declarada."
                )
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



# ═══════════════════════════════════════════════════════════════
#  FASE 3 — GENERACIÓN DE CÓDIGO INTERMEDIO (cuádruplas / 3 dir.)
# ═══════════════════════════════════════════════════════════════

@dataclass
class Cuadrupla:
    op:     str
    arg1:   str
    arg2:   str
    result: str

    def __str__(self):
        return f"({self.op:<12} {self.arg1:<12} {self.arg2:<12} {self.result})"


class GeneradorIntermedio:
    """Genera código de tres direcciones a partir del AST implícito del parser."""

    def __init__(self):
        self.cuadruplas: list[Cuadrupla] = []
        self._temp_count = 0
        self._label_count = 0

    def _nuevo_temp(self) -> str:
        self._temp_count += 1
        return f"t{self._temp_count}"

    def _nueva_etiqueta(self) -> str:
        self._label_count += 1
        return f"L{self._label_count}"

    def generar(self, tipo_sent: str, tokens: list[Token]) -> list[Cuadrupla]:
        """Genera cuádruplas para una sentencia ya validada."""
        inicio = len(self.cuadruplas)
        if tipo_sent == "DECLARACION":
            self._gen_declaracion(tokens)
        elif tipo_sent == "CAPTURA":
            self._gen_captura(tokens)
        elif tipo_sent == "ASIGNACION":
            self._gen_asignacion(tokens)
        elif tipo_sent == "SALIDA":
            self._gen_salida(tokens)
        return self.cuadruplas[inicio:]

    # ── helpers internos ──────────────────────────────────────────
    def _gen_declaracion(self, tokens):
        id_tok  = next((t for t in tokens if t.tipo == "IDENTIFICADOR"), None)
        tip_tok = next((t for t in tokens if t.tipo == "TIPO_DATO"), None)
        if id_tok and tip_tok:
            self.cuadruplas.append(
                Cuadrupla("DECL", tip_tok.valor, "", id_tok.valor)
            )

    def _gen_captura(self, tokens):
        id_tok  = next((t for t in tokens if t.tipo == "IDENTIFICADOR"), None)
        cap_tok = next((t for t in tokens if t.tipo == "CAPTURA_TIPO"), None)
        if id_tok and cap_tok:
            self.cuadruplas.append(
                Cuadrupla("READ", cap_tok.valor, "", id_tok.valor)
            )

    def _gen_asignacion(self, tokens):
        # tokens: ID = expr ;
        id_tok = tokens[0]
        expr_tokens = []
        i = 2
        while i < len(tokens) and tokens[i].tipo != "PUNTO_COMA":
            expr_tokens.append(tokens[i])
            i += 1
        resultado = self._gen_expr(expr_tokens)
        if resultado != id_tok.valor:
            self.cuadruplas.append(
                Cuadrupla("ASSIGN", resultado, "", id_tok.valor)
            )

    def _gen_salida(self, tokens):
        txt_tok = next((t for t in tokens if t.tipo == "TEXTO_LIT"), None)
        if txt_tok:
            self.cuadruplas.append(
                Cuadrupla("PRINT", txt_tok.valor, "", "")
            )

    def _gen_expr(self, tokens: list[Token]) -> str:
        """Genera cuádruplas para una expresión y retorna el resultado."""
        # Manejo de paréntesis y operadores con precedencia básica
        # Usamos un enfoque de pila simple (sin precedencia compleja)
        operandos = []
        operadores = []

        def aplicar_op():
            if len(operandos) >= 2 and operadores:
                op  = operadores.pop()
                r   = operandos.pop()
                l   = operandos.pop()
                tmp = self._nuevo_temp()
                self.cuadruplas.append(Cuadrupla(op, l, r, tmp))
                operandos.append(tmp)

        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.tipo in ("IDENTIFICADOR", "ENTERO_LIT", "REAL_LIT",
                          "TEXTO_LIT", "LOGICO_LIT"):
                operandos.append(t.valor)
            elif t.tipo == "OPERADOR":
                # precedencia: * / antes que + -
                while (operadores and operadores[-1] in ("*", "/")
                       and t.valor in ("+", "-")):
                    aplicar_op()
                operadores.append(t.valor)
            elif t.tipo == "PARENTESIS_AP":
                operadores.append("(")
            elif t.tipo == "PARENTESIS_CI":
                while operadores and operadores[-1] != "(":
                    aplicar_op()
                if operadores:
                    operadores.pop()  # quitar "("
            i += 1

        while operadores:
            aplicar_op()

        return operandos[0] if operandos else "?"


# ═══════════════════════════════════════════════════════════════
#  FASE 4 — OPTIMIZACIÓN DE CÓDIGO INTERMEDIO
# ═══════════════════════════════════════════════════════════════

class OptimizadorCodigo:
    """
    Aplica optimizaciones sobre la lista de cuádruplas:
      1. Plegado de constantes  (2 + 3  →  5)
      2. Eliminación de asignaciones redundantes  (t1 = t1)
      3. Propagación de copias  (t1 = x; y = t1  →  y = x)
      4. Eliminación de temporales no usados
    """

    def __init__(self):
        self.log: list[str] = []   # registro de optimizaciones aplicadas

    def optimizar(self, cuadruplas: list[Cuadrupla]) -> list[Cuadrupla]:
        self.log = []
        resultado = list(cuadruplas)
        resultado = self._plegar_constantes(resultado)
        resultado = self._eliminar_redundantes(resultado)
        resultado = self._propagar_copias(resultado)
        resultado = self._eliminar_temporales_muertos(resultado)
        if not self.log:
            self.log.append("  Sin optimizaciones aplicables.")
        return resultado

    # ── 1. Plegado de constantes ──────────────────────────────────
    def _plegar_constantes(self, cuads: list[Cuadrupla]) -> list[Cuadrupla]:
        resultado = []
        for c in cuads:
            if c.op in ("+", "-", "*", "/") and self._es_numero(c.arg1) and self._es_numero(c.arg2):
                try:
                    a = float(c.arg1.replace(",", "."))
                    b = float(c.arg2.replace(",", "."))
                    if   c.op == "+": val = a + b
                    elif c.op == "-": val = a - b
                    elif c.op == "*": val = a * b
                    elif c.op == "/": val = a / b if b != 0 else 0
                    val_str = str(int(val)) if val == int(val) else str(val)
                    self.log.append(
                        f"  Plegado de constantes: {c.arg1} {c.op} {c.arg2} → {val_str}  (en {c.result})"
                    )
                    resultado.append(Cuadrupla("ASSIGN", val_str, "", c.result))
                    continue
                except Exception:
                    pass
            resultado.append(c)
        return resultado

    # ── 2. Eliminar asignaciones redundantes (x = x) ─────────────
    def _eliminar_redundantes(self, cuads: list[Cuadrupla]) -> list[Cuadrupla]:
        resultado = []
        for c in cuads:
            if c.op == "ASSIGN" and c.arg1 == c.result:
                self.log.append(f"  Asignación redundante eliminada: {c.result} = {c.arg1}")
                continue
            resultado.append(c)
        return resultado

    # ── 3. Propagación de copias ──────────────────────────────────
    def _propagar_copias(self, cuads: list[Cuadrupla]) -> list[Cuadrupla]:
        copias: dict[str, str] = {}
        resultado = []
        for c in cuads:
            # sustituir usos de temporales copiados
            arg1 = copias.get(c.arg1, c.arg1)
            arg2 = copias.get(c.arg2, c.arg2)
            if arg1 != c.arg1 or arg2 != c.arg2:
                self.log.append(
                    f"  Propagación de copia: {c.arg1} → {arg1}"
                    + (f", {c.arg2} → {arg2}" if arg2 != c.arg2 else "")
                )
                c = Cuadrupla(c.op, arg1, arg2, c.result)
            # registrar nueva copia
            if c.op == "ASSIGN" and c.arg2 == "":
                copias[c.result] = c.arg1
            else:
                # si el resultado se redefine, invalidar copia anterior
                copias.pop(c.result, None)
            resultado.append(c)
        return resultado

    # ── 4. Eliminar temporales muertos ────────────────────────────
    def _eliminar_temporales_muertos(self, cuads: list[Cuadrupla]) -> list[Cuadrupla]:
        # calcular qué temporales se usan como argumento
        usados: set[str] = set()
        for c in cuads:
            if c.arg1: usados.add(c.arg1)
            if c.arg2: usados.add(c.arg2)

        resultado = []
        for c in cuads:
            es_temp = c.result.startswith("t") and c.result[1:].isdigit()
            if es_temp and c.result not in usados:
                self.log.append(f"  Temporal muerto eliminado: {c.result} (nunca usado)")
                continue
            resultado.append(c)
        return resultado

    @staticmethod
    def _es_numero(s: str) -> bool:
        try:
            float(s.replace(",", "."))
            return True
        except (ValueError, AttributeError):
            return False


# ═══════════════════════════════════════════════════════════════
#  FASE 5 — GENERACIÓN DE CÓDIGO FINAL (pseudoASM)
# ═══════════════════════════════════════════════════════════════

class GeneradorCodigoFinal:
    """
    Traduce cuádruplas optimizadas a pseudoensamblador de pila.

    Registros virtuales:
      AX, BX, CX  — registros de propósito general
      SP          — puntero de pila (implícito)

    Instrucciones generadas:
      ALLOC  tipo, var       — reservar espacio para variable
      LOAD   src, reg        — cargar valor en registro
      STORE  reg, dst        — guardar registro en variable
      ADD/SUB/MUL/DIV        — operaciones aritméticas
      PUSH   val             — apilar valor
      POP    reg             — desapilar en registro
      IN     tipo, var       — leer entrada del usuario
      OUT    val             — imprimir valor
      MOV    src, dst        — mover valor
      HALT                   — fin del programa
    """

    def __init__(self):
        self.instrucciones: list[str] = []
        self._reg_map = {"t": "AX", "u": "BX", "v": "CX"}
        self._reg_idx = 0
        self._regs = ["AX", "BX", "CX", "DX"]

    def _reg(self, temp: str) -> str:
        """Asigna un registro virtual a un temporal."""
        if not hasattr(self, "_asignaciones"):
            self._asignaciones: dict[str, str] = {}
        if temp not in self._asignaciones:
            reg = self._regs[self._reg_idx % len(self._regs)]
            self._asignaciones[temp] = reg
            self._reg_idx += 1
        return self._asignaciones[temp]

    def _es_temp(self, s: str) -> bool:
        return bool(s) and s.startswith("t") and s[1:].isdigit()

    def generar(self, cuadruplas: list[Cuadrupla], tabla: "TablaSimbolos") -> list[str]:
        self.instrucciones = []
        self._asignaciones = {}
        self._reg_idx = 0

        self.instrucciones.append("; ── Sección de datos ──────────────────────────")
        # ALLOC para cada variable declarada
        for c in cuadruplas:
            if c.op == "DECL":
                self.instrucciones.append(f"  ALLOC   {c.arg1:<10} {c.result}")

        self.instrucciones.append("; ── Sección de código ─────────────────────────")

        for c in cuadruplas:
            if c.op == "DECL":
                continue  # ya procesado arriba

            elif c.op == "READ":
                self.instrucciones.append(f"  IN      {c.arg1:<20} ; leer → {c.result}")

            elif c.op == "ASSIGN":
                src = c.arg1
                dst = c.result
                if self._es_temp(src):
                    reg = self._reg(src)
                    self.instrucciones.append(f"  STORE   {reg:<10} {dst:<10} ; {dst} = {reg}")
                elif self._es_temp(dst):
                    reg = self._reg(dst)
                    self.instrucciones.append(f"  LOAD    {src:<10} {reg:<10} ; {reg} = {src}")
                else:
                    self.instrucciones.append(f"  MOV     {src:<10} {dst:<10} ; {dst} = {src}")

            elif c.op in ("+", "-", "*", "/"):
                op_map = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV"}
                mnem = op_map[c.op]
                reg_dst = self._reg(c.result)
                # cargar arg1
                if self._es_temp(c.arg1):
                    self.instrucciones.append(f"  LOAD    {self._reg(c.arg1):<10} {reg_dst:<10} ; {reg_dst} = {c.arg1}")
                else:
                    self.instrucciones.append(f"  LOAD    {c.arg1:<10} {reg_dst:<10} ; {reg_dst} = {c.arg1}")
                # operar con arg2
                arg2 = self._reg(c.arg2) if self._es_temp(c.arg2) else c.arg2
                self.instrucciones.append(f"  {mnem:<8} {reg_dst:<10} {arg2:<10} ; {c.result} = {c.arg1} {c.op} {c.arg2}")

            elif c.op == "PRINT":
                self.instrucciones.append(f"  OUT     {c.arg1:<20} ; imprimir")

        self.instrucciones.append("  HALT                               ; fin del programa")
        return self.instrucciones


# ═══════════════════════════════════════════════════════════════
#  Función pública: generar_fases(codigo) → dict con resultados
# ═══════════════════════════════════════════════════════════════

def generar_fases(codigo: str, tabla: TablaSimbolos) -> dict:
    """
    Ejecuta las fases 3, 4 y 5 sobre el código ya validado.
    Retorna un dict con:
      'intermedio'  → list[Cuadrupla]
      'optimizado'  → list[Cuadrupla]
      'log_opt'     → list[str]
      'final'       → list[str]
    """
    gen   = GeneradorIntermedio()
    opt   = OptimizadorCodigo()
    final = GeneradorCodigoFinal()

    parser_aux = AnalizadorSintactico(TablaSimbolos())
    lineas = codigo.strip().split("\n")

    todas_cuads: list[Cuadrupla] = []
    for num, linea in enumerate(lineas, 1):
        linea = linea.strip()
        if not linea:
            continue
        tokens, _ = tokenizar(linea, num)
        tipo_sent, errores = parser_aux.analizar(tokens)
        if not errores:
            cuads = gen.generar(tipo_sent, tokens)
            todas_cuads.extend(cuads)

    optimizadas = opt.optimizar(todas_cuads)
    codigo_final = final.generar(optimizadas, tabla)

    return {
        "intermedio": todas_cuads,
        "optimizado": optimizadas,
        "log_opt":    opt.log,
        "final":      codigo_final,
    }


def _resolver_valor(nombre: str, tabla: TablaSimbolos, _vistos: set = None) -> str:
    """
    Resuelve el valor final de una variable siguiendo la cadena de asignaciones.
    Si la expresión contiene otras variables, las sustituye recursivamente.
    Si alguna depende de Captura, devuelve '<entrada usuario>'.
    """
    if _vistos is None:
        _vistos = set()
    if nombre in _vistos:
        return f"<{nombre}>"  # evitar ciclos
    _vistos.add(nombre)

    sim = tabla.obtener(nombre)
    if sim is None or sim.valor is None:
        return f"<{nombre}>"

    val = sim.valor

    # si viene de captura, no se puede resolver
    if val.startswith("Captura."):
        return f"<{nombre}: entrada usuario>"

    # intentar evaluar sustituyendo variables conocidas
    expr = val
    for var_nombre, var_sim in tabla._tabla.items():
        if var_nombre == nombre:
            continue
        if var_sim.valor and not var_sim.valor.startswith("Captura."):
            sub = _resolver_valor(var_nombre, tabla, set(_vistos))
            # solo sustituir si el resultado es numérico
            try:
                float(sub.replace(",", "."))
                expr = re.sub(rf'\b{re.escape(var_nombre)}\b', sub, expr)
            except ValueError:
                pass

    # normalizar y evaluar
    expr_norm = expr.replace(",", ".")
    try:
        resultado = eval(expr_norm)  # noqa: S307
        if isinstance(resultado, float) and resultado == int(resultado):
            return str(int(resultado))
        return str(resultado)
    except Exception:
        return val  # devolver la expresión si no se puede evaluar


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

        # Si es SALIDA, mostrar el valor que imprimiría
        if tipo_sent == "SALIDA" and not todos_errores:
            partes = []
            i = 1  # saltar MENSAJE_TEXTO
            while i < len(tokens):
                t = tokens[i]
                if t.tipo == "TEXTO_LIT":
                    partes.append(t.valor.strip('"'))
                elif t.tipo == "IDENTIFICADOR":
                    partes.append(_resolver_valor(t.valor, tabla))
                elif t.tipo in ("ENTERO_LIT", "REAL_LIT", "LOGICO_LIT"):
                    partes.append(t.valor)
                elif t.tipo in ("PARENTESIS_CI", "PUNTO_COMA"):
                    break
                i += 1
            print(f"  Salida : {' '.join(partes)}")

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