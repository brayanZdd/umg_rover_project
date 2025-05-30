# umg_transpiler.py
import re
import logging
import time

logger = logging.getLogger(__name__)

class UMGTranspiler:
    def __init__(self):
        self.reserved_words = [
            'PROGRAM', 'BEGIN', 'END', 'PUNTO',
            'avanzar_vlts', 'avanzar_ctms', 'avanzar_mts',
            'girar', 'circulo', 'cuadrado', 'rotar',
            'caminar', 'moonwalk'
        ]
        
        self.command_delay = 0.01  # 10ms en lugar de 200ms

    def _avanzar_vlts(self, n):
        if n == 0:
            raise ValueError("El parámetro de avanzar_vlts no puede ser 0")
        cmd = 'F' if n > 0 else 'B'
        return [(cmd, abs(n) * 565)]

    def _moonwalk(self, n):
        """
        Simula el moonwalk usando rotaciones cortas hacia atrás
        Alterna entre rotar hacia atrás por la izquierda y por la derecha
        Esto simula el movimiento de moonwalk donde las ruedas se mueven alternadamente
        """
        if n == 0:
            raise ValueError("El parámetro de moonwalk no puede ser 0")
        
        result = []
        pasos = abs(n)
        
        # Para cada paso del moonwalk mikel
        for i in range(pasos):
            # Usar los comandos de giro diagonal hacia atrás
            # H = BackwardLeft (ruedas derechas principalmente)
            # J = BackwardRight (ruedas izquierdas principalmente)
            
            # Paso 1: Mover principalmente lado derecho hacia atrás
            result.append(('H', 600))  # BackwardLeft
            result.append(('S', 100))  # Pausa corta
            
            # Paso 2: Mover principalmente lado izquierdo hacia atrás
            result.append(('J', 600))  # BackwardRight
            result.append(('S', 100))  # Pausa corta
        
        return result

    def _avanzar_ctms(self, n):
        if n == 0:
            raise ValueError("El parámetro de avanzar_ctms no puede ser 0")
        cmd = 'F' if n > 0 else 'B'
        return [(cmd, abs(n) * 30)]

    def _avanzar_mts(self, n):
        if n == 0:
            raise ValueError("El parámetro de avanzar_mts no puede ser 0")
        cmd = 'F' if n > 0 else 'B'
        return [(cmd, abs(n) * 2960)]

    def _girar(self, n):
        if n == 0:
            return [('F', 500)]
        return [('R', 500)] if n > 0 else [('L', 500)]

    def _circulo(self, r):
        if r < 10 or r > 200:
            raise ValueError("El radio del círculo debe estar entre 10 y 200 cm")
        return [('I', r * 100)]

    def _rotar(self, n):
        if n == 0:
            raise ValueError("El parámetro de rotar no puede ser 0")
        cmd = 'R' if n > 0 else 'L'
        return [(cmd, abs(n) * 2000)]

    def _caminar(self, n):
        if n == 0:
            raise ValueError("El parámetro de caminar no puede ser 0")
        cmd = 'F' if n > 0 else 'B'
        return [(cmd, abs(n) * 800)]

    def _cuadrado(self, n):
        if n < 10 or n > 200:
            raise ValueError("El lado del cuadrado debe estar entre 10 y 200 cm")
        duration = n * 50
        return [
            ('F', duration), ('R', 800),
            ('F', duration), ('R', 800),
            ('F', duration), ('R', 800),
            ('F', duration), ('S', 100)
        ]

    def parse(self, code):
        try:
            if not re.search(r'PROGRAM\s+\w+', code, re.IGNORECASE):
                return {"error": "Falta la declaración PROGRAM"}
            if not re.search(r'BEGIN', code, re.IGNORECASE):
                return {"error": "Falta la palabra clave BEGIN"}
            if not re.search(r'END', code, re.IGNORECASE):
                return {"error": "Falta la palabra clave END"}

            match = re.search(r'BEGIN(.*?)END', code, re.DOTALL | re.IGNORECASE)
            if not match:
                return {"error": "Estructura de programa inválida"}

            body = match.group(1).strip()
            
            # Validar que el cuerpo no esté vacío
            if not body:
                return {"error": "El programa no contiene instrucciones"}
            
            # Primero validar la sintaxis línea por línea
            lines = body.split('\n')
            current_instruction = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                current_instruction += " " + line if current_instruction else line
                
                # Si la línea termina con ; es el final de una instrucción
                if line.endswith(';'):
                    current_instruction = ""
                # Si la línea contiene un comando pero no termina con ;
                elif re.search(r'\w+\s*\([^)]*\)', line):
                    # Verificar si la siguiente línea no empieza con + (comando combinado)
                    line_index = lines.index(line)
                    if line_index < len(lines) - 1:
                        next_line = lines[line_index + 1].strip()
                        if not next_line.startswith('+') and not line.endswith('+'):
                            return {"error": f"Error de sintaxis: falta punto y coma (;) al final de: {line}"}
                    else:
                        # Es la última línea con contenido y no tiene ;
                        return {"error": f"Error de sintaxis: falta punto y coma (;) al final de: {line}"}
            
            # Si quedó una instrucción sin cerrar
            if current_instruction.strip():
                return {"error": f"Error de sintaxis: instrucción incompleta o falta punto y coma (;)"}
            
            # Procesar instrucciones normalmente
            instructions = [i.strip() for i in body.split(';') if i.strip()]
            commands = []

            for instr in instructions:
                if '+' in instr:
                    parts = [p.strip() for p in instr.split('+')]
                    for part in parts:
                        commands += self._parse_instruction(part)
                else:
                    commands += self._parse_instruction(instr)

            return commands

        except Exception as e:
            logger.error(f"Error al parsear código UMG++: {str(e)}")
            return {"error": f"Error al parsear: {str(e)}"}

    def _parse_instruction(self, instr):
        match = re.match(r'(\w+)\s*\(\s*(-?\d+)\s*\)', instr)
        if not match:
            raise ValueError(f"Instrucción inválida: {instr}")

        func_name = match.group(1)
        param = int(match.group(2))

        functions = {
            'avanzar_vlts': self._avanzar_vlts,
            'moonwalk': self._moonwalk,
            'avanzar_ctms': self._avanzar_ctms,
            'avanzar_mts': self._avanzar_mts,
            'girar': self._girar,
            'circulo': self._circulo,
            'rotar': self._rotar,
            'caminar': self._caminar,
            'cuadrado': self._cuadrado
        }

        if func_name not in functions:
            raise ValueError(f"Función desconocida: {func_name}")

        return functions[func_name](param)

    def execute_commands(self, commands, rover_communicator):
        if isinstance(commands, dict) and "error" in commands:
            return commands

        results = []

        try:
            for cmd_data in commands:
                cmd, duration = cmd_data
                
                # Enviar comando
                result = rover_communicator.send_command(cmd, duration)
                results.append(result)

                if not result["success"]:
                    return {"error": f"Error al ejecutar comando {cmd}", "results": results}

                # Esperar la duración del comando para que se complete
                time.sleep(duration / 1000.0)
                
                # Delay mínimo entre comandos (5ms)
                time.sleep(0.005)

            return {"success": True, "results": results}

        except Exception as e:
            logger.error(f"Error al ejecutar comandos: {str(e)}")
            return {"error": f"Error al ejecutar comandos: {str(e)}", "results": results}