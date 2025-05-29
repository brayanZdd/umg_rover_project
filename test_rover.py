"""
Script de prueba para comunicarse directamente con el ESP8266.
Ejecutar desde la línea de comandos:
python test_rover.py
"""

import requests
import time

# Configuración del rover
ROVER_IP = "192.168.1.79"
BASE_URL = f"http://{ROVER_IP}"

def test_connection():
    """Prueba la conexión básica con el rover"""
    try:
        print(f"Probando conexión con: {BASE_URL}...")
        response = requests.get(f"{BASE_URL}/status", timeout=2)
        
        if response.status_code == 200:
            print("✅ Conexión exitosa - API nueva")
            print(f"Respuesta: {response.text}")
            return True
    except Exception:
        pass
    
    try:
        response = requests.get(BASE_URL, timeout=2)
        if response.status_code == 200:
            print("✅ Conexión exitosa - API antigua")
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False

def send_command(command, duration=0):
    """Envía un comando al rover"""
    try:
        if duration > 0:
            url = f"{BASE_URL}/command?cmd={command}&duration={duration}"
        else:
            url = f"{BASE_URL}/?State={command}"
        
        print(f"Enviando comando: {url}")
        response = requests.get(url, timeout=2)
        
        if response.status_code == 200:
            print(f"✅ Comando enviado: {command}")
            return True
        else:
            print(f"❌ Error al enviar comando. Código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False

def test_movement():
    """Prueba movimientos básicos"""
    commands = [
        ("F", "Adelante"),
        ("S", "Detener"),
        ("B", "Atrás"),
        ("S", "Detener"),
        ("L", "Izquierda"),
        ("S", "Detener"),
        ("R", "Derecha"),
        ("S", "Detener"),
        ("V", "Bocina")
    ]
    
    for cmd, desc in commands:
        print(f"\nProbando: {desc}")
        if send_command(cmd):
            time.sleep(1)  # Esperar 1 segundo entre comandos
        else:
            print("Prueba interrumpida debido a error")
            break

def test_advanced_command():
    """Prueba el comando con duración"""
    print("\nProbando comando con duración...")
    send_command("F", 2000)  # Avanzar durante 2 segundos (2000 ms)
    time.sleep(3)  # Esperar a que termine

if __name__ == "__main__":
    if test_connection():
        print("\n=== Iniciando pruebas de movimiento ===")
        test_movement()
        
        print("\n=== Iniciando pruebas avanzadas ===")
        test_advanced_command()
        
        print("\n✅ Pruebas completadas")
    else:
        print("\n❌ No se pudo establecer conexión con el rover")