from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    
# views.py
import requests
from django.http import JsonResponse

def ping_rover(request):
    rover_ip = request.GET.get("rover_ip")  # El frontend envía el dominio como parámetro
    if not rover_ip:
        return JsonResponse({"error": "Falta el rover_ip"}, status=400)

    try:
        response = requests.get(f"{rover_ip}ping", timeout=5)
        return JsonResponse({"status": response.status_code})
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)

