# 🌊 Proyecto: Compilador Costeñol

**Integrantes:**
- Emanuel Orozco
- Vanelly Ariza
- Yimileth Manga

> Proyecto de Compiladores — Corporación Universitaria del Caribe (CUL)

---

## 📝 Descripción

Este proyecto es un compilador para el lenguaje **Costeñol**, desarrollado en Python. Incluye un analizador léxico, un analizador sintáctico, un analizador semántico, una tabla de símbolos y una interfaz gráfica (IDE) completa para escribir, compilar y guardar código Costeñol.

---

## 📁 Contenido del Proyecto

| Archivo | Descripción |
|---|---|
| `compi.py` | Núcleo del compilador: tokenizador, analizador sintáctico, semántico y tabla de símbolos |
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
- **▶ Compilar** — ejecuta todas las fases del compilador y muestra los resultados por pestaña
- **🔍 Solo Léxico** — muestra únicamente los tokens identificados por línea con su posición
- **📋 Tabla de Símbolos** — lista todas las variables declaradas con tipo, valor, estado de inicialización y línea
- **❌ Errores** — resumen de todos los errores léxicos, sintácticos y semánticos encontrados
- **📂 Abrir** — carga un archivo de código desde el sistema de archivos
- **💾 Guardar** — exporta el código como archivo `.pqpk` (formato nativo Costeñol)
- **📋 Ejemplo** — carga un código de ejemplo predefinido
- **🗑 Limpiar** — limpia el editor y todos los paneles de resultados

### Formato de guardado

Al guardar, el IDE exporta el archivo con extensión **`.pqpk`**, que es el formato nativo del lenguaje Costeñol. También es posible guardar como `.txt` desde el mismo diálogo.

---

## 🎨 Resaltado de Sintaxis en el Editor

El editor colorea el código **en tiempo real** mientras escribes. Cada elemento del lenguaje tiene un color asignado:

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

| Tipo | Descripción | Ejemplo |
|---|---|---|
| `Entero` | Número entero | `num1 Entero;` |
| `Real` | Número decimal (usa coma) | `pi Real;` → `pi=3,1416;` |
| `Texto` | Cadena de caracteres | `nombre Texto;` |
| `Logico` | Valor booleano | `asis Logico;` |

### Sentencias soportadas

```
# Declaración de variable
nombre Tipo;

# Captura de entrada del usuario
variable= Captura.Tipo();

# Asignación con expresión
variable=expresion;

# Salida por pantalla (acepta texto y variables)
Mensaje.Texto("texto");
Mensaje.Texto("El resultado es:", variable);
```

### Operadores aritméticos

| Operador | Descripción |
|---|---|
| `+` | Suma |
| `-` | Resta |
| `*` | Multiplicación |
| `/` | División |

### Reglas importantes

- Toda sentencia debe terminar con `;`
- No se permiten tokens después del `;`
- No se permiten operadores consecutivos (`*+`, `++`, etc.)
- Las variables deben declararse antes de usarse
- Los tipos deben ser compatibles en operaciones y capturas
- Solo `Entero` y `Real` pueden usarse en operaciones aritméticas

### Ejemplo de código Costeñol

```
num1 Entero;
num2 Entero;
num3 Entero;
suma Entero;
nombre Texto;
pi Real;
num1= Captura.Entero();
num2= Captura.Entero();
num3= Captura.Entero();
suma=num1+(num2*num3);
nombre="Alejandra";
pi=3,1416;
Mensaje.Texto("El resultado es:", suma);
```

---

## ⚙️ Fases del Compilador

1. **Análisis Léxico** — divide el código en tokens clasificados (tipos, identificadores, literales, operadores, etc.)
2. **Análisis Sintáctico** — verifica que las sentencias sigan la gramática del lenguaje
3. **Análisis Semántico** — comprueba que:
   - Las variables estén declaradas antes de usarse
   - Los tipos sean compatibles en operaciones y capturas
   - No se usen variables de tipo `Texto` o `Logico` en operaciones aritméticas
   - No haya variables sin inicializar siendo usadas
4. **Tabla de Símbolos** — registra todas las variables con su tipo, valor asignado y línea de declaración
5. **Generación de Código Intermedio** — produce cuádruplas en formato de tres direcciones
6. **Optimización de Código** — aplica plegado de constantes, eliminación de redundancias, propagación de copias y eliminación de temporales muertos
7. **Generación de Código Final** — traduce las cuádruplas optimizadas a pseudoensamblador (`ALLOC`, `LOAD`, `STORE`, `MOV`, `ADD/SUB/MUL/DIV`, `IN`, `OUT`, `HALT`)

---

## ❌ Detección de Errores

El compilador detecta y reporta los siguientes tipos de errores:

| Tipo | Ejemplo |
|---|---|
| **Error Léxico** | Carácter no reconocido: `num1= 5@;` |
| **Error Sintáctico** | Tokens después del `;`: `num1=5;*` |
| **Error Sintáctico** | Operadores consecutivos: `suma=num1*+num2;` |
| **Error Semántico** | Variable no declarada: usar `x` sin `x Entero;` |
| **Error Semántico** | Tipo incompatible en captura: declarar `Entero` y capturar como `Texto` |
| **Error Semántico** | Tipo incompatible en operación: usar variable `Texto` en suma |
| **Error Semántico** | Variable declarada dos veces |
