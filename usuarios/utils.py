# usuarios/utils.py
import os
import qrcode
import base64
import logging
from io import BytesIO
from datetime import datetime
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import traceback

def get_execution_status():
    """
    Devuelve el estado actual de ejecución
    """
    global current_execution
    return current_execution.copy()
    

def generar_qr_code(data):
    """
    Genera un código QR y lo devuelve como una imagen base64
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        
        # Convertir a base64 para incluirlo en HTML
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return qr_base64
    except Exception as e:
        logging.error(f"Error al generar QR: {str(e)}")
        return None
#----------------------------------------------------------- INICIO GENERACION PDF-------------------------------------------------------------------------

def obtener_o_generar_pdf(usuario_id, nombre=None, correo=None, telefono=None, nickname=None, avatar_data=None):
    """
    Obtiene un PDF existente o genera uno nuevo si no existe usando una plantilla JPG
    """

    logging.basicConfig(level=logging.DEBUG)
    
    # Asegurar directorio
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'credenciales'), exist_ok=True)
    
    # Ruta del PDF
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'credenciales', f'credencial_{usuario_id}.pdf')
    logging.debug(f"Ruta del PDF: {pdf_path}")
    
    # Verificar si el archivo ya existe
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 500:
        logging.debug(f"PDF encontrado: {pdf_path}, {os.path.getsize(pdf_path)} bytes")
        return pdf_path
        
    # Si no existe o no se proporcionaron datos, verificar si podemos obtenerlos
    if not all([nombre, correo, telefono, nickname]):
        try:
            from usuarios.services import get_usuario_by_id
            usuario_data = get_usuario_by_id(usuario_id)
            if usuario_data:
                nombre = nombre or usuario_data['nombre']
                correo = correo or usuario_data['correo']
                telefono = telefono or usuario_data['telefono']
                nickname = nickname or usuario_data['nickname']
                avatar_data = avatar_data or usuario_data.get('avatar', '')
                logging.debug(f"Datos obtenidos de la base de datos: {nombre}, {nickname}")
        except Exception as e:
            logging.error(f"Error al obtener datos del usuario: {str(e)}")
            traceback.print_exc()
    
    # Verificar que tenemos los datos necesarios
    if not all([nombre, correo, telefono, nickname]):
        logging.error(f"No hay suficientes datos para generar PDF para usuario {usuario_id}")
        return None
        
    # Generar el PDF con plantilla
    logging.debug(f"Generando PDF con plantilla para usuario {usuario_id}")
    
    try:
        # Buscar la plantilla
        template_path = None
        possible_paths = [
            os.path.join(settings.STATIC_ROOT, 'img', 'templates', 'credencial_template.jpg'),
            os.path.join(settings.BASE_DIR, 'static', 'img', 'templates', 'credencial_template.jpg'),
        ]
        
        # Agregar paths desde STATICFILES_DIRS
        for static_dir in settings.STATICFILES_DIRS:
            possible_paths.append(os.path.join(static_dir, 'img', 'templates', 'credencial_template.jpg'))
        
        for path in possible_paths:
            if os.path.exists(path):
                template_path = path
                logging.debug(f"Plantilla encontrada en: {template_path}")
                break
        
        # Crear el PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Si tenemos plantilla, usarla
        if template_path and os.path.exists(template_path):
            logging.debug("Usando plantilla JPG para el PDF")
            
            # Dibujar la plantilla como fondo
            c.drawImage(template_path, 0, 0, width=width, height=height)
            
            # Configurar color blanco para el texto
            c.setFillColor(colors.white)
            
            # NICKNAME - En el rectángulo superior
            c.setFont("Helvetica-Bold", 28)
            c.drawCentredString(width/2, height - 420, nickname.upper())
            
            # CORREO - En el rectángulo inferior
            c.setFont("Helvetica", 28)
            c.drawCentredString(width/2, height - 490, correo)
            
            # Avatar circular en el centro
            if avatar_data and len(avatar_data) > 0:
                try:
                    logging.debug(f"Procesando avatar para plantilla")
                    
                    # Decodificar avatar
                    avatar_binary = base64.b64decode(avatar_data)
                    avatar_buffer = BytesIO(avatar_binary)
                    
                    # Abrir con PIL
                    avatar_image = PILImage.open(avatar_buffer)
                    
                    # Convertir a RGB si es necesario
                    if avatar_image.mode != 'RGB':
                        avatar_image = avatar_image.convert('RGB')
                    
                    # Crear máscara circular
                    size = (200, 200)  # Reducido de 220 a 200
                    avatar_image = avatar_image.resize(size, PILImage.Resampling.LANCZOS)
                    
                    # Crear imagen circular
                    mask = PILImage.new('L', size, 0)
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0) + size, fill=255)
                    
                    # Aplicar máscara circular
                    output = PILImage.new('RGBA', size, (0, 0, 0, 0))
                    output.paste(avatar_image, (0, 0))
                    output.putalpha(mask)
                    
                    # Guardar temporalmente
                    temp_avatar_path = os.path.join(os.path.dirname(pdf_path), f'temp_avatar_{usuario_id}.png')
                    output.save(temp_avatar_path, 'PNG')
                    
                    # Dibujar en el PDF - ajustado para quedar dentro del círculo
                    if os.path.exists(temp_avatar_path):
                        avatar_x = (width - 200) / 2  # Centrar horizontalmente
                        avatar_y = height - 370  # Subir un poco la posición
                        c.drawImage(temp_avatar_path, avatar_x, avatar_y, width=200, height=200, mask='auto')
                        os.remove(temp_avatar_path)
                        logging.debug("Avatar circular añadido sobre la plantilla")
                except Exception as e:
                    logging.error(f"Error al procesar avatar: {str(e)}")
            
            # Generar y añadir QR en el cuadro inferior
            try:
                qr_data = f"ID:{usuario_id},Nickname:{nickname},Correo:{correo}"
                
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_buffer = BytesIO()
                qr_img.save(qr_buffer, format="PNG")
                qr_buffer.seek(0)
                
                # Guardar QR temporalmente
                temp_qr_path = os.path.join(os.path.dirname(pdf_path), f'temp_qr_{usuario_id}.png')
                with open(temp_qr_path, 'wb') as f:
                    f.write(qr_buffer.getvalue())
                
                # Dibujar QR centrado en el cuadro inferior
                if os.path.exists(temp_qr_path):
                    qr_size = 200  # Reducido de 250 a 220
                    qr_x = (width - qr_size) / 2  # Centrar horizontalmente
                    qr_y = 60  # Subir un poco de 100 a 120
                    c.drawImage(temp_qr_path, qr_x, qr_y, width=qr_size, height=qr_size)
                    os.remove(temp_qr_path)
                    logging.debug("QR añadido en el cuadro inferior")
            except Exception as e:
                logging.error(f"Error al generar QR: {str(e)}")
                
        else:
            # Si no hay plantilla, usar el método original
            logging.warning("No se encontró plantilla, usando método de generación original")
            
            # Aquí va tu código original de generación sin plantilla
            # (el que ya tienes implementado)
            
            # Fondo blanco
            c.setFillColor(colors.white)
            c.rect(0, 0, width, height, fill=1)
            
            # Header con color de fondo
            c.setFillColor(colors.lavender)
            c.rect(0, height - 2*inch, width, 2*inch, fill=1)
            
            # Título centrado
            c.setFont("Helvetica-Bold", 28)
            c.setFillColor(colors.black)
            c.drawCentredString(width/2, height - 1*inch, "UMG Basic Rover 2.0")
            
            # ... resto del código original ...
        
        # Guardar el PDF
        c.save()
        
        # Verificar creación
        if os.path.exists(pdf_path):
            pdf_size = os.path.getsize(pdf_path)
            logging.debug(f"PDF generado correctamente: {pdf_path} ({pdf_size} bytes)")
            return pdf_path
        else:
            logging.error(f"PDF no encontrado después de guardarlo en {pdf_path}")
            return None
            
    except Exception as e:
        logging.error(f"Error al generar PDF: {str(e)}")
        traceback.print_exc()
        return None
    #----------------------------------------------- FIN GENERACION PDF-------------------------------------------------------------------------

def generar_avatar_predeterminado(nickname):
    """Genera avatar con imagen base y nickname"""
    import base64
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    from django.conf import settings
    
    try:
        # Buscar imagen base
        imagen_path = os.path.join(settings.STATIC_ROOT, 'img', 'avatars', 'default_avatar.jpg')
        
        if not os.path.exists(imagen_path):
            # Buscar en STATICFILES_DIRS
            for static_dir in settings.STATICFILES_DIRS:
                imagen_path = os.path.join(static_dir, 'img', 'avatars', 'default_avatar.jpg')
                if os.path.exists(imagen_path):
                    break
        
        if os.path.exists(imagen_path):
            # Usar imagen base
            img = Image.open(imagen_path).resize((200, 200))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            draw = ImageDraw.Draw(img)
            
            # Configurar fuente más grande
            font_size = 36
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("Arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Calcular posición para centrar el texto horizontalmente y bajarlo
            try:
                bbox = draw.textbbox((0, 0), nickname, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                text_width = len(nickname) * 20
                text_height = font_size
            
            # Posición: centrado horizontalmente, más abajo verticalmente
            x = (200 - text_width) // 2
            y = 101  # Cambiado de centro (100) a más abajo (130)
            
            # Contorno negro grueso para mejor visibilidad
            contorno_grosor = 3
            for dx in range(-contorno_grosor, contorno_grosor + 1):
                for dy in range(-contorno_grosor, contorno_grosor + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), nickname, fill=(0, 0, 0), font=font)
            
            # Texto principal en blanco
            draw.text((x, y), nickname, fill=(255, 255, 255), font=font)  # Cambiado a blanco
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=95)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error en avatar predeterminado: {e}")
        pass
    
    # Si falla, crear avatar simple mejorado
    return crear_avatar_simple_texto_mejorado(nickname)


def crear_avatar_simple_texto_mejorado(nickname):
    """Crear avatar simple de texto mejorado como respaldo"""
    import base64
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    
    try:
        # Crear imagen simple con colores más atractivos
        img = Image.new('RGB', (200, 200), (70, 130, 180))
        draw = ImageDraw.Draw(img)
        
        # Dibujar círculo más grande
        draw.ellipse([10, 10, 190, 190], fill=(240, 240, 240))
        
        # Fuente más grande
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Calcular posición centrada horizontalmente y más abajo
        if font:
            try:
                bbox = draw.textbbox((0, 0), nickname, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                text_width = len(nickname) * 16
                text_height = 28
        else:
            text_width = len(nickname) * 16
            text_height = 28
        
        x = (200 - text_width) // 2
        y = 150  # Más abajo también en el avatar de respaldo
        
        # Contorno negro grueso
        contorno = 3
        for dx in range(-contorno, contorno + 1):
            for dy in range(-contorno, contorno + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), nickname, fill=(0, 0, 0), font=font)
        
        # Texto principal en blanco
        draw.text((x, y), nickname, fill=(255, 255, 255), font=font)  # Cambiado a blanco
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=95)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error en avatar simple: {e}")
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
# Mantener la función original para compatibilidad
def generar_credencial_pdf(usuario_id, nombre, correo, telefono, nickname, avatar_data=None):
    """
    Función de compatibilidad que redirige a obtener_o_generar_pdf
    """
    logging.info(f"Llamada a generar_credencial_pdf redirigida a obtener_o_generar_pdf para usuario {usuario_id}")
    return obtener_o_generar_pdf(
        usuario_id=usuario_id,
        nombre=nombre,
        correo=correo,
        telefono=telefono,
        nickname=nickname,
        avatar_data=avatar_data
    )
# Reemplaza o agrega esta función en tu utils.py

def get_usuario_by_id(usuario_id):
    """
    Obtiene los datos de un usuario por su ID - versión compatible con obtener_o_generar_pdf
    """
    try:
        from usuarios import services
        
        with services.get_mysql_connection() as cursor:
            cursor.execute("""
                SELECT id_usuario, nombre, correo, telefono, id_rol, 
                       password, avatar, nickname
                FROM tb_usuarios 
                WHERE id_usuario = %s
            """, [usuario_id])
            
            usuario = cursor.fetchone()
            
            if usuario:
                # Tu configuración devuelve tuplas, convertimos a diccionario
                return {
                    'id_usuario': usuario[0],
                    'nombre': usuario[1], 
                    'correo': usuario[2],
                    'telefono': usuario[3],
                    'id_rol': usuario[4],
                    'password': usuario[5],
                    'avatar': usuario[6],
                    'nickname': usuario[7]
                }
    except Exception as e:
        print(f"Error al obtener usuario por ID en utils: {e}")
        import traceback
        traceback.print_exc()
    
    return None