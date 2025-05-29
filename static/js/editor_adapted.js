// editor_simple.js - Versión simplificada pero funcional para controlar el rover

document.addEventListener('DOMContentLoaded', function () {
    console.log("Editor UMG++ inicializado");

    // Referencias a elementos del DOM
    const codeEditor = document.querySelector('textarea');
    const consoleOutput = document.querySelector('.console-output, #console-output');
    const compileBtn = document.querySelector('#compile-btn, button[id="compile-btn"]');
    const simulateBtn = document.querySelector('#simulate-btn, button[id="simulate-btn"]');
    const executeBtn = document.querySelector('#execute-btn, button[id="execute-btn"]');
    const roverIpInput = document.querySelector('#rover-ip, input[id="rover-ip"]');

    // Asegurarse de que tenemos todos los elementos necesarios
    if (!codeEditor || !consoleOutput) {
        console.error("No se pudieron encontrar elementos esenciales en la página");
        return;
    }

    // Función para agregar mensaje a la consola
    function logToConsole(message) {
        if (consoleOutput) {
            consoleOutput.textContent += '\n' + message;
            consoleOutput.scrollTop = consoleOutput.scrollHeight;
        }
        console.log(message);
    }

    logToConsole("Editor UMG++ listo para usar");

    // Obtener el token CSRF
    function getCSRFToken() {
        const tokenElements = document.querySelectorAll('input[name="csrfmiddlewaretoken"]');
        if (tokenElements.length > 0) {
            return tokenElements[0].value;
        }
        // Alternativa: obtener del cookie
        return document.cookie.replace(/(?:(?:^|.*;\s*)csrftoken\s*\=\s*([^;]*).*$)|^.*$/, "$1");
    }

    // Función para compilar código UMG++
    async function compileCode() {
        const code = codeEditor.value;

        if (!code || code.trim() === '') {
            logToConsole("Error: El editor está vacío");
            return null;
        }

        logToConsole("Compilando código UMG++...");

        // Validación básica de la estructura del programa
        if (!code.includes('PROGRAM') || !code.includes('BEGIN') || !code.includes('END')) {
            logToConsole("Error de sintaxis: El programa debe incluir PROGRAM, BEGIN y END");
            return null;
        }

        // Extraer comandos del programa
        const programBody = extractProgramBody(code);
        if (!programBody) {
            logToConsole("Error: No se pudo extraer el cuerpo del programa");
            return null;
        }

        // Dividir en instrucciones
        const instructions = programBody.split(';');
        const commands = [];

        // Procesar cada instrucción
        for (let instruction of instructions) {
            instruction = instruction.trim();
            if (!instruction) continue;

            // Intentar analizar la instrucción
            try {
                const parsedCommand = parseInstruction(instruction);
                if (parsedCommand) {
                    commands.push(parsedCommand);
                }
            } catch (error) {
                logToConsole(`Error al analizar instrucción "${instruction}": ${error.message}`);
                return null;
            }
        }

        if (commands.length === 0) {
            logToConsole("Advertencia: No se encontraron comandos válidos");
        } else {
            logToConsole(`Compilación exitosa: ${commands.length} comandos generados`);
        }

        return commands;
    }

    // Función para extraer el cuerpo del programa
    function extractProgramBody(code) {
        const beginIndex = code.indexOf('BEGIN');
        const endIndex = code.lastIndexOf('END');

        if (beginIndex === -1 || endIndex === -1 || beginIndex >= endIndex) {
            return null;
        }

        return code.substring(beginIndex + 5, endIndex).trim();
    }

    // Función para analizar una instrucción
    function parseInstruction(instruction) {
        // Manejar instrucciones combinadas (con +)
        if (instruction.includes('+')) {
            const parts = instruction.split('+');
            const commands = [];

            for (const part of parts) {
                const command = parseSimpleInstruction(part.trim());
                if (command) {
                    commands.push(command);
                }
            }

            return commands;
        } else {
            return parseSimpleInstruction(instruction);
        }
    }

    // Función para analizar una instrucción simple
    function parseSimpleInstruction(instruction) {
        // Extraer nombre de función y argumentos
        const match = instruction.match(/(\w+)\s*\(\s*(-?\d+)\s*\)/);
        if (!match) {
            throw new Error(`Sintaxis inválida: ${instruction}`);
        }

        const functionName = match[1];
        const argument = parseInt(match[2]);

        // Mapear funciones UMG++ a comandos del rover
        switch (functionName) {
            case 'avanzar_vlts':
                return {
                    command: argument > 0 ? 'F' : 'B',
                    duration: Math.abs(argument) * 1500 // 1.5 segundos por vuelta
                };
            case 'avanzar_ctms':
                return {
                    command: argument > 0 ? 'F' : 'B',
                    duration: Math.abs(argument) * 50 // 50ms por cm
                };
            case 'avanzar_mts':
                return {
                    command: argument > 0 ? 'F' : 'B',
                    duration: Math.abs(argument) * 5000 // 5 segundos por metro
                };
            case 'girar':
                if (argument === 1) {
                    return { command: 'R', duration: 500 };
                } else if (argument === -1) {
                    return { command: 'L', duration: 500 };
                } else if (argument === 0) {
                    return { command: 'F', duration: 500 };
                } else {
                    throw new Error(`Valor inválido para girar: ${argument}`);
                }
            case 'circulo':
                if (argument < 10 || argument > 200) {
                    throw new Error(`El radio debe estar entre 10 y 200 cm`);
                }
                return { command: 'I', duration: argument * 100 };
            case 'cuadrado':
                if (argument < 10 || argument > 200) {
                    throw new Error(`El lado debe estar entre 10 y 200 cm`);
                }
                // Nota: Un cuadrado requeriría múltiples comandos, pero para simplificar:
                return [
                    { command: 'F', duration: argument * 50 },
                    { command: 'R', duration: 800 },
                    { command: 'F', duration: argument * 50 },
                    { command: 'R', duration: 800 },
                    { command: 'F', duration: argument * 50 },
                    { command: 'R', duration: 800 },
                    { command: 'F', duration: argument * 50 },
                    { command: 'S', duration: 0 }
                ];
            case 'rotar':
                return {
                    command: argument > 0 ? 'R' : 'L',
                    duration: Math.abs(argument) * 2000 // 2 segundos por vuelta
                };
            case 'caminar':
                return {
                    command: argument > 0 ? 'F' : 'B',
                    duration: Math.abs(argument) * 800 // 0.8 segundos por paso
                };
            case 'moonwalk':
                return {
                    command: argument > 0 ? 'B' : 'F', // Invertido para moonwalk
                    duration: Math.abs(argument) * 1000 // 1 segundo por paso de moonwalk
                };
            default:
                throw new Error(`Función desconocida: ${functionName}`);
        }
    }

    // Función para simular código
    function simulateCode() {
        compileCode().then(commands => {
            if (!commands) return;

            logToConsole("Simulando ejecución (esto no mueve el rover real):");

            // Mostrar los comandos generados
            for (let i = 0; i < commands.length; i++) {
                const cmd = Array.isArray(commands[i]) ? commands[i] : [commands[i]];

                for (const c of cmd) {
                    const commandName = getCommandName(c.command);
                    logToConsole(`${i + 1}. ${commandName} durante ${c.duration}ms`);
                }
            }

            logToConsole("Simulación completada");
        });
    }

    // Función para obtener el nombre descriptivo de un comando
    function getCommandName(cmd) {
        switch (cmd) {
            case 'F': return "Adelante";
            case 'B': return "Atrás";
            case 'L': return "Izquierda";
            case 'R': return "Derecha";
            case 'G': return "Adelante-Izquierda";
            case 'I': return "Adelante-Derecha";
            case 'H': return "Atrás-Izquierda";
            case 'J': return "Atrás-Derecha";
            case 'S': return "Detener";
            case 'V': return "Bocina";
            case 'W': return "Luz ON";
            case 'w': return "Luz OFF";
            default: return cmd;
        }
    }

    // Función para ejecutar código en el rover real
    async function executeCode() {
        const commands = await compileCode();
        if (!commands) return;

        const roverIp = roverIpInput.value.trim() || '192.168.1.79';

        logToConsole(`Ejecutando en el rover (IP: ${roverIp})...`);

        // Aplanar la lista de comandos (puede contener arrays anidados)
        const flattenedCommands = flattenCommands(commands);

        // Ejecutar los comandos secuencialmente
        for (let i = 0; i < flattenedCommands.length; i++) {
            const cmd = flattenedCommands[i];

            try {
                const url = `http://${roverIp}/command?cmd=${cmd.command}&duration=${cmd.duration}`;
                logToConsole(`Enviando: ${getCommandName(cmd.command)} (${cmd.duration}ms)`);

                const response = await fetch(url);

                if (response.ok) {
                    logToConsole(`✓ Comando ${i + 1}/${flattenedCommands.length} ejecutado`);
                } else {
                    // Si falla el nuevo formato, intentar con el antiguo
                    const oldUrl = `http://${roverIp}/?State=${cmd.command}`;
                    logToConsole(`Reintentando con formato antiguo: ${oldUrl}`);

                    const oldResponse = await fetch(oldUrl);

                    if (oldResponse.ok) {
                        logToConsole(`✓ Comando ${i + 1}/${flattenedCommands.length} ejecutado (formato antiguo)`);

                        // Si se usa el formato antiguo, necesitamos manejar la duración manualmente
                        if (cmd.duration > 0) {
                            await new Promise(resolve => setTimeout(resolve, cmd.duration));

                            // Enviar comando de detención
                            await fetch(`http://${roverIp}/?State=S`);
                        }
                    } else {
                        logToConsole(`✗ Error al ejecutar comando ${i + 1}/${flattenedCommands.length}`);
                    }
                }

                // Esperar un poco entre comandos
                if (i < flattenedCommands.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            } catch (error) {
                logToConsole(`✗ Error de red: ${error.message}`);
                break;
            }
        }

        logToConsole("Ejecución completada");
    }

    // Función para aplanar arrays anidados
    function flattenCommands(commands) {
        const result = [];

        for (const cmd of commands) {
            if (Array.isArray(cmd)) {
                result.push(...cmd);
            } else {
                result.push(cmd);
            }
        }

        return result;
    }

    // Asociar funciones a los botones
    if (compileBtn) {
        compileBtn.addEventListener('click', function (e) {
            e.preventDefault();
            compileCode();
        });
    }

    if (simulateBtn) {
        simulateBtn.addEventListener('click', function (e) {
            e.preventDefault();
            simulateCode();
        });
    }

    if (executeBtn) {
        executeBtn.addEventListener('click', function (e) {
            e.preventDefault();
            executeCode();
        });
    }

    // Inicializar la IP del rover
    if (roverIpInput && !roverIpInput.value) {
        roverIpInput.value = '192.168.1.79';
    }
});