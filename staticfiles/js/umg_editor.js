// static/js/umg_editor.js
document.addEventListener('DOMContentLoaded', function () {
    console.log("UMG Editor inicializado");

    // Elementos DOM
    const codeEditor = document.getElementById('code-editor');
    const consoleOutput = document.querySelector('.console-output');
    const compileBtn = document.getElementById('compile-btn');
    const simulateBtn = document.getElementById('simulate-btn');
    const executeBtn = document.getElementById('execute-btn');
    const roverIpInput = document.getElementById('rover-ip');

    // Comprobar que se encontraron todos los elementos
    console.log("Elementos DOM cargados:", {
        editor: codeEditor ? "✓" : "✗",
        console: consoleOutput ? "✓" : "✗",
        compileBtn: compileBtn ? "✓" : "✗",
        simulateBtn: simulateBtn ? "✓" : "✗",
        executeBtn: executeBtn ? "✓" : "✗",
        roverIp: roverIpInput ? "✓" : "✗"
    });

    // Función para agregar mensaje a la consola
    function logToConsole(message) {
        consoleOutput.textContent += '\n' + message;
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }

    // Obtener token CSRF para peticiones POST
    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    // Función para compilar código
    async function compileCode() {
        const code = codeEditor.value;
        logToConsole("Compilando código...");

        try {
            const response = await fetch('/api/compile/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ code })
            });

            const data = await response.json();

            if (data.success) {
                logToConsole("✓ Compilación exitosa: " + data.message);
                return data.commands;
            } else {
                logToConsole("✗ Error: " + data.message);
                return null;
            }
        } catch (error) {
            logToConsole("✗ Error de conexión: " + error.message);
            return null;
        }
    }

    // Función para simular código
    async function simulateCode() {
        logToConsole("Iniciando simulación...");

        try {
            const code = codeEditor.value;
            const response = await fetch('/api/simulate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ code })
            });

            const data = await response.json();

            if (data.success) {
                logToConsole("✓ Simulación completada");

                // Mostrar traza de simulación
                data.simulation_trace.forEach((step, index) => {
                    logToConsole(`${index + 1}. ${getCommandName(step.command)} durante ${step.duration}ms`);
                });
            } else {
                logToConsole("✗ Error: " + data.message);
            }
        } catch (error) {
            logToConsole("✗ Error de simulación: " + error.message);
        }
    }

    // Función para ejecutar código
    async function executeCode() {
        const roverIp = roverIpInput.value.trim();
        logToConsole(`Ejecutando en el rover (IP: ${roverIp})...`);

        try {
            const code = codeEditor.value;
            const response = await fetch('/api/execute/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    code,
                    rover_ip: roverIp
                })
            });

            const data = await response.json();

            if (data.success) {
                logToConsole("✓ Ejecución completada con éxito");
            } else {
                logToConsole("✗ Error: " + data.message);
            }
        } catch (error) {
            logToConsole("✗ Error de ejecución: " + error.message);
        }
    }

    // Función para obtener nombre descriptivo de un comando
    function getCommandName(cmd) {
        const names = {
            'F': "Adelante",
            'B': "Atrás",
            'L': "Izquierda",
            'R': "Derecha",
            'I': "Círculo",
            'S': "Detener",
            'V': "Bocina",
            'W': "Luz ON",
            'w': "Luz OFF"
        };

        return names[cmd] || cmd;
    }

    // Asignar eventos a los botones
    if (compileBtn) {
        compileBtn.addEventListener('click', compileCode);
    }

    if (simulateBtn) {
        simulateBtn.addEventListener('click', simulateCode);
    }

    if (executeBtn) {
        executeBtn.addEventListener('click', executeCode);
    }

    // Highlight sintaxis para código UMG++
    function highlightUMG() {
        if (codeEditor) {
            const code = codeEditor.value;
            // Esta es una aproximación muy simple del resaltado
            // En un entorno real, deberías usar CodeMirror o similar

            // Aquí podrías implementar un resaltado básico si lo necesitas
        }
    }

    // Intentar resaltar cuando cambia el texto
    if (codeEditor) {
        codeEditor.addEventListener('input', highlightUMG);
        // Resaltar inicialmente
        highlightUMG();
    }

    // Mensaje inicial
    logToConsole("Editor UMG++ listo");
});