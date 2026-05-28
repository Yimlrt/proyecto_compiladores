# Proyecto: Compilador Costeñol

**Integrantes:**
- Emanuel Orozco
- Vanelly Ariza
- Yimileth Manga

---

## 📝 Descripción

Este proyecto es un compilador para el lenguaje **Costeñol**, desarrollado en Python. Incluye un analizador léxico, un analizador sintáctico, una tabla de símbolos y una interfaz gráfica (IDE) para escribir, compilar y guardar código Costeñol.

---

## 📁 Contenido del Proyecto

| Archivo | Descripción |
|---|---|
| `compi.py` | Núcleo del compilador: tokenizador, analizador sintáctico y tabla de símbolos |
| `ide.py` | Interfaz gráfica del IDE construida con CustomTkinter |
| `tokens.py` | Script auxiliar del analizador léxico |
| `prueba.txt` | Archivo de ejemplo con código fuente Costeñol |
| `README.md` | Este documento |

---

## 🚀 Instrucciones de Ejecución

### Requisitos previos

- Python 3.10 o superior
- Librería `customtkinter`

### Instalación de dependencias

```bash
pip install customtkinter
```

### Correr el IDE gráfico

```bash
python ide.py
```

### Correr el compilador en consola (sin interfaz)

```bash
python compi.py
```

---

## 🖥️ Funcionalidades del IDE

El IDE cuenta con las siguientes características:

- **Editor de código** con numeración de líneas y resaltado de sintaxis en tiempo real
- **▶ Compilar** — ejecuta el análisis léxico + sintáctico completo y muestra los resultados
- **🔍 Solo Léxico** — muestra únicamente los tokens identificados por línea
- **📋 Tabla de Símbolos** — lista todas las variables declaradas con su tipo, valor y estado de inicialización
- **❌ Errores** — resumen de todos los errores léxicos, sintácticos y semánticos encontrados
- **📂 Abrir** — carga un archivo de código desde el sistema de archivos
- **💾 Guardar** — exporta el código como archivo `.pqek` (formato nativo Costeñol)
- **📋 Ejemplo** — carga un código de ejemplo predefinido
- **🗑 Limpiar** — limpia el editor y todos los paneles de resultados

### Formato de guardado

Al guardar, el IDE exporta el archivo con extensión **`.pqek`**, que es el formato nativo del lenguaje Costeñol. También es posible guardar como `.txt` desde el mismo diálogo.

---

## 🎨 Resaltado de Sintaxis en el Editor

El editor colorea el código en tiempo real mientras escribes. Cada elemento del lenguaje tiene un color asignado:

| Color | Elemento | Ejemplo |
|---|---|---|
| 🔵 Azul claro | Tipos de dato | `Entero`, `Real`, `Texto`, `Logico` |
| 🟢 Verde | Captura de entrada | `Captura.Entero()`, `Captura.Texto()` |
| 🟠 Naranja | Salida por pantalla | `Mensaje.Texto(` |
| 🩷 Rosa | Cadenas de texto | `"Alejandra"`, `"Hola mundo"` |
| 🟣 Morado | Números literales | `12`, `3.1416`, `5` |
| 🩵 Cian | Valores lógicos | `verdadero`, `falso` |
| 🟡 Amarillo | Operadores | `+`, `-`, `*`, `/`, `=` |
| ⚪ Blanco | Identificadores (variables) | `num1`, `suma`, `nombre` |

> **Indicador de error visual:** Si una palabra está escrita incorrectamente o no corresponde a ningún elemento reconocido del lenguaje, aparece en **blanco sin resaltado**. Esto sirve como señal visual de que algo puede estar mal antes de compilar.

---

## 📊 Especificaciones del Lenguaje

### Tipos de dato

| Tipo | Descripción |
|---|---|
| `Entero` | Número entero |
| `Real` | Número decimal |
| `Texto` | Cadena de caracteres |
| `Logico` | Valor booleano (`verdadero` / `falso`) |

### Sentencias soportadas

```
# Declaración de variable
nombre Tipo;

# Captura de entrada
variable= Captura.Tipo();

# Asignación
variable=expresion;

# Salida por pantalla
Mensaje.Texto("texto");
```

### Operadores

`+`, `-`, `*`, `/`, `=`, `==`, `!=`, `<`, `>`, `<=`, `>=`

### Ejemplo de código Costeñol

```
num1 Entero;
nombre Texto;
pi Real;
num1= Captura.Entero();
nombre="Alejandra";
pi=3,1416;
Mensaje.Texto("Hola mundo");
```

---

## ⚙️ Fases del Compilador

1. **Análisis Léxico** — divide el código en tokens clasificados (tipos, identificadores, literales, operadores, etc.)
2. **Análisis Sintáctico** — verifica que las sentencias sigan la gramática del lenguaje
3. **Análisis Semántico** — comprueba que las variables estén declaradas antes de usarse y que los tipos sean compatibles
4. **Tabla de Símbolos** — registra todas las variables con su tipo, valor asignado y línea de declaración
