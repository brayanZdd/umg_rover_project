# usuarios/messaging.py
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime
import os
import traceback

def enviar_credencial_email(nombre, correo, pdf_path, nickname, usuario_id):
    """
    Envía un correo electrónico con la credencial del usuario

    Args:
        nombre: Nombre del usuario
        correo: Correo electrónico
        pdf_path: Ruta del archivo PDF de la credencial
        nickname: Nickname del usuario
        usuario_id: ID del usuario

    Returns:
        bool: True si el correo fue enviado correctamente, False en caso contrario
    """
    import logging
    import os
    import traceback
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    from django.conf import settings
    from datetime import datetime
    
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        logging.debug(f"Preparando correo para {correo}")
        logging.debug(f"Configuración: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}, USER={settings.EMAIL_HOST_USER}")

        # Verificar si el PDF existe
        if not os.path.exists(pdf_path):
            logging.error(f"El archivo PDF no existe en {pdf_path}")
            return False


        # Verificar tamaño del PDF
        filesize = os.path.getsize(pdf_path)
        logging.debug(f"Tamaño del archivo PDF: {filesize} bytes")
        if filesize < 500:  # Umbral mínimo para considerar el PDF válido
            logging.error(f"El archivo PDF es demasiado pequeño, posiblemente está vacío o corrupto.")
            return False

        # Preparar contexto para la plantilla
        context = {
            'nombre': nombre,
            'nickname': nickname,
            'usuario_id': usuario_id,
            'fecha': datetime.now().strftime('%d/%m/%Y')
        }

        # Renderizar plantilla de email
        try:
            email_html = render_to_string('usuarios/email_credencial.html', context)
            logging.debug("Plantilla de email renderizada correctamente")
        except Exception as e:
            logging.error(f"Error al renderizar plantilla de email: {str(e)}")
            # Usar un mensaje simple como alternativa
            email_html = f"""
            <html>
            <body>
                <h2>UMG Basic Rover 2.0 - Tu credencial de acceso</h2>
                <p>Hola {nombre},</p>
                <p>¡Tu registro en la plataforma UMG Basic Rover 2.0 ha sido exitoso!</p>
                <p>Hemos adjuntado tu credencial de acceso en formato PDF a este correo.</p>
                <p>Datos de tu cuenta:</p>
                <ul>
                    <li>Nickname: {nickname}</li>
                    <li>ID: {usuario_id}</li>
                </ul>
                <p>Saludos,<br>El equipo de UMG Basic Rover 2.0</p>
            </body>
            </html>
            """

        # Crear el mensaje
        subject = 'UMG Basic Rover 2.0 - Tu credencial de acceso'
        message = EmailMessage(
            subject=subject,
            body=email_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[correo],
        )
        message.content_subtype = 'html'  # Para enviar el email como HTML

        # Adjuntar el PDF
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
                message.attach(f'credencial_{usuario_id}.pdf', pdf_content, 'application/pdf')
                logging.debug(f"PDF adjuntado correctamente, tamaño: {len(pdf_content)} bytes")
        except Exception as e:
            logging.error(f"Error al adjuntar PDF: {str(e)}")
            traceback.print_exc()
            return False

        # Enviar el correo
        logging.debug(f"Enviando correo electrónico a {correo}...")
        try:
            sent = message.send(fail_silently=False)
            
            if sent:
                logging.debug("Correo enviado correctamente")
                return True
            else:
                logging.error("No se pudo enviar el correo")
                return False
        except Exception as e:
            logging.error(f"Error al enviar correo: {str(e)}")
            traceback.print_exc()
            
            # Intentar con otra configuración de correo
            try:
                logging.debug("Intentando enviar con configuración alternativa...")
                
                # Usar smtplib directamente como alternativa
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                from email.mime.application import MIMEApplication
                
                # Crear mensaje
                msg = MIMEMultipart()
                msg['From'] = settings.DEFAULT_FROM_EMAIL
                msg['To'] = correo
                msg['Subject'] = subject
                
                # Añadir texto
                msg.attach(MIMEText(email_html, 'html'))
                
                # Añadir PDF
                with open(pdf_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    pdf_attachment.add_header('Content-Disposition', f'attachment; filename=credencial_{usuario_id}.pdf')
                    msg.attach(pdf_attachment)
                
                # Conectar y enviar
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                text = msg.as_string()
                server.sendmail(settings.DEFAULT_FROM_EMAIL, correo, text)
                server.quit()
                
                logging.debug("Correo enviado correctamente con método alternativo")
                return True
            except Exception as alt_e:
                logging.error(f"Error al enviar correo con método alternativo: {str(alt_e)}")
                traceback.print_exc()
                return False
            
            return False

    except Exception as e:
        logging.error(f"Error general al enviar correo: {str(e)}")
        traceback.print_exc()
        return False

def enviar_whatsapp(telefono, nombre, usuario_id, nickname):
    """
    Envía un mensaje de WhatsApp con la información de la credencial
    
    Args:
        telefono: Número de teléfono
        nombre: Nombre del usuario
        usuario_id: ID del usuario
        nickname: Nickname del usuario
        
    Returns:
        bool: True si el mensaje fue enviado correctamente, False en caso contrario
    """
    try:
        from twilio.rest import Client
        
        # Verificar si Twilio está configurado
        if not hasattr(settings, 'TWILIO_ACCOUNT_SID') or not settings.TWILIO_ACCOUNT_SID:
            print("Twilio no está configurado correctamente")
            return False
            
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_number = settings.TWILIO_WHATSAPP_NUMBER
        
        # Formato: whatsapp:+numero
        to_number = f"whatsapp:+{telefono}"
        
        # Mensaje
        mensaje = f"""
        *UMG Basic Rover 2.0 - Credencial*
        
        Hola {nombre}, tu cuenta ha sido creada exitosamente.
        
        *Datos de acceso:*
        - Nickname: {nickname}
        - ID: {usuario_id}
        
        Para acceder a la plataforma, deberás usar la credencial que se te ha enviado por correo electrónico.
        """
        
        # Enviar mensaje
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=mensaje,
            from_=from_number,
            to=to_number
        )
        
        print(f"Mensaje de WhatsApp enviado: {message.sid}")
        return True
        
    except ImportError:
        print("Error: La biblioteca Twilio no está instalada")
        return False
    except Exception as e:
        print(f"Error al enviar WhatsApp: {str(e)}")
        traceback.print_exc()
        return False