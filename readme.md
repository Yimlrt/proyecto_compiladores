Proyecto: compilador costeñol

integrantes :
Emanuel Orozco
Vanelly Ariza
Yimileth Manga


📝 Descripción hasta ahora 25%
Este proyecto consiste en un Analizador Léxico desarrollado en Python. Su función es leer un archivo de código fuente de izquierda a derecha y descomponerlo en una serie de Tokens clasificados. El script identifica palabras reservadas, tipos de datos, identificadores, operadores y delimitadores.

📁 Contenido del Proyecto
tokens.py: Script principal que contiene la lógica del analizador.

prueba.txt: Archivo de texto que contiene el código fuente que será evaluado.

README.md: Este documento explicativo.

🚀 Instrucciones de Ejecución
Requisitos previos
Tener instalado Python 3.10 o superior.

Pasos para correr el proyecto
Asegúrate de que los archivos tokens.py y prueba.txt estén en la misma carpeta.

Abre una terminal 

Ubícate en la carpeta donde guardaste los archivos usando el comando "cd". Por ejemplo:
python tokens.py

📊 Especificaciones del Lenguaje
El analizador reconoce las siguientes estructuras:

Tipos: Entero, Real, Texto, Logico.

Comandos: Captura.TipoDato(), Mensaje.Texto().

Símbolos: =, ;, +, *, (, ).

Literales: Cadenas entre comillas ("...") y valores numéricos.