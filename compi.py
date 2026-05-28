import re
import random
from dataclasses import dataclass, field
from typing import Optional


# ── Mensajes con dialecto barranquillero ──────────────────────────────────────
_MSGS_OK = [
    "¡Eso ta' fino, llave!",
    "¡Ajá, así es como se hace, mano!",
    "¡Qué molleja, salió perfecto!",
    "¡Bien puesta esa vaina, pana!",
    "¡Ta' bueno eso, mijo!",
    "¡Eso quedó de pelos, hermano!",
]
_MSGS_ERROR_LEX = [
    "¡Epa! Ahí hay un carácter que no es ni chicha ni limonada",
    "¡Uy, llave! Ese símbolo no lo conoce ni el compilador",
    "¡Ajá! ¿Y eso qué es? Eso no va ahí, mano",
    "¡Mano, ese carácter no pinta nada ahí!",
]
_MSGS_ERROR_SIN = [
    "¡Se dañó la vaina! La sintaxis está barro",
    "¡Epa, llave! Eso no está bien escrito",
    "¡Ajá! ¿Qué fue lo que pusiste ahí? No cuadra",
    "¡Mano, eso está mal armado, vuelve y mira!",
]
_MSGS_ERROR_SEM = [
    "¡Uy, mano! Esa variable no la has presentado todavía",
    "¡Mano, los tipos no casan ni amarrados!",
    "¡Ajá! ¿Y esa variable de dónde salió, llave?",
    "¡Eso está barro, mijo! Revisa los tipos que usaste",
]
_MSGS_FINAL_OK = [
    "¡Bacano, llave! El código quedó fino fino 🎉",
    "¡Eso sí está de aquellas, llave! Cero errores 🌊",
    "¡Ajá, así se hace! Todo limpio, mano 🎉",
    "¡Qué molleja de código tan bonito! Sin un solo error 🌊",
]
_MSGS_FINAL_ERR = [
    "¡Epa! Quedó barro, mano. Hay {n} error(es) que arreglar",
    "¡Ajá! Eso tiene {n} problema(s), llave. ¡A dale!",
    "¡Mano, {n} error(es)! Eso está más enredao que un partido del Junior",
    "¡Uy, pana! {n} error(es). Vuelve y revisa eso con cuidado",
]

