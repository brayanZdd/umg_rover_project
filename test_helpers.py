#!/usr/bin/env python
"""
Script de ayuda para probar las funcionalidades de generación de PDF y envío de correos
Ejecuta este script con: python test_helpers.py

Asegúrate de estar en el entorno virtual de Django y de que el proyecto está configurado correctamente.
"""

import os
import sys
import django
import traceback

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'umg_rover.settings')

try:
    django.setup()
    print("Django configurado correctamente.")
except Exception as e:
    print(f"Error al configurar Django: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

# Verificar si las configuraciones están cargadas correctamente
from django.conf import settings

# Crear directorios necesarios si no existen
media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(os.getcwd(), 'media'))
os.makedirs(media_root, exist_ok=True)
os.makedirs(os.path.join(media_root, 'credenciales'), exist_ok=True)
os.makedirs(os.path.join(media_root, 'avatars'), exist_ok=True)

print(f"MEDIA_ROOT: {media_root}")
print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'No configurado')}")
print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'No configurado')}")

# Verificar si tenemos las carpetas de estáticos
static_dir = os.path.join(os.getcwd(), 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'img'), exist_ok=True)
    print(f"Creado directorio: {static_dir}")
    print(f"Creado directorio: {os.path.join(static_dir, 'img')}")
else:
    print(f"Directorio static ya existe: {static_dir}")

# Ahora podemos importar desde nuestras aplicaciones
try:
    from usuarios.utils import generar_credencial_pdf, generar_qr_code
    from usuarios.messaging import enviar_credencial_email, enviar_whatsapp
    print("Importaciones correctas.")
except ImportError as e:
    print(f"Error de importación: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

def test_generar_pdf():
    """Prueba la generación de PDF"""
    usuario_id = 205  # ID de prueba
    nombre = "umg"
    correo = "jcordone1@miumg.edu.gt"
    telefono = "38184787"
    nickname = "umg"

    
    print("\n==== PRUEBA DE GENERACIÓN DE PDF ====")
    print(f"Generando PDF para usuario: {nombre} (ID: {usuario_id})")
    
    # Verificar que exista la carpeta para los PDFs
    credenciales_dir = os.path.join(os.getcwd(), 'media', 'credenciales')
    os.makedirs(credenciales_dir, exist_ok=True)
    print(f"Directorio para credenciales: {credenciales_dir}")
    
    # Generar PDF
    try:
        pdf_path = generar_credencial_pdf(
            usuario_id=usuario_id,
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            nickname=nickname
        )
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"✅ PDF generado correctamente en: {pdf_path}")
            print(f"   Tamaño: {os.path.getsize(pdf_path)} bytes")
            return pdf_path
        else:
            print(f"❌ Error: No se pudo generar el PDF en {pdf_path}")
            if pdf_path:
                print(f"   La ruta existe? {os.path.exists(pdf_path)}")
            return None
    except Exception as e:
        print(f"❌ Error al generar PDF: {str(e)}")
        traceback.print_exc()
        return None

def test_enviar_email(pdf_path=None):
    """Prueba el envío de correo electrónico"""
    nombre = "Usuario de Prueba"
    correo = input("\nIngresa un correo electrónico para la prueba: ")
    usuario_id = 205
    nickname = "test_user"
    
    print("\n==== PRUEBA DE ENVÍO DE CORREO ====")
    
    # Si no se proporciona una ruta de PDF, tratar de generarla
    if not pdf_path:
        pdf_path = test_generar_pdf()
        if not pdf_path:
            print("❌ No se puede enviar el correo sin un PDF válido")
            return False
    
    print(f"Enviando correo a {correo} con PDF: {pdf_path}")
    
    # Verificar configuración de correo
    print("Verificando configuración de correo:")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'No configurado')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'No configurado')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'No configurado')}")
    print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'No configurado')}")
    
    # Enviar correo
    try:
        result = enviar_credencial_email(
            nombre=nombre,
            correo=correo,
            pdf_path=pdf_path,
            nickname=nickname,
            usuario_id=usuario_id
        )
        
        if result:
            print(f"✅ Correo enviado correctamente a {correo}")
        else:
            print("❌ Error al enviar el correo")
        
        return result
    except Exception as e:
        print(f"❌ Error al enviar correo: {str(e)}")
        traceback.print_exc()
        return False

def test_enviar_whatsapp():
    """Prueba el envío de mensaje de WhatsApp"""
    telefono = input("\nIngresa un número de teléfono para la prueba (formato: 502xxxxxxxx): ")
    nombre = "Usuario de Prueba"
    usuario_id = 204
    nickname = "test_user"
    
    print("\n==== PRUEBA DE ENVÍO DE WHATSAPP ====")
    
    # Verificar configuración de Twilio
    print("Verificando configuración de Twilio:")
    print(f"TWILIO_ACCOUNT_SID: {getattr(settings, 'TWILIO_ACCOUNT_SID', 'No configurado')}")
    twilio_auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', 'No configurado')
    print(f"TWILIO_AUTH_TOKEN: {'Configurado' if twilio_auth_token != 'No configurado' else 'No configurado'}")
    print(f"TWILIO_WHATSAPP_NUMBER: {getattr(settings, 'TWILIO_WHATSAPP_NUMBER', 'No configurado')}")
    
    print(f"Enviando WhatsApp a {telefono}")
    
    # Enviar WhatsApp
    try:
        result = enviar_whatsapp(
            telefono=telefono,
            nombre=nombre,
            usuario_id=usuario_id,
            nickname=nickname
        )
        
        if result:
            print(f"✅ WhatsApp enviado correctamente a {telefono}")
        else:
            print("❌ Error al enviar WhatsApp. Verifica tu configuración de Twilio.")
        
        return result
    except Exception as e:
        print(f"❌ Error al enviar WhatsApp: {str(e)}")
        traceback.print_exc()
        return False

def menu():
    """Menú principal del script de prueba"""
    print("\n====================================")
    print("  SCRIPT DE PRUEBA UMG ROVER 2.0")
    print("====================================")
    print("1. Probar generación de PDF")
    print("2. Probar envío de correo")
    print("3. Probar envío de WhatsApp")
    print("4. Probar todo (PDF + correo + WhatsApp)")
    print("0. Salir")
    
    opcion = input("\nSelecciona una opción: ")
    
    if opcion == "1":
        test_generar_pdf()
    elif opcion == "2":
        test_enviar_email()
    elif opcion == "3":
        test_enviar_whatsapp()
    elif opcion == "4":
        pdf_path = test_generar_pdf()
        if pdf_path:
            test_enviar_email(pdf_path)
        test_enviar_whatsapp()
    elif opcion == "0":
        print("\n¡Hasta luego!\n")
        return False
    else:
        print("\nOpción no válida. Inténtalo de nuevo.")
    
    return True

if __name__ == "__main__":
    try:
        print("Iniciando script de prueba...")
        continuar = True
        while continuar:
            continuar = menu()
    except KeyboardInterrupt:
        print("\nScript terminado por el usuario.")
    except Exception as e:
        print(f"\nError no controlado: {str(e)}")
        traceback.print_exc()