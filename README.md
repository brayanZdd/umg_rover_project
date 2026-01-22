# UMG++ Rover Control Language

Lenguaje de programación propio (**UMG++**) para controlar un rover (carro/robot) mediante comandos de movimiento y secuencias coreografiadas.  
Incluye un **analizador léxico, sintáctico y semántico**, un **intérprete/transpilador** y una **plataforma web** para programar y simular trayectorias.

---

## 🚀 ¿Qué hace este proyecto?

- Permite escribir programas en archivos `.umgpp`
- Compila e interpreta instrucciones como:
  - Avanzar, retroceder, girar
  - Repeticiones y secuencias
  - Coreografías predefinidas
- Simula la trayectoria del rover
- Registra errores y bitácoras de ejecución
- Incluye una interfaz web con editor de código

---

## 🧠 Características Técnicas

- Lenguaje propio con gramática definida (UMG++)
- Análisis léxico
- Análisis sintáctico
- Análisis semántico
- Intérprete de instrucciones
- Sistema de coreografías
- Simulación visual del recorrido
- Bitácora de ejecución y errores
- Interfaz web con login y editor

---

## 🛠️ Tecnologías Usadas

| Tecnología | Uso |
|-----------|-----|
| JavaScript / Node.js | Backend del compilador |
| HTML / CSS / JS | Interfaz web |
| MySQL | Almacenamiento de usuarios y bitácoras |
| Jison / JFlex / CUP (o equivalente) | Lexer & Parser |
| Express | Servidor web |
| Canvas / SVG | Simulación del rover |

---

## 📄 Ejemplo de Código UMG++

```umgpp
INICIO
  AVANZAR 10
  GIRAR DERECHA
  AVANZAR 5
  REPETIR 3 {
    IZQUIERDA
    AVANZAR 2
  }
FIN