def _msg(lista: list[str], **kw) -> str:
    return random.choice(lista).format(**kw)


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
            errores.append(f"  ERROR LÉXICO: {_msg(_MSGS_ERROR_LEX)} — carácter inesperado '{valor}' en posición {pos}")
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
    ultimo_valor_numerico: Optional[str] = None  # último valor literal conocido antes de Captura


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
        # Guardar el último valor numérico conocido antes de que Captura lo sobreescriba
        try:
            float(valor.replace(",", "."))
            self._tabla[nombre].ultimo_valor_numerico = valor
        except (ValueError, AttributeError):
            pass
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
        self.errores.append(f"  ERROR SINTÁCTICO: {_msg(_MSGS_ERROR_SIN)} — se esperaba {esperado}, se obtuvo {obtenido}")
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

        self.errores.append(f"  ERROR SINTÁCTICO: {_msg(_MSGS_ERROR_SIN)} — sentencia no reconocida, empieza con {t.tipo}('{t.valor}')")
        return "DESCONOCIDO", self.errores

    def _ver_siguiente(self, tipo: str) -> bool:
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1].tipo == tipo
        return False

   
    def _declaracion(self) -> tuple[str, list[str]]:
        id_tok  = self.consumir("IDENTIFICADOR")
        tip_tok = self.consumir("TIPO_DATO")
        self.consumir("PUNTO_COMA")
        self._validar_fin_linea()
        if not self.errores and id_tok and tip_tok:
            ok, msg = self.tabla.declarar(id_tok.valor, tip_tok.valor, id_tok.linea)
            if not ok:
                self.errores.append(f"  ERROR SEMÁNTICO: {_msg(_MSGS_ERROR_SEM)} — {msg}")
        return "DECLARACION", self.errores

    def _captura(self) -> tuple[str, list[str]]:
        id_tok  = self.consumir("IDENTIFICADOR")
        self.consumir("ASIGNACION")
        cap_tok = self.consumir("CAPTURA_TIPO")
        self.consumir("PUNTO_COMA")
        self._validar_fin_linea()
        if not self.errores and id_tok and cap_tok:
            # verificar que la variable esté declarada
            if not self.tabla.existe(id_tok.valor):
                self.errores.append(f"  ERROR SEMÁNTICO: {_msg(_MSGS_ERROR_SEM)} — variable '{id_tok.valor}' no declarada antes de usarla.")
            else:
                # verificar compatibilidad de tipo — es ERROR, no advertencia
                tipo_captura = re.search(r'\.(Entero|Real|Texto|Logico)', cap_tok.valor).group(1)
                sim = self.tabla.obtener(id_tok.valor)
                if sim.tipo != tipo_captura:
                    self.errores.append(
                        f"  ERROR SEMÁNTICO: {_msg(_MSGS_ERROR_SEM)} — '{id_tok.valor}' declarada como {sim.tipo} "
                        f"pero se intenta capturar como {tipo_captura}. ¡Los tipos no cuadran, llave!"
                    )
                else:
                    self.tabla.asignar(id_tok.valor, f"Captura.{tipo_captura}()")
        return "CAPTURA", self.errores

    def _validar_fin_linea(self):
        """Detecta tokens inesperados después del punto y coma."""
        if self.actual() is not None:
            sobrantes = []
            while self.actual():
                sobrantes.append(self.actual().valor)
                self.pos += 1
            self.errores.append(
                f"  ERROR SINTÁCTICO: tokens inesperados después del ';': "
                f"{''.join(sobrantes)}"
            )

    def _asignacion(self) -> tuple[str, list[str]]:
        id_tok = self.consumir("IDENTIFICADOR")
        self.consumir("ASIGNACION")
        # recolectar tokens de la expresión para validación de tipos
        expr_tokens = []
        while self.actual() and self.actual().tipo != "PUNTO_COMA":
            expr_tokens.append(self.actual())
            self.pos += 1
        # reconstruir expr con paréntesis para eval
        expr_str = "".join(t.valor for t in expr_tokens)
        self.consumir("PUNTO_COMA")
        self._validar_fin_linea()

        # ── validar operadores consecutivos en la expresión ───────────────────
        for i in range(len(expr_tokens) - 1):
            if expr_tokens[i].tipo == "OPERADOR" and expr_tokens[i+1].tipo == "OPERADOR":
                self.errores.append(
                    f"  ERROR SINTÁCTICO: operadores consecutivos inválidos: "
                    f"'{expr_tokens[i].valor}{expr_tokens[i+1].valor}'"
                )

        if not self.errores and id_tok:
            if not self.tabla.existe(id_tok.valor):
                self.errores.append(
                    f"  ERROR SEMÁNTICO: {_msg(_MSGS_ERROR_SEM)} — variable '{id_tok.valor}' no declarada."
                )
            else:
                # ── validar tipos de los identificadores en la expresión ──────
                sim_dest = self.tabla.obtener(id_tok.valor)
                for et in expr_tokens:
                    if et.tipo == "IDENTIFICADOR":
                        if not self.tabla.existe(et.valor):
                            self.errores.append(
                                f"  ERROR SEMÁNTICO: {_msg(_MSGS_ERROR_SEM)} — variable '{et.valor}' usada pero no declarada."
                            )
                        else:
                            sim_op = self.tabla.obtener(et.valor)
                            # verificar que esté inicializada antes de usarla
                            if not sim_op.inicializado:
                                self.errores.append(
                                    f"  ERROR SEMÁNTICO: ¡Epa, llave! La variable '{et.valor}' está declarada "
                                    f"pero nunca le diste un valor. ¡No la puedes usar así!"
                                )
                            # operaciones aritméticas solo con Entero/Real
                            hay_operador = any(t.tipo == "OPERADOR" for t in expr_tokens)
                            if hay_operador and sim_op.tipo not in ("Entero", "Real"):
                                self.errores.append(
                                    f"  ERROR SEMÁNTICO: {_msg(_MSGS_ERROR_SEM)} — '{et.valor}' es de tipo "
                                    f"{sim_op.tipo} y no puede usarse en operaciones aritméticas."
                                )
                if not self.errores:
                    valor_evaluado = self._evaluar_expr(expr_str)
                    # si no se pudo evaluar, guardar expresión legible con espacios
                    if valor_evaluado == expr_str:
                        valor_evaluado = self._expr_legible(expr_tokens)
                    self.tabla.asignar(id_tok.valor, valor_evaluado)
        return "ASIGNACION", self.errores

    def _expr_legible(self, tokens: list) -> str:
        """Construye una representación legible de la expresión con espacios."""
        partes = []
        for t in tokens:
            if t.tipo == "OPERADOR":
                partes.append(f" {t.valor} ")
            elif t.tipo == "PARENTESIS_AP":
                partes.append("(")
            elif t.tipo == "PARENTESIS_CI":
                partes.append(")")
            else:
                partes.append(t.valor)
        return "".join(partes)

    def _evaluar_expr(self, expr: str) -> str:
        """
        Intenta evaluar una expresión sustituyendo variables por sus valores
        numéricos conocidos en la tabla de símbolos.
        Sustituye lo que puede aunque no pueda evaluar todo.
        """
        expr_eval = expr
        for nombre, sim in self.tabla._tabla.items():
            if sim.valor is None:
                continue
            # Si el valor actual es Captura, usar el último valor numérico conocido
            val_usar = sim.valor
            if sim.valor.startswith("Captura.") and sim.ultimo_valor_numerico is not None:
                val_usar = sim.ultimo_valor_numerico
            val_norm = val_usar.replace(",", ".")
            try:
                float(val_norm)
                expr_eval = re.sub(rf'\b{re.escape(nombre)}\b', val_norm, expr_eval)
            except ValueError:
                pass
        expr_eval_norm = expr_eval.replace(",", ".")
        try:
            resultado = eval(expr_eval_norm)  # noqa: S307
            if isinstance(resultado, float) and resultado == int(resultado):
                return str(int(resultado))
            return str(resultado)
        except Exception:
            # No se pudo evaluar todo — devolver la expresión con sustituciones parciales
            # evaluar subexpresiones entre paréntesis que sí sean numéricas
            def _eval_sub(m):
                try:
                    r = eval(m.group(1))  # noqa: S307
                    if isinstance(r, float) and r == int(r):
                        return str(int(r))
                    return str(r)
                except Exception:
                    return m.group(0)
            simplificada = re.sub(r'\(([^()]+)\)', _eval_sub, expr_eval_norm)
            try:
                resultado = eval(simplificada)  # noqa: S307
                if isinstance(resultado, float) and resultado == int(resultado):
                    return str(int(resultado))
                return str(resultado)
            except Exception:
                # añadir espacios alrededor de operadores para legibilidad
                simplificada = re.sub(r'([+\-*/])', r' \1 ', simplificada)
                simplificada = re.sub(r'\s+', ' ', simplificada).strip()
                return simplificada

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
        self._validar_fin_linea()

        # validar que variables usadas estén declaradas e inicializadas
        for arg in argumentos:
            if arg.tipo == "IDENTIFICADOR":
                if not self.tabla.existe(arg.valor):
                    self.errores.append(
                        f"  ERROR SEMÁNTICO: {_msg(_MSGS_ERROR_SEM)} — variable '{arg.valor}' usada en Mensaje.Texto() no está declarada."
                    )
                elif not self.tabla.obtener(arg.valor).inicializado:
                    self.errores.append(
                        f"  ERROR SEMÁNTICO: ¡Ajá, mano! La variable '{arg.valor}' está declarada "
                        f"pero no tiene ningún valor. ¡No la puedes imprimir así, mano!"
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
        partes_print = []
        for t in tokens:
            if t.tipo == "TEXTO_LIT":
                partes_print.append(t.valor)
            elif t.tipo == "IDENTIFICADOR":
                partes_print.append(t.valor)
        if partes_print:
            self.cuadruplas.append(
                Cuadrupla("PRINT", " ".join(partes_print), "", "")
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
    Resuelve el valor final de una variable.
    - Si el valor ya es un número → lo devuelve.
    - Si es una expresión con variables → sustituye los que puede y evalúa.
    - Si no puede evaluar → devuelve la expresión legible.
    - Si depende de Captura directamente → devuelve la expresión.
    """
    if _vistos is None:
        _vistos = set()
    if nombre in _vistos:
        return f"[{nombre}]"
    _vistos.add(nombre)

    sim = tabla.obtener(nombre)
    if sim is None or sim.valor is None:
        return f"[{nombre}]"

    val = sim.valor

    # ya es un número puro
    try:
        float(val.replace(",", "."))
        return val
    except (ValueError, AttributeError):
        pass

    # viene directamente de captura
    if val.startswith("Captura."):
        return val  # mostrar "Captura.Entero()" tal cual

    # es una expresión — intentar sustituir variables por sus valores numéricos
    expr = val
    tiene_captura = False  # bandera: alguna variable depende de Captura
    for var_nombre, var_sim in tabla._tabla.items():
        if var_nombre == nombre:
            continue
        if not re.search(rf'\b{re.escape(var_nombre)}\b', expr):
            continue
        # Si la variable viene de Captura pero tiene un valor numérico previo, usarlo
        if var_sim.valor and var_sim.valor.startswith("Captura."):
            if var_sim.ultimo_valor_numerico is not None:
                sub = var_sim.ultimo_valor_numerico
                expr = re.sub(rf'\b{re.escape(var_nombre)}\b', sub, expr)
            else:
                tiene_captura = True
            continue  # ya procesado
        sub = _resolver_valor(var_nombre, tabla, set(_vistos))
        try:
            float(sub.replace(",", "."))
            expr = re.sub(rf'\b{re.escape(var_nombre)}\b', sub, expr)
        except ValueError:
            expr = re.sub(rf'\b{re.escape(var_nombre)}\b', sub, expr)

    # Si hay variables de Captura, no se puede evaluar numéricamente —
    # devolver la expresión con espacios legibles alrededor de operadores
    if tiene_captura:
        expr_legible = re.sub(r'([+\-*/])', r' \1 ', expr)
        expr_legible = re.sub(r'\s+', ' ', expr_legible).strip()
        return expr_legible

    expr_norm = expr.replace(",", ".")
    try:
        resultado = eval(expr_norm)  # noqa: S307
        if isinstance(resultado, float) and resultado == int(resultado):
            return str(int(resultado))
        return str(resultado)
    except Exception:
        # intentar evaluar subexpresiones entre paréntesis que sean numéricas
        def eval_subexpr(m):
            try:
                r = eval(m.group(1))  # noqa: S307
                if isinstance(r, float) and r == int(r):
                    return str(int(r))
                return str(r)
            except Exception:
                return m.group(0)
        expr_simplificada = re.sub(r'\(([^()]+)\)', eval_subexpr, expr_norm)
        try:
            resultado = eval(expr_simplificada)  # noqa: S307
            if isinstance(resultado, float) and resultado == int(resultado):
                return str(int(resultado))
            return str(resultado)
        except Exception:
            # añadir espacios alrededor de operadores para legibilidad
            expr_legible = re.sub(r'([+\-*/])', r' \1 ', expr_simplificada)
            expr_legible = re.sub(r'\s+', ' ', expr_legible).strip()
            return expr_legible


def compilar(codigo: str) -> None:
    tabla   = TablaSimbolos()
    parser  = AnalizadorSintactico(tabla)
    lineas  = codigo.strip().split("\n")

    print("=" * 65)
    print("  🌊 COMPILADOR COSTEÑOL — Léxico + Sintáctico")
    print("=" * 65)

    total_errores = 0

    for num, linea in enumerate(lineas, start=1):
        linea = linea.strip()
        if not linea:
            continue

        tokens, err_lex = tokenizar(linea, num)

        # Si hay errores léxicos, no ejecutar el análisis sintáctico
        # para evitar errores falsos de "se esperaba PUNTO_COMA"
        if err_lex:
            tipo_sent = "ERROR_LEXICO"
            err_sint = []
        else:
            tipo_sent, err_sint = parser.analizar(tokens)

        todos_errores = err_lex + err_sint
        total_errores += len(todos_errores)

        estado = f"✓ {_msg(_MSGS_OK)}" if not todos_errores else f"✗ {len(todos_errores)} error(es)"
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

    
    estado_final = _msg(_MSGS_FINAL_OK) if total_errores == 0 else _msg(_MSGS_FINAL_ERR, n=total_errores)
    print(f"  {estado_final}")
    print("=" * 65)




if __name__ == "__main__":
    codigo_prueba = """
A Entero;  
b Entero;  
suma Entero;
pi Real;
num2 Entero;
num3 Entero;    
num1 Entero;
num1= 12;
num2= 5;
num3= 13;
nombre Texto;
n1 Real;
asis Logico;
nombre= Captura.Texto();
n1= Captura.Real();
num1= Captura.Entero();
num2= Captura.Entero();
num3= Captura.Entero();
asis=Captura.Logico();
suma=num1+(num2*num3);
nombre="Alejandra";
pi=3.1416;
Mensaje.Texto("El resultado es:", suma);
Mensaje.Texto("Hola mundo");
"""
    compilar(codigo_prueba)