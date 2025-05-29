// editor.js - JavaScript para interactuar con el Editor UMG++ y el ESP8266 RC Car

document.addEventListener('DOMContentLoaded', function () {
    // Inicializar CodeMirror
    var editor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
        lineNumbers: true,
        theme: 'dracula',
        mode: 'javascript',
        indentUnit: 4,
        tabSize: 4,
        autoCloseBrackets: true,
        matchBrackets: true
    });

    // Configuración de colores para sintaxis personalizada
    editor.defineMode("umgpp", function () {
        return {
            token: function (stream, state) {
                if (stream.match(/PROGRAM|BEGIN|END/)) {
                    return "keyword"; // Azul para palabras clave
                } else if (stream.match(/avanzar_vlts|avanzar_ctms|avanzar_mts|girar|circulo|cuadrado|rotar|caminar|moonwalk/)) {
                    return "def"; // Celeste para comandos
                } else if (stream.match(/\(/)) {
                    stream.backUp(1);
                    if (stream.match(/\([\d\-]+\)/)) {
                        return "string"; // Verde para paréntesis y números
                    }
                    stream.next();
                    return "bracket"; // Verde para paréntesis
                } else if (stream.match(/\d+/)) {
                    return "number"; // Rojo para números
                } else if (stream.match(/;|\./)) {
                    return "punctuation"; // Para puntuación
                } else if (stream.match(/\+/)) {
                    return "operator"; // Para operadores
                }
                stream.next();
                return null;
            }
        };
    });

    editor.setOption("mode", "umgpp");

    // Función para añadir a la consola
    function logToConsole(message) {
        var consoleOutput = document.querySelector('.console-output');
        consoleOutput.innerHTML += '\n' + message;
        document.querySelector('.console').scrollTop = document.querySelector('.console').scrollHeight;
    }

    // Función para mostrar mensajes de error o éxito
    function showMessage(message, isError = false) {
        const alertClass = isError ? 'alert-danger' : 'alert-success';
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Insertar al principio del contenedor
        const container = document.querySelector('.editor-content');
        container.insertBefore(alertDiv, container.firstChild);

        // Auto-cerrar después de 5 segundos
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // Manejadores para el Rover
    let roverConnected = false;
    let roverIP = '192.168.1.79'; // IP predeterminada

    // Función para compilar el código
    async function compileCode() {
        const code = editor.getValue();
        logToConsole('Compilando código...');

        try {
            const response = await fetch('/api/compile/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken() // Función para obtener el token CSRF
                },
                body: JSON.stringify({ code })
            });

            const data = await response.json();

            if (data.success) {
                logToConsole('✅ ' + data.message);
                showMessage(data.message);
                return data;
            } else {
                logToConsole('❌ Error: ' + data.message);
                showMessage(data.message, true);
                return null;
            }
        } catch (error) {
            logToConsole('❌ Error de conexión: ' + error.message);
            showMessage('Error de conexión: ' + error.message, true);
            return null;
        }
    }

    // Función para simular el código
    async function simulateCode() {
        const compilationResult = await compileCode();
        if (!compilationResult) return;

        logToConsole('Simulando trayectoria...');

        try {
            const code = editor.getValue();
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
                logToConsole('✅ ' + data.message);
                showMessage(data.message);

                // Mostrar simulación
                displaySimulation(data.simulation_trace);
            } else {
                logToConsole('❌ Error: ' + data.message);
                showMessage(data.message, true);
            }
        } catch (error) {
            logToConsole('❌ Error de simulación: ' + error.message);
            showMessage('Error de simulación: ' + error.message, true);
        }
    }

    // Función para ejecutar el código en el rover
    async function executeCode() {
        const compilationResult = await compileCode();
        if (!compilationResult) return;

        // Verificar conexión con el rover antes de ejecutar
        if (!roverConnected) {
            const connectionResult = await testRoverConnection();
            if (!connectionResult) {
                return;
            }
        }

        logToConsole('Ejecutando en el rover...');

        try {
            const code = editor.getValue();
            const response = await fetch('/api/execute/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    code,
                    rover_ip: roverIP
                })
            });

            const data = await response.json();

            if (data.success) {
                logToConsole('✅ ' + data.message);
                showMessage('Código ejecutado exitosamente en el rover');
            } else {
                logToConsole('❌ Error: ' + data.message);
                showMessage(data.message, true);
            }
        } catch (error) {
            logToConsole('❌ Error de ejecución: ' + error.message);
            showMessage('Error de ejecución: ' + error.message, true);
        }
    }

    // Función para probar la conexión con el rover
    async function testRoverConnection() {
        logToConsole('Probando conexión con el rover en ' + roverIP + '...');

        try {
            const response = await fetch('/api/test-rover-connection/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ rover_ip: roverIP })
            });

            const data = await response.json();

            if (data.success) {
                logToConsole('✅ ' + data.message);
                showMessage(data.message);
                roverConnected = true;
                return true;
            } else {
                logToConsole('❌ ' + data.message);
                showMessage(data.message, true);

                // Mostrar diálogo para configurar IP
                showConfigDialog();
                return false;
            }
        } catch (error) {
            logToConsole('❌ Error al probar conexión: ' + error.message);
            showMessage('Error al probar conexión: ' + error.message, true);
            return false;
        }
    }

    // Mostrar diálogo para configurar IP del rover
    function showConfigDialog() {
        // Crear modal usando Bootstrap
        const modalHTML = `
        <div class="modal fade" id="roverConfigModal" tabindex="-1" aria-labelledby="roverConfigModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="roverConfigModalLabel">Configuración del Rover</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>No se pudo conectar con el rover. Por favor verifica la configuración:</p>
                        <form id="roverConfigForm">
                            <div class="mb-3">
                                <label for="roverIP" class="form-label">Dirección IP del Rover:</label>
                                <input type="text" class="form-control" id="roverIP" value="${roverIP}">
                                <div class="form-text">Introduce la IP del ESP8266. Por defecto es 192.168.1.79 en modo AP.</div>
                            </div>
                            <div class="mb-3 form-check">
                                <input type="checkbox" class="form-check-input" id="connectToRover">
                                <label class="form-check-label" for="connectToRover">Conectarse al Rover</label>
                            </div>
                            <div class="connection-options d-none">
                                <div class="mb-3">
                                    <label class="form-label">Opciones de conexión:</label>
                                    <div class="form-text mb-2">Hay dos formas de conectarse al rover:</div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="radio" name="connectionType" id="apMode" value="ap" checked>
                                        <label class="form-check-label" for="apMode">
                                            Conectarse a la red WiFi del Rover (Modo AP)
                                        </label>
                                        <div class="form-text">El rover crea su propia red WiFi. Debes conectar tu computadora a esta red.</div>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="radio" name="connectionType" id="staMode" value="sta">
                                        <label class="form-check-label" for="staMode">
                                            Conectar el Rover a tu red WiFi (Modo STA)
                                        </label>
                                        <div class="form-text">El rover se conecta a la misma red WiFi que tu computadora.</div>
                                    </div>
                                </div>
                                <div id="staModeOptions" class="d-none">
                                    <div class="mb-3">
                                        <label for="wifiSSID" class="form-label">Nombre de red WiFi (SSID):</label>
                                        <input type="text" class="form-control" id="wifiSSID">
                                    </div>
                                    <div class="mb-3">
                                        <label for="wifiPassword" class="form-label">Contraseña WiFi:</label>
                                        <input type="password" class="form-control" id="wifiPassword">
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" id="saveRoverConfig">Guardar y Probar</button>
                    </div>
                </div>
            </div>
        </div>
        `;

        // Añadir modal al DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('roverConfigModal'));
        modal.show();

        // Manejar eventos de la modal
        document.getElementById('connectToRover').addEventListener('change', function (e) {
            const connectionOptions = document.querySelector('.connection-options');
            if (e.target.checked) {
                connectionOptions.classList.remove('d-none');
            } else {
                connectionOptions.classList.add('d-none');
            }
        });

        document.querySelectorAll('input[name="connectionType"]').forEach(input => {
            input.addEventListener('change', function (e) {
                const staModeOptions = document.getElementById('staModeOptions');
                if (e.target.value === 'sta') {
                    staModeOptions.classList.remove('d-none');
                } else {
                    staModeOptions.classList.add('d-none');
                }
            });
        });

        // Guardar configuración
        document.getElementById('saveRoverConfig').addEventListener('click', function () {
            roverIP = document.getElementById('roverIP').value.trim();

            // Si se seleccionó conectar al rover
            if (document.getElementById('connectToRover').checked) {
                const connectionType = document.querySelector('input[name="connectionType"]:checked').value;

                if (connectionType === 'sta') {
                    const ssid = document.getElementById('wifiSSID').value.trim();
                    const password = document.getElementById('wifiPassword').value;

                    if (ssid && password) {
                        // Aquí se implementaría la lógica para enviar la configuración WiFi al rover
                        logToConsole(`Configurando rover para conectarse a la red ${ssid}...`);
                        showMessage(`Configurando rover para conectarse a la red ${ssid}...`);
                    } else {
                        showMessage('Debes proporcionar SSID y contraseña para el modo STA', true);
                        return;
                    }
                }
            }

            // Cerrar modal
            modal.hide();

            // Eliminar modal del DOM después de cerrar
            document.getElementById('roverConfigModal').addEventListener('hidden.bs.modal', function () {
                document.getElementById('roverConfigModal').remove();
            });

            // Probar conexión con la nueva IP
            testRoverConnection();
        });
    }

    // Función para mostrar la simulación
    function displaySimulation(simulationTrace) {
        const simulationContainer = document.querySelector('.simulation-container');
        const simulationArea = document.querySelector('.simulation-area');
        const rover = document.querySelector('.rover');

        // Limpiar simulación anterior
        simulationArea.innerHTML = '';

        // Crear nuevo rover
        const newRover = document.createElement('div');
        newRover.className = 'rover';
        simulationArea.appendChild(newRover);

        // Mostrar contenedor de simulación
        simulationContainer.style.display = 'flex';

        // Crear indicador de camino
        const pathContainer = document.createElement('div');
        pathContainer.className = 'path-container';
        simulationArea.appendChild(pathContainer);

        // Variables para la animación
        let animationIndex = 0;

        // Función para animar el rover
        function animateRover() {
            if (animationIndex >= simulationTrace.length) {
                return;
            }

            const step = simulationTrace[animationIndex];
            const position = step.position;

            // Actualizar posición del rover
            newRover.style.transform = `translate(${position.x}px, ${position.y}px) rotate(${position.direction}deg)`;

            // Crear marcador de camino
            const pathMarker = document.createElement('div');
            pathMarker.className = 'path-marker';
            pathMarker.style.left = `${position.x}px`;
            pathMarker.style.top = `${position.y}px`;
            pathContainer.appendChild(pathMarker);

            // Avanzar al siguiente paso
            animationIndex++;

            // Programar siguiente animación
            setTimeout(animateRover, 500);
        }

        // Iniciar animación
        setTimeout(animateRover, 500);
    }

    // Función para obtener el token CSRF
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue;
    }

    // Eventos para los botones
    document.getElementById('compile-btn').addEventListener('click', compileCode);
    document.getElementById('simulate-btn').addEventListener('click', simulateCode);
    document.getElementById('execute-btn').addEventListener('click', executeCode);

    // Cerrar simulación
    document.querySelector('.close-simulation').addEventListener('click', function () {
        document.querySelector('.simulation-container').style.display = 'none';
    });

    // Insertar comandos desde el sidebar
    document.querySelectorAll('.sidebar-item[data-command]').forEach(function (item) {
        item.addEventListener('click', function () {
            var command = this.getAttribute('data-command');
            var template = command + '(1);';
            editor.replaceSelection(template);
            editor.focus();
        });
    });

    // Cargar coreografías
    document.querySelectorAll('.sidebar-item[data-choreography]').forEach(function (item) {
        item.addEventListener('click', function () {
            var choreography = this.getAttribute('data-choreography');

            // Simular carga de coreografía predefinida
            if (choreography === 'coreografia1') {
                editor.setValue(`PROGRAM coreografia_1
BEGIN
    avanzar_mts(2);
    girar(1) + avanzar_ctms(80);
    circulo(50);
    girar(-1) + avanzar_mts(1);
    cuadrado(100);
END.`);
            } else if (choreography === 'coreografia2') {
                editor.setValue(`PROGRAM coreografia_2
BEGIN
    moonwalk(5);
    circulo(30);
    avanzar_mts(1);
    girar(1) + avanzar_ctms(50);
    girar(-1) + avanzar_ctms(50);
    rotar(3);
END.`);
            } else if (choreography === 'coreografia3') {
                editor.setValue(`PROGRAM coreografia_3
BEGIN
    cuadrado(50);
    rotar(2);
    avanzar_mts(1);
    caminar(5);
    girar(1) + avanzar_ctms(70);
    moonwalk(3);
END.`);
            }

            logToConsole('Coreografía "' + this.textContent + '" cargada.');
        });
    });

    // Otros botones
    document.getElementById('new-file').addEventListener('click', function () {
        if (confirm('¿Crear un nuevo archivo? Los cambios no guardados se perderán.')) {
            editor.setValue(`PROGRAM nuevo_programa
BEGIN
    
END.`);
            logToConsole('Nuevo archivo creado.');
        }
    });

    document.getElementById('save-file').addEventListener('click', function () {
        // Guardar en localStorage
        const code = editor.getValue();
        const programName = code.match(/PROGRAM\s+(\w+)/i)?.[1] || 'mi_programa';

        localStorage.setItem(`umgpp_${programName}`, code);
        logToConsole(`Archivo "${programName}" guardado localmente.`);
    });

    document.getElementById('open-file').addEventListener('click', function () {
        // Crear lista de archivos guardados
        const savedFiles = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('umgpp_')) {
                savedFiles.push(key.substring(6));
            }
        }

        if (savedFiles.length === 0) {
            alert('No hay archivos guardados.');
            return;
        }

        // Crear diálogo para seleccionar archivo
        const fileList = savedFiles.map(file => `<button class="list-group-item list-group-item-action" data-file="${file}">${file}</button>`).join('');

        const modalHTML = `
        <div class="modal fade" id="openFileModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Abrir archivo</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>Selecciona un archivo para abrir:</p>
                        <div class="list-group">
                            ${fileList}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;

        // Añadir modal al DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('openFileModal'));
        modal.show();

        // Manejar selección de archivo
        document.querySelectorAll('#openFileModal button[data-file]').forEach(button => {
            button.addEventListener('click', function () {
                const fileName = this.getAttribute('data-file');
                const code = localStorage.getItem(`umgpp_${fileName}`);

                if (code) {
                    editor.setValue(code);
                    logToConsole(`Archivo "${fileName}" cargado.`);
                }

                modal.hide();

                // Eliminar modal del DOM después de cerrar
                document.getElementById('openFileModal').addEventListener('hidden.bs.modal', function () {
                    document.getElementById('openFileModal').remove();
                });
            });
        });
    });

    // Probar conexión con el rover al cargar
    setTimeout(testRoverConnection, 2000);
});

// Estilos para la simulación
document.head.insertAdjacentHTML('beforeend', `
<style>
    .path-container {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 1;
    }
    
    .path-marker {
        position: absolute;
        width: 5px;
        height: 5px;
        background-color: #aa96da;
        border-radius: 50%;
        transform: translate(-50%, -50%);
    }
    
    .rover {
        position: absolute;
        width: 30px;
        height: 50px;
        background-color: #aa96da;
        border-radius: 5px;
        z-index: 2;
        transition: transform 0.5s ease;
        transform: translate(-50%, -50%);
    }
    
    .rover:before {
        content: '';
        position: absolute;
        width: 0;
        height: 0;
        top: -10px;
        left: 50%;
        transform: translateX(-50%);
        border-left: 10px solid transparent;
        border-right: 10px solid transparent;
        border-bottom: 10px solid #aa96da;
    }
</style>
`);