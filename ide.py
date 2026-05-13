"""
COSTEÑOL IDE — Interfaz gráfica con CustomTkinter
Proyecto Compiladores — CUL
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import re
from io import StringIO
import sys

# ── importar el compilador propio ─────────────────────────────────────────────
from compi import compilar, tokenizar, TablaSimbolos, AnalizadorSintactico

# ── Tema y apariencia ─────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Paleta de colores para el resaltado de sintaxis ──────────────────────────
COLOR_TIPO     = "#4FC3F7"   # Entero, Real, Texto, Logico
COLOR_CAPTURA  = "#81C784"   # Captura.xxx()
COLOR_MENSAJE  = "#FFB74D"   # Mensaje.Texto()
COLOR_LITERAL  = "#F48FB1"   # "cadenas"
COLOR_NUM      = "#CE93D8"   # 123, 3.14
COLOR_LOGICO   = "#80DEEA"   # verdadero / falso
COLOR_IDENT    = "#FFFFFF"
COLOR_OP       = "#FFD54F"
COLOR_ERROR    = "#FF5252"
COLOR_COMMENT  = "#757575"

TIPOS_DATO     = {"Entero", "Real", "Texto", "Logico"}
LOGICOS_LIT    = {"verdadero", "falso", "true", "false"}

CODIGO_EJEMPLO = """\
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
pi=3,1416;
Mensaje.Texto("Esto es una prueba");
Mensaje.Texto("Hola mundo");
"""


# ═════════════════════════════════════════════════════════════════════════════
class CosteñolIDE(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("COSTEÑOL IDE  —  Compilador")
        self.geometry("1280x780")
        self.minsize(900, 600)

        self._construir_ui()
        self._insertar_ejemplo()

    # ── Construcción de la UI ─────────────────────────────────────────────────
    def _construir_ui(self):
        # ── barra superior ────────────────────────────────────────────────────
        barra = ctk.CTkFrame(self, height=52, corner_radius=0,
                             fg_color="#1e1e2e")
        barra.pack(fill="x", side="top")

        ctk.CTkLabel(barra, text="🌊  COSTEÑOL IDE",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#4FC3F7").pack(side="left", padx=16)

        # botones barra
        for texto, cmd, color in [
            ("▶  Compilar",    self._compilar,      "#1565C0"),
            ("🔍 Solo Léxico", self._solo_lexico,   "#1B5E20"),
            ("🗑  Limpiar",    self._limpiar,       "#4A148C"),
            ("📂 Abrir",       self._abrir_archivo, "#37474F"),
            ("💾 Guardar",     self._guardar_archivo,"#37474F"),
            ("📋 Ejemplo",     self._insertar_ejemplo,"#BF360C"),
        ]:
            ctk.CTkButton(barra, text=texto, width=120, height=34,
                          fg_color=color, hover_color=color,
                          command=cmd,
                          font=ctk.CTkFont(size=12, weight="bold"),
                          corner_radius=6).pack(side="left", padx=4, pady=8)

        # modo apariencia a la derecha
        ctk.CTkOptionMenu(barra, values=["Dark", "Light", "System"],
                          width=100, height=28,
                          command=lambda m: ctk.set_appearance_mode(m)
                          ).pack(side="right", padx=12)

        # ── panel principal dividido ──────────────────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=4)
        main.rowconfigure(0, weight=1)

        # ── panel IZQUIERDO: editor ───────────────────────────────────────────
        izq = ctk.CTkFrame(main, corner_radius=10)
        izq.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        izq.rowconfigure(1, weight=1)
        izq.columnconfigure(0, weight=1)

        ctk.CTkLabel(izq, text="✏️  Editor de Código",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#4FC3F7").grid(row=0, column=0,
                     sticky="w", padx=12, pady=(8, 2))

        # frame numeración + editor
        editor_frame = ctk.CTkFrame(izq, fg_color="#1e1e2e", corner_radius=8)
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        editor_frame.rowconfigure(0, weight=1)
        editor_frame.columnconfigure(1, weight=1)

        # números de línea
        self.numeros = tk.Text(editor_frame, width=4,
                               state="disabled",
                               bg="#252535", fg="#555577",
                               font=("Consolas", 12),
                               relief="flat", bd=0,
                               selectbackground="#252535",
                               cursor="arrow")
        self.numeros.grid(row=0, column=0, sticky="ns", padx=(4, 0))

        # editor principal
        self.editor = tk.Text(editor_frame,
                              bg="#1e1e2e", fg="#FFFFFF",
                              font=("Consolas", 13),
                              insertbackground="#4FC3F7",
                              selectbackground="#3a3a5a",
                              relief="flat", bd=0,
                              wrap="none", undo=True,
                              tabs=("2c",))
        self.editor.grid(row=0, column=1, sticky="nsew")

        # scrollbars
        sb_y = ctk.CTkScrollbar(editor_frame, command=self._scroll_sync_y)
        sb_y.grid(row=0, column=2, sticky="ns")
        sb_x = ctk.CTkScrollbar(editor_frame, orientation="horizontal",
                                 command=self.editor.xview)
        sb_x.grid(row=1, column=1, sticky="ew")
        self.editor.configure(yscrollcommand=self._on_editor_scroll_y,
                               xscrollcommand=sb_x.set)
        self.numeros.configure(yscrollcommand=lambda *a: None)

        self.editor.bind("<KeyRelease>", self._on_edit)
        self.editor.bind("<MouseWheel>", self._on_edit)
        self.editor.bind("<Button-1>", self._actualizar_status)

        # status bar editor
        self.status_editor = ctk.CTkLabel(izq, text="Lín 1, Col 1",
                                          text_color="#888",
                                          font=ctk.CTkFont(size=11))
        self.status_editor.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 4))

        # ── panel DERECHO: resultados (pestañas) ──────────────────────────────
        der = ctk.CTkFrame(main, corner_radius=10)
        der.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        der.rowconfigure(1, weight=1)
        der.columnconfigure(0, weight=1)

        ctk.CTkLabel(der, text="📊  Resultados",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#4FC3F7").grid(row=0, column=0,
                     sticky="w", padx=12, pady=(8, 2))

        self.tabs = ctk.CTkTabview(der, corner_radius=8)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self.tab_compilacion  = self.tabs.add("🔨 Compilación")
        self.tab_lexico       = self.tabs.add("🔤 Léxico")
        self.tab_tabla        = self.tabs.add("📋 Tabla Símbolos")
        self.tab_errores      = self.tabs.add("❌ Errores")

        self.out_compilacion  = self._crear_salida(self.tab_compilacion)
        self.out_lexico       = self._crear_salida(self.tab_lexico)
        self.out_tabla        = self._crear_salida(self.tab_tabla)
        self.out_errores      = self._crear_salida(self.tab_errores)

        # ── barra de estado inferior ──────────────────────────────────────────
        self.barra_estado = ctk.CTkFrame(self, height=28, corner_radius=0,
                                          fg_color="#0d0d1a")
        self.barra_estado.pack(fill="x", side="bottom")
        self.lbl_estado = ctk.CTkLabel(self.barra_estado,
                                        text="Listo. Escribe código Costeñol y presiona ▶ Compilar.",
                                        font=ctk.CTkFont(size=11),
                                        text_color="#888")
        self.lbl_estado.pack(side="left", padx=12)

    def _crear_salida(self, parent):
        """Crea un widget Text de solo lectura dentro del tab dado."""
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        f = ctk.CTkFrame(parent, fg_color="#111120", corner_radius=6)
        f.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)
        t = tk.Text(f, bg="#111120", fg="#E0E0E0",
                    font=("Consolas", 12),
                    state="disabled", relief="flat", bd=0,
                    wrap="word", selectbackground="#333355")
        t.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(f, command=t.yview)
        sb.grid(row=0, column=1, sticky="ns")
        t.configure(yscrollcommand=sb.set)
        self._configurar_tags(t)
        return t

    def _configurar_tags(self, widget):
        widget.tag_configure("header",   foreground="#4FC3F7",
                             font=("Consolas", 12, "bold"))
        widget.tag_configure("ok",       foreground="#81C784")
        widget.tag_configure("error",    foreground="#FF5252")
        widget.tag_configure("warn",     foreground="#FFB74D")
        widget.tag_configure("tipo",     foreground=COLOR_TIPO)
        widget.tag_configure("literal",  foreground=COLOR_LITERAL)
        widget.tag_configure("num",      foreground=COLOR_NUM)
        widget.tag_configure("op",       foreground=COLOR_OP)
        widget.tag_configure("captura",  foreground=COLOR_CAPTURA)
        widget.tag_configure("mensaje",  foreground=COLOR_MENSAJE)
        widget.tag_configure("logico",   foreground=COLOR_LOGICO)
        widget.tag_configure("dim",      foreground="#666688")
        widget.tag_configure("bold",     font=("Consolas", 12, "bold"))

    # ── Scroll sincronizado ───────────────────────────────────────────────────
    def _scroll_sync_y(self, *args):
        self.editor.yview(*args)
        self.numeros.yview(*args)

    def _on_editor_scroll_y(self, *args):
        self.numeros.yview_moveto(args[0])

    # ── Eventos del editor ────────────────────────────────────────────────────
    def _on_edit(self, event=None):
        self._actualizar_numeros()
        self._resaltar_sintaxis()
        self._actualizar_status()

    def _actualizar_status(self, event=None):
        try:
            pos = self.editor.index("insert")
            lin, col = pos.split(".")
            self.status_editor.configure(text=f"Lín {lin}, Col {int(col)+1}")
        except Exception:
            pass

    def _actualizar_numeros(self):
        self.numeros.configure(state="normal")
        self.numeros.delete("1.0", "end")
        lineas = int(self.editor.index("end-1c").split(".")[0])
        nums = "\n".join(str(i) for i in range(1, lineas + 1))
        self.numeros.insert("1.0", nums)
        self.numeros.configure(state="disabled")

    # ── Resaltado de sintaxis ─────────────────────────────────────────────────
    def _resaltar_sintaxis(self):
        codigo = self.editor.get("1.0", "end-1c")
        # limpiar todos los tags de color
        for tag in ("t_tipo", "t_captura", "t_mensaje", "t_literal",
                    "t_num", "t_logico", "t_op", "t_error"):
            self.editor.tag_remove(tag, "1.0", "end")

        # configurar tags en el editor
        self.editor.tag_configure("t_tipo",    foreground=COLOR_TIPO)
        self.editor.tag_configure("t_captura", foreground=COLOR_CAPTURA)
        self.editor.tag_configure("t_mensaje", foreground=COLOR_MENSAJE)
        self.editor.tag_configure("t_literal", foreground=COLOR_LITERAL)
        self.editor.tag_configure("t_num",     foreground=COLOR_NUM)
        self.editor.tag_configure("t_logico",  foreground=COLOR_LOGICO)
        self.editor.tag_configure("t_op",      foreground=COLOR_OP)
        self.editor.tag_configure("t_error",   foreground=COLOR_ERROR,
                                  underline=True)

        patrones = [
            ("t_captura", r'Captura\.(Entero|Real|Texto|Logico)\(\)'),
            ("t_mensaje", r'Mensaje\.Texto\('),
            ("t_tipo",    r'\b(Entero|Real|Texto|Logico)\b'),
            ("t_logico",  r'\b(verdadero|falso|true|false)\b'),
            ("t_literal", r'"[^"]*"'),
            ("t_num",     r'\b\d+[.,]\d+\b|\b\d+\b'),
            ("t_op",      r'[+\-*/=<>!]+'),
        ]
        for tag, patron in patrones:
            for m in re.finditer(patron, codigo):
                start = f"1.0 + {m.start()} chars"
                end   = f"1.0 + {m.end()} chars"
                self.editor.tag_add(tag, start, end)

    # ── Obtener código del editor ─────────────────────────────────────────────
    def _get_codigo(self):
        return self.editor.get("1.0", "end-1c").strip()

    # ── Escritura en paneles de salida ────────────────────────────────────────
    def _limpiar_panel(self, widget):
        widget.configure(state="normal")
        widget.delete("1.0", "end")

    def _escribir(self, widget, texto, tag=None):
        widget.configure(state="normal")
        if tag:
            widget.insert("end", texto, tag)
        else:
            widget.insert("end", texto)

    def _cerrar_panel(self, widget):
        widget.configure(state="disabled")
        widget.see("end")

    # ── Acción: COMPILAR COMPLETO ─────────────────────────────────────────────
    def _compilar(self):
        codigo = self._get_codigo()
        if not codigo:
            messagebox.showwarning("Vacío", "El editor está vacío.")
            return

        # capturar stdout del compilador
        captura = StringIO()
        sys.stdout = captura
        try:
            compilar(codigo)
        finally:
            sys.stdout = sys.__stdout__
        salida_raw = captura.getvalue()

        # mostrar en tab Compilación
        self._limpiar_panel(self.out_compilacion)
        self._renderizar_salida_compilador(self.out_compilacion, salida_raw)
        self._cerrar_panel(self.out_compilacion)

        # tabla de símbolos separada
        self._construir_tabla_simbolos(codigo)

        # errores separados
        self._construir_tab_errores(codigo)

        # léxico también
        self._solo_lexico(silent=True)

        self.tabs.set("🔨 Compilación")
        self.lbl_estado.configure(text="✅ Compilación completada.")

    def _renderizar_salida_compilador(self, widget, texto):
        for linea in texto.split("\n"):
            if "=" * 10 in linea:
                self._escribir(widget, linea + "\n", "dim")
            elif linea.strip().startswith("✓") or "Bacano" in linea:
                self._escribir(widget, linea + "\n", "ok")
            elif linea.strip().startswith("✗") or "ERROR" in linea or "BARRO" in linea:
                self._escribir(widget, linea + "\n", "error")
            elif "ADVERTENCIA" in linea or "WARN" in linea:
                self._escribir(widget, linea + "\n", "warn")
            elif "[Línea" in linea:
                self._escribir(widget, linea + "\n", "header")
            elif linea.strip().startswith("Tokens :"):
                # colorear tokens inline
                self._escribir(widget, "  Tokens : ")
                partes = linea.replace("  Tokens : ", "").split(" → ")
                for i, p in enumerate(partes):
                    tag = self._tag_para_token_str(p)
                    self._escribir(widget, p, tag)
                    if i < len(partes) - 1:
                        self._escribir(widget, " → ", "dim")
                self._escribir(widget, "\n")
            else:
                self._escribir(widget, linea + "\n")

    def _tag_para_token_str(self, tok_str):
        if "TIPO_DATO" in tok_str:       return "tipo"
        if "CAPTURA" in tok_str:         return "captura"
        if "MENSAJE" in tok_str:         return "mensaje"
        if "TEXTO_LIT" in tok_str:       return "literal"
        if "ENTERO_LIT" in tok_str or "REAL_LIT" in tok_str: return "num"
        if "LOGICO" in tok_str:          return "logico"
        if "OPERADOR" in tok_str or "ASIGNACION" in tok_str: return "op"
        if "ERROR" in tok_str:           return "error"
        return None

    # ── Acción: SOLO LÉXICO ───────────────────────────────────────────────────
    def _solo_lexico(self, silent=False):
        codigo = self._get_codigo()
        if not codigo:
            if not silent:
                messagebox.showwarning("Vacío", "El editor está vacío.")
            return

        self._limpiar_panel(self.out_lexico)

        self._escribir(self.out_lexico,
                       "══════════════════════════════════════════\n"
                       "  ANÁLISIS LÉXICO — Tokens por línea\n"
                       "══════════════════════════════════════════\n", "header")

        lineas = codigo.strip().split("\n")
        for num, linea in enumerate(lineas, 1):
            linea = linea.strip()
            if not linea:
                continue
            tokens, errores = tokenizar(linea, num)
            self._escribir(self.out_lexico,
                           f"\n[Línea {num:>2}]  {linea}\n", "header")
            self._escribir(self.out_lexico,
                           f"  {'Pos':<5} {'Token':<18} {'Valor'}\n", "dim")
            self._escribir(self.out_lexico,
                           "  " + "─" * 40 + "\n", "dim")
            for t in tokens:
                tag = self._tag_para_token_str(t.tipo)
                self._escribir(self.out_lexico,
                               f"  {t.posicion:<5} ")
                self._escribir(self.out_lexico,
                               f"{t.tipo:<18} ", tag or "")
                self._escribir(self.out_lexico,
                               f"{t.valor}\n", tag or "")
            for e in errores:
                self._escribir(self.out_lexico, e + "\n", "error")

        self._escribir(self.out_lexico,
                       "\n══════════════════════════════════════════\n"
                       "  Análisis léxico completado.\n"
                       "══════════════════════════════════════════\n", "dim")
        self._cerrar_panel(self.out_lexico)

        if not silent:
            self.tabs.set("🔤 Léxico")
            self.lbl_estado.configure(text="🔤 Análisis léxico completado.")

    # ── Tabla de símbolos ─────────────────────────────────────────────────────
    def _construir_tabla_simbolos(self, codigo):
        self._limpiar_panel(self.out_tabla)
        tabla = TablaSimbolos()
        parser = AnalizadorSintactico(tabla)
        lineas = codigo.strip().split("\n")
        for num, linea in enumerate(lineas, 1):
            linea = linea.strip()
            if not linea:
                continue
            tokens, _ = tokenizar(linea, num)
            parser.analizar(tokens)

        self._escribir(self.out_tabla,
                       "══════════════════════════════════════════════════════════\n"
                       "  TABLA DE SÍMBOLOS\n"
                       "══════════════════════════════════════════════════════════\n",
                       "header")

        if not tabla._tabla:
            self._escribir(self.out_tabla, "  (sin variables declaradas)\n", "dim")
        else:
            self._escribir(self.out_tabla,
                           f"\n  {'Variable':<16} {'Tipo':<10} {'Inicializado':<15} {'Valor':<22} {'Línea'}\n",
                           "bold")
            self._escribir(self.out_tabla, "  " + "─" * 68 + "\n", "dim")
            for s in tabla._tabla.values():
                val = s.valor if s.valor is not None else "—"
                ini = "✓ Sí" if s.inicializado else "✗ No"
                tag_ini = "ok" if s.inicializado else "warn"
                self._escribir(self.out_tabla, f"  {s.nombre:<16} ")
                self._escribir(self.out_tabla, f"{s.tipo:<10} ", "tipo")
                self._escribir(self.out_tabla, f"{ini:<15} ", tag_ini)
                self._escribir(self.out_tabla, f"{val:<22} ")
                self._escribir(self.out_tabla, f"{s.linea_declaracion}\n", "dim")

        self._escribir(self.out_tabla,
                       "\n══════════════════════════════════════════════════════════\n",
                       "dim")
        self._cerrar_panel(self.out_tabla)

    # ── Tab errores ───────────────────────────────────────────────────────────
    def _construir_tab_errores(self, codigo):
        self._limpiar_panel(self.out_errores)
        tabla = TablaSimbolos()
        parser = AnalizadorSintactico(tabla)
        lineas = codigo.strip().split("\n")
        errores_totales = []

        for num, linea in enumerate(lineas, 1):
            linea_s = linea.strip()
            if not linea_s:
                continue
            tokens, err_lex = tokenizar(linea_s, num)
            _, err_sint = parser.analizar(tokens)
            for e in err_lex + err_sint:
                errores_totales.append((num, linea_s, e))

        self._escribir(self.out_errores,
                       "══════════════════════════════════════════\n"
                       "  RESUMEN DE ERRORES Y ADVERTENCIAS\n"
                       "══════════════════════════════════════════\n", "header")

        if not errores_totales:
            self._escribir(self.out_errores,
                           "\n  ✅  ¡Sin errores! El código está bacano 🎉\n", "ok")
        else:
            for num, linea_s, e in errores_totales:
                self._escribir(self.out_errores,
                               f"\n  Línea {num}: {linea_s}\n", "warn")
                tag = "warn" if "ADVERTENCIA" in e else "error"
                self._escribir(self.out_errores, f"  {e.strip()}\n", tag)

            self._escribir(self.out_errores,
                           f"\n  Total: {len(errores_totales)} problema(s) encontrado(s).\n",
                           "error")

        self._escribir(self.out_errores,
                       "\n══════════════════════════════════════════\n", "dim")
        self._cerrar_panel(self.out_errores)

    # ── Acciones de archivo ───────────────────────────────────────────────────
    def _abrir_archivo(self):
        ruta = filedialog.askopenfilename(
            filetypes=[("Archivos de texto", "*.txt *.cos"), ("Todos", "*.*")])
        if ruta:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", contenido)
            self._on_edit()
            self.lbl_estado.configure(text=f"📂 Archivo cargado: {ruta}")

    def _guardar_archivo(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt *.cos"), ("Todos", "*.*")])
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self._get_codigo())
            self.lbl_estado.configure(text=f"💾 Guardado en: {ruta}")

    def _limpiar(self):
        self.editor.delete("1.0", "end")
        for w in (self.out_compilacion, self.out_lexico,
                  self.out_tabla, self.out_errores):
            self._limpiar_panel(w)
            self._cerrar_panel(w)
        self._actualizar_numeros()
        self.lbl_estado.configure(text="Editor limpiado.")

    def _insertar_ejemplo(self):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", CODIGO_EJEMPLO)
        self._on_edit()
        self.lbl_estado.configure(text="📋 Código de ejemplo cargado.")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = CosteñolIDE()
    app.mainloop()
