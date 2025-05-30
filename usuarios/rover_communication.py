# rover_communication.py - VERSIÓN FINAL OPTIMIZADA

import requests
import logging
from django.conf import settings
import threading
import time

logger = logging.getLogger(__name__)

class RoverCommunicator:
    """Clase para manejar la comunicación con el rover ESP8266"""
    
    def __init__(self, rover_ip=None):
        """
        Inicializa un comunicador con el rover
        
        Args:
            rover_ip: IP del rover. Si es None, se usa la configuración predeterminada
        """
        self.rover_ip = rover_ip or getattr(settings, 'ROVER_IP', '192.168.1.98')
        self.session = requests.Session()
        self.session.headers.update({'ngrok-skip-browser-warning': 'true'})
        logger.info(f"Inicializado RoverCommunicator con IP: {self.rover_ip}")
    
    def _get_base_url(self):
        """Obtiene la URL base correctamente formateada"""
        if self.rover_ip.startswith('') or self.rover_ip.startswith(''):
            # Quitar trailing slash si existe
            return self.rover_ip.rstrip('')
        else:
            return f"{self.rover_ip}"
    
    def test_connection(self):
        """
        Prueba la conexión con el rover
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario
        """
        base_url = self._get_base_url()
        
        try:
            # Primero intentar con la API nueva
            url = f"{base_url}/status"
            logger.info(f"Probando conexión con rover en: {url}")
            
            response = self.session.get(url, timeout=1)
            if response.status_code == 200:
                logger.info("Conexión exitosa (API nueva)")
                return True
        except Exception as e:
            logger.warning(f"Error al conectar con API nueva: {str(e)}")
        
        try:
            # Si la API nueva falla, intentar con la API antigua
            url = f"{base_url}/"
            logger.info(f"Probando conexión con rover (API antigua) en: {url}")
            
            response = self.session.get(url, timeout=1)
            if response.status_code == 200:
                logger.info("Conexión exitosa (API antigua)")
                return True
        except Exception as e:
            logger.error(f"Error al conectar con API antigua: {str(e)}")
        
        return False
    
    def send_command(self, command, duration=0):
        """
        Envía un comando al rover - VERSIÓN OPTIMIZADA
        
        Args:
            command: Comando a enviar (F, B, L, R, etc.)
            duration: Duración del comando en milisegundos
        
        Returns:
            dict: Respuesta del rover
        """
        base_url = self._get_base_url()
        
        try:
            # Intentar primero con formato nuevo
            if duration > 0:
                url = f"{base_url}/command?cmd={command}&duration={duration}"
            else:
                url = f"{base_url}/command?cmd={command}"
            
            logger.info(f"Enviando comando: {url}")
            
            # TIMEOUT MUY CORTO para no esperar respuesta
            response = self.session.get(url, timeout=0.2)
            
            if response.status_code == 200:
                logger.info(f"Comando enviado exitosamente (API nueva)")
                return {
                    "success": True,
                    "message": "Comando enviado exitosamente",
                    "response": "OK"
                }
        except requests.exceptions.Timeout:
            # Timeout esperado - comando enviado
            return {
                "success": True,
                "message": "Comando enviado (timeout esperado)",
                "response": "OK"
            }
        except Exception as e:
            logger.warning(f"Error al enviar comando con API nueva: {str(e)}")
        
        try:
            # Si falla, intentar con formato antiguo
            url = f"{base_url}/?State={command}"
            logger.info(f"Intentando con formato antiguo: {url}")
            
            response = self.session.get(url, timeout=0.2)
            
            if response.status_code == 200 or response.status_code == 502:
                logger.info(f"Comando enviado exitosamente (API antigua)")
                
                # NO ESPERAR si hay duración - el ESP8266 lo maneja
                return {
                    "success": True,
                    "message": "Comando enviado exitosamente (API antigua)",
                    "response": "OK"
                }
        except requests.exceptions.Timeout:
            # Timeout esperado
            return {
                "success": True,
                "message": "Comando enviado (timeout esperado)",
                "response": "OK"
            }
        except Exception as e:
            # Ignorar errores 502 de ngrok
            if "502" in str(e):
                return {
                    "success": True,
                    "message": "Comando enviado (ngrok 502 ignorado)",
                    "response": "OK"
                }
            logger.error(f"Error al enviar comando con API antigua: {str(e)}")
        
        return {
            "success": False,
            "message": f"No se pudo enviar el comando {command} al rover"
        }
    
    def send_command_no_wait(self, command, duration=0):
        """
        Envía un comando al rover sin esperar respuesta completa.
        Útil para comandos de emergencia donde la velocidad es crítica.
        
        Args:
            command: Comando a enviar (F, B, L, R, etc.)
            duration: Duración del comando en milisegundos (ignorada en modo emergencia)
        
        Returns:
            dict: Estado básico del envío
        """
        base_url = self._get_base_url()
        
        def _send_async(url):
            """Función auxiliar para enviar comando en thread separado"""
            try:
                # Usar timeout muy corto y no esperar respuesta
                self.session.get(url, timeout=0.05)
            except:
                # Ignorar todos los errores
                pass
        
        try:
            # Intentar con ambas APIs en paralelo para máxima efectividad
            
            # API nueva
            if duration > 0:
                url_new = f"{base_url}/command?cmd={command}&duration={duration}"
            else:
                url_new = f"{base_url}/command?cmd={command}"
            
            # API antigua
            url_old = f"{base_url}/?State={command}"
            
            # Enviar a ambas APIs en threads separados
            thread1 = threading.Thread(target=_send_async, args=(url_new,))
            thread2 = threading.Thread(target=_send_async, args=(url_old,))
            
            thread1.daemon = True
            thread2.daemon = True
            
            thread1.start()
            thread2.start()
            
            # No esperar a que terminen los threads
            logger.debug(f"Comando de emergencia '{command}' enviado sin esperar respuesta")
            
            return {"success": True, "command": command}
            
        except Exception as e:
            logger.error(f"Error en envío de emergencia: {str(e)}")
            return {"success": False, "error": str(e)}

    def emergency_stop(self):
        """
        Ejecuta una parada de emergencia completa del rover.
        
        Returns:
            dict: Resultado de la operación de emergencia
        """
        logger.warning("🔴 PARADA DE EMERGENCIA ACTIVADA")

        commands_sent = 0

        try:
            # Estrategia 1: Bombardeo de comandos STOP rápido
            for _ in range(30):
                self.send_command_no_wait('S', 0)
                commands_sent += 1
                time.sleep(0.0005)  # 0.5ms

            # Estrategia 2: Secuencia de comandos conflictivos para forzar frenado
            conflict_sequence = [
                ('L', 5), ('R', 5), ('S', 0),
                ('F', 5), ('B', 5), ('S', 0),
                ('G', 5), ('I', 5), ('S', 0),
                ('H', 5), ('J', 5), ('S', 0),
            ]
            for cmd, duration in conflict_sequence:
                self.send_command_no_wait(cmd, duration)
                commands_sent += 1

            # Estrategia 3: Más comandos STOP finales
            for _ in range(20):
                self.send_command_no_wait('S', 0)
                commands_sent += 1
                time.sleep(0.0005)

            # Estrategia 4: Envío de comandos inválidos para potencial soft-reset
            for invalid_cmd in ['X', 'Z', 'Q', '0', '!', '*']:
                try:
                    self.send_command_no_wait(invalid_cmd, 0)
                    commands_sent += 1
                except Exception as e:
                    logger.debug(f"Comando inválido '{invalid_cmd}' ignorado: {str(e)}")

            # Envío final con método normal
            try:
                self.send_command('S', 0)
            except Exception as e:
                logger.warning(f"Fallo envio final de STOP: {str(e)}")

            time.sleep(0.2)  # Breve espera para asegurar ejecución
            logger.info(f"✅ Parada de emergencia completada: {commands_sent} comandos enviados")

            return {
                "success": True,
                "commands_sent": commands_sent,
                "message": f"Parada de emergencia ejecutada con {commands_sent} comandos"
            }

        except Exception as stop_error:
            logger.error(f"❌ Error durante parada de emergencia: {str(stop_error)}")
            return {
                "success": False,
                "commands_sent": commands_sent,
                "error": str(stop_error),
                "message": "Error durante parada de emergencia"
            }