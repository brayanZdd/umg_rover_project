# usuarios/tests.py
import os
from django.test import TestCase
from django.conf import settings
from .utils import generar_credencial_pdf, generar_qr_code
from .messaging import enviar_credencial_email, enviar_whatsapp

def test_generar_pdf():
    """Función de prueba para generar un PDF"""
    usuario_id = 9999  # ID de prueba
    nombre = "Usuario de Prueba"
    correo = "prueba@example.com"
    telefono = "12345678"
    nickname = "test_user"
    
    print("Iniciando prueba de generación de PDF...")
    
    # Generar PDF
    pdf_path = generar_credencial_pdf(
        usuario_id=usuario_id,
        nombre=nombre,
        correo=correo,
        telefono=telefono,
        nickname=nickname
    )
    
    if pdf_path and os.path.exists(pdf_path):
        print(f"PDF generado correctamente en: {pdf_path}")
        print(f"Tamaño: {os.path.getsize(pdf_path)} bytes")
        return pdf_path
    else:
        print("Error: No se pudo generar el PDF")
        return None

def test_enviar_email(pdf_path=None):
    """Función de prueba para enviar un correo electrónico"""
    nombre = "Usuario de Prueba"
    correo = "tu_correo@example.com"  # Reemplazar con un correo real
    usuario_id = 9999
    nickname = "test_user"
    
    # Si no se proporciona una ruta de PDF, tratar de generarla
    if not pdf_path:
        pdf_path = test_generar_pdf()
        if not pdf_path:
            print("No se puede enviar el correo sin un PDF válido")
            return False
    
    print(f"Enviando correo a {correo} con PDF: {pdf_path}")
    
    # Enviar correo
    result = enviar_credencial_email(
        nombre=nombre,
        correo=correo,
        pdf_path=pdf_path,
        nickname=nickname,
        usuario_id=usuario_id
    )
    
    if result:
        print("Correo enviado correctamente")
    else:
        print("Error al enviar el correo")
    
    return result

def test_enviar_whatsapp():
    """Función de prueba para enviar un mensaje de WhatsApp"""
    telefono = "50238184787"  # Reemplazar con un número real
    nombre = "Usuario de Prueba"
    usuario_id = 9999
    nickname = "test_user"
    
    print(f"Enviando WhatsApp a {telefono}")
    
    # Enviar WhatsApp
    result = enviar_whatsapp(
        telefono=telefono,
        nombre=nombre,
        usuario_id=usuario_id,
        nickname=nickname
    )
    
    if result:
        print("WhatsApp enviado correctamente")
    else:
        print("Error al enviar WhatsApp")
    
    return result

# Estas funciones pueden ser llamadas desde el shell de Django
# python manage.py shell
# from usuarios.tests import test_generar_pdf, test_enviar_email, test_enviar_whatsapp
# pdf_path = test_generar_pdf()
# test_enviar_email(pdf_path)
# test_enviar_whatsapp()