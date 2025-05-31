# keep_alive.py
import threading
import time
import requests

def keep_alive_ping(rover_ip):
    def ping():
        while True:
            try:
                response = requests.get(f"http://{rover_ip}/ping", timeout=5)
                print(f"[Keep-Alive] Ping enviado: {response.status_code}")
            except Exception as e:
                print(f"[Keep-Alive] Error al hacer ping: {e}")
            time.sleep(20)  # espera 20 segundos

    # Hilo en segundo plano
    hilo = threading.Thread(target=ping, daemon=True)
    hilo.start()
