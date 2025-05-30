from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .forms import RegistroForm, LoginForm
from . import services
import base64
import qrcode
from io import BytesIO
import os
from datetime import datetime
from django.template.loader import render_to_string
from django.urls import reverse
from django.http import HttpResponse, FileResponse
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.utils.html import mark_safe
import traceback
import threading
import time
import sys
import requests
# Importaciones para ReportLab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from PIL import Image
import logging
from .umg_transpiler import UMGTranspiler
from .rover_communication import RoverCommunicator
import json
import logging


# Configuración del logger
logger = logging.getLogger(__name__)

def compile_code(request):
    """
    Vista para compilar código UMG++ y verificar su sintaxis
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            
            transpiler = UMGTranspiler()
            commands = transpiler.parse(code)
            
            if isinstance(commands, dict) and "error" in commands:
                return JsonResponse({
                    "success": False,
                    "message": commands["error"]
                })
            
            return JsonResponse({
                "success": True,
                "message": f"Compilación exitosa. Se generaron {len(commands)} comandos.",
                "commands": [{"command": cmd, "duration": dur} for cmd, dur in commands]
            })
            
        except Exception as e:
            logger.error(f"Error al compilar: {str(e)}")
            return JsonResponse({
                "success": False,
                "message": f"Error al compilar: {str(e)}"
            })
    
    return JsonResponse({
        "success": False,
        "message": "Método no permitido"
    })

def simulate_code(request):
    """
    Vista para simular la ejecución del código UMG++
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            
            transpiler = UMGTranspiler()
            commands = transpiler.parse(code)
            
            if isinstance(commands, dict) and "error" in commands:
                return JsonResponse({
                    "success": False,
                    "message": commands["error"]
                })
            
            # Generamos una traza de simulación
            simulation_trace = []
            position = {"x": 150, "y": 150, "direction": 0}  # Posición inicial
            
            for cmd, duration in commands:
                # Actualizar posición según el comando
                if cmd == "F":  # Adelante
                    position["y"] -= duration * 10
                elif cmd == "B":  # Atrás
                    position["y"] += duration * 10
                elif cmd == "L":  # Izquierda
                    position["direction"] -= 90
                    position["x"] -= duration * 10
                elif cmd == "R":  # Derecha
                    position["direction"] += 90
                    position["x"] += duration * 10
                
                # Añadir posición a la traza
                simulation_trace.append({
                    "command": cmd,
                    "duration": duration,
                    "position": {
                        "x": position["x"],
                        "y": position["y"],
                        "direction": position["direction"]
                    }
                })
            
            return JsonResponse({
                "success": True,
                "message": "Simulación exitosa",
                "simulation_trace": simulation_trace
            })
            
        except Exception as e:
            logger.error(f"Error al simular: {str(e)}")
            return JsonResponse({
                "success": False,
                "message": f"Error al simular: {str(e)}"
            })
    
    return JsonResponse({
        "success": False,
        "message": "Método no permitido"
    })

def execute_code(request):
    """
    Vista para ejecutar código UMG++ en el rover real
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            
            # Obtener IP del rover (configurada o proporcionada)
            rover_ip = data.get('rover_ip', None)
            
            transpiler = UMGTranspiler()
            commands = transpiler.parse(code)
            
            if isinstance(commands, dict) and "error" in commands:
                return JsonResponse({
                    "success": False,
                    "message": commands["error"]
                })
            
            # Inicializar comunicador
            rover_communicator = RoverCommunicator(rover_ip)
            
            # Probar la conexión antes de ejecutar
            if not rover_communicator.test_connection():
                return JsonResponse({
                    "success": False,
                    "message": f"No se pudo conectar con el rover en {rover_communicator.rover_ip}"
                })
            
            # Ejecutar comandos
            result = transpiler.execute_commands(commands, rover_communicator)
            
            if isinstance(result, dict) and "error" in result:
                return JsonResponse({
                    "success": False,
                    "message": result["error"]
                })
            
            return JsonResponse({
                "success": True,
                "message": "Ejecución exitosa",
                "results": result.get("results", [])
            })
            
        except Exception as e:
            logger.error(f"Error al ejecutar: {str(e)}")
            return JsonResponse({
                "success": False,
                "message": f"Error al ejecutar: {str(e)}"
            })
    
    return JsonResponse({
        "success": False,
        "message": "Método no permitido"
    })

def test_rover_connection(request):
    """
    Vista para probar la conexión con el rover
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            rover_ip = data.get('rover_ip', None)
            
            # Inicializar comunicador
            rover_communicator = RoverCommunicator(rover_ip)
            
            # Probar conexión
            connection_ok = rover_communicator.test_connection()
            
            if connection_ok:
                return JsonResponse({
                    "success": True,
                    "message": f"Conexión exitosa con el rover en {rover_communicator.rover_ip}"
                })
            else:
                return JsonResponse({
                    "success": False,
                    "message": f"No se pudo conectar con el rover en {rover_communicator.rover_ip}"
                })
            
        except Exception as e:
            logger.error(f"Error al probar conexión: {str(e)}")
            return JsonResponse({
                "success": False,
                "message": f"Error al probar conexión: {str(e)}"
            })
    
    return JsonResponse({
        "success": False,
        "message": "Método no permitido"
    })

def test_rover_view(request):
    """Vista para la página de prueba del rover"""
    return render(request, 'test_rover.html')

def direct_control(request):
    """Vista para controlar directamente el rover sin usar UMG++"""
    return render(request, 'direct_control.html')
def registro_exitoso(request):
    """Vista para la página de registro exitoso."""
    messages.info(request, "Por favor, inicia sesión con tus nuevas credenciales.")
    return redirect('login')

def login(request):
    """Vista para gestionar el inicio de sesión de usuarios"""
    import logging
    logging.basicConfig(level=logging.INFO)
         
    # Limpiar el mensaje de registro exitoso después de mostrarlo una vez
    if 'registro_exitoso_message' in request.session:
        del request.session['registro_exitoso_message']
         
    if request.method == 'POST':
        login_type = request.POST.get('login_type', 'traditional')
        
        if login_type == 'qr':
            # Login con código QR
            qr_data = request.POST.get('qr_data', '')
            logging.info(f"Intento de login con QR: {qr_data}")
            
            try:
                # Parsear los datos del QR
                # Formato esperado: "ID:123,Nickname:user,Correo:email@example.com"
                qr_parts = {}
                for part in qr_data.split(','):
                    if ':' in part:
                        key, value = part.split(':', 1)
                        qr_parts[key.strip()] = value.strip()
                
                # Verificar que tenemos los campos necesarios
                if 'ID' in qr_parts and 'Nickname' in qr_parts:
                    usuario_id = int(qr_parts['ID'])
                    nickname = qr_parts['Nickname']
                    
                    # Verificar que el usuario existe y obtener sus datos
                    with services.get_mysql_connection() as cursor:
                        cursor.execute("""
                            SELECT id_usuario, id_rol, nickname
                            FROM tb_usuarios
                            WHERE id_usuario = %s AND nickname = %s
                        """, [usuario_id, nickname])
                        
                        usuario = cursor.fetchone()
                        
                        if usuario:
                            # Login exitoso con QR
                            # Registrar el ingreso usando el mismo procedimiento que el login tradicional
                            try:
                                cursor.callproc('insertar_ingreso', [usuario_id, 7, ''])
                                cursor.execute("SELECT LAST_INSERT_ID()")
                                result = cursor.fetchone()
                                ingreso_id = result[0] if result else None
                                logging.info(f"Ingreso registrado con QR: ingreso_id={ingreso_id}")
                            except Exception as e:
                                logging.error(f"Error al registrar ingreso con QR: {str(e)}")
                                # Intentar obtener el último ingreso como en el login tradicional
                                try:
                                    cursor.execute("""
                                        SELECT id_ingreso 
                                        FROM tb_ingresos 
                                        WHERE id_usuario = %s AND fecha_salida IS NULL
                                        ORDER BY fecha_ingreso DESC 
                                        LIMIT 1
                                    """, [usuario_id])
                                    
                                    ultimo_ingreso = cursor.fetchone()
                                    if ultimo_ingreso:
                                        ingreso_id = ultimo_ingreso[0]
                                        logging.info(f"Recuperado ingreso_id={ingreso_id} para sesión QR")
                                    else:
                                        ingreso_id = None
                                except Exception as e2:
                                    logging.error(f"Error al buscar último ingreso QR: {str(e2)}")
                                    ingreso_id = None
                            
                            # Guardar datos en la sesión (igual que el login tradicional)
                            request.session['usuario_id'] = usuario[0]
                            request.session['rol_id'] = usuario[1]
                            request.session['id_grupo'] = 7
                            
                            # Verificar ingreso_id
                            if ingreso_id:
                                request.session['ingreso_id'] = ingreso_id
                                logging.info(f"Sesión QR iniciada: usuario_id={usuario[0]}, ingreso_id={ingreso_id}")
                            else:
                                logging.warning(f"No se obtuvo ingreso_id para usuario QR {usuario[0]}")
                            
                            # Mensaje de bienvenida
                            messages.success(request, f"¡Bienvenido, {nickname}!")
                            
                            # Redireccionar según el rol (igual que el login tradicional)
                            if usuario[1] == 2:  # Si es administrador
                                return redirect('dashboard')
                            else:
                                return redirect('editor')
                        else:
                            messages.error(request, "Código QR inválido o usuario no encontrado.")
                else:
                    messages.error(request, "El código QR no contiene la información necesaria.")
                    
            except Exception as e:
                logging.error(f"Error al procesar login con QR: {str(e)}")
                messages.error(request, "Error al procesar el código QR. Por favor, intenta de nuevo.")
        
        else:
            # Login tradicional (tu código original sin cambios)
            form = LoginForm(request.POST)
            if form.is_valid():
                nickname = form.cleaned_data['nickname']
                password = form.cleaned_data['password']
                             
                # Verificar credenciales
                usuario_data, mensaje = services.login_usuario(nickname, password)
                             
                if usuario_data:
                    # Guardar datos básicos en la sesión
                    request.session['usuario_id'] = usuario_data['id_usuario']
                    request.session['rol_id'] = usuario_data['id_rol']
                    request.session['id_grupo'] = usuario_data.get('id_grupo', 7)
                                     
                    # Verificar ingreso_id
                    ingreso_id = usuario_data.get('id_ingreso')
                    if ingreso_id:
                        request.session['ingreso_id'] = ingreso_id
                        logging.info(f"Sesión iniciada: usuario_id={usuario_data['id_usuario']}, ingreso_id={ingreso_id}")
                    else:
                        logging.warning(f"No se obtuvo ingreso_id para usuario {usuario_data['id_usuario']}")
                        # Intentar obtener el último ingreso
                        try:
                            with services.get_mysql_connection() as cursor:
                                cursor.execute("""
                                    SELECT id_ingreso 
                                    FROM tb_ingresos 
                                    WHERE id_usuario = %s AND fecha_salida IS NULL
                                    ORDER BY fecha_ingreso DESC 
                                    LIMIT 1
                                """, [usuario_data['id_usuario']])
                                                     
                                ultimo_ingreso = cursor.fetchone()
                                if ultimo_ingreso:
                                    request.session['ingreso_id'] = ultimo_ingreso[0]
                                    logging.info(f"Recuperado ingreso_id={ultimo_ingreso[0]} para sesión")
                        except Exception as e:
                            logging.error(f"Error al buscar último ingreso: {str(e)}")
                                     
                    # Mensaje de bienvenida
                    messages.success(request, f"¡Bienvenido, {nickname}!")
                                     
                    # Redireccionar según el rol
                    if usuario_data['id_rol'] == 2:  # Si es administrador
                        return redirect('dashboard')
                    else:
                        return redirect('editor')
                else:
                    messages.error(request, mensaje)
    else:
        form = LoginForm()
    
    # Asegurar que siempre hay un form para el template
    if 'form' not in locals():
        form = LoginForm()
         
    return render(request, 'usuarios/login.html', {'form': form})
"""
Añade esta vista a tu archivo views.py para depurar la comunicación con el rover
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def debug_rover(request):
    """
    Vista para pruebas directas con el rover desde la interfaz web
    Acceder a: /debug-rover/?cmd=F para probar
    """
    command = request.GET.get('cmd', '')
    rover_ip = request.GET.get('ip', '192.168.1.98')
    duration = request.GET.get('duration', 0)
    
    if not command:
        return JsonResponse({
            'status': 'error',
            'message': 'Comando no especificado. Usa ?cmd=X donde X es un comando válido.'
        })
    
    try:
        # Construir URL según parámetros
        base_url = f"http://{rover_ip}"
        
        if int(duration) > 0:
            url = f"{base_url}/command?cmd={command}&duration={duration}"
        else:
            # Intentar primero el nuevo formato
            url = f"{base_url}/command?cmd={command}"
        
        logger.info(f"Enviando comando al rover: {url}")
        
        # Realizar solicitud HTTP GET
        response = requests.get(url, timeout=2)
        
        # Si falla con nuevo formato, intentar formato antiguo
        if response.status_code != 200:
            url = f"{base_url}/?State={command}"
            logger.info(f"Intentando formato antiguo: {url}")
            response = requests.get(url, timeout=2)
        
        # Verificar respuesta
        if response.status_code == 200:
            return JsonResponse({
                'status': 'success',
                'message': f'Comando {command} enviado correctamente',
                'url': url,
                'response': response.text
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al enviar comando. Código: {response.status_code}',
                'url': url
            })
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión con el rover: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error de conexión: {str(e)}',
            'rover_ip': rover_ip
        })

def session_info(request):
    """Vista para depurar la información de la sesión"""
    session_data = {
        'usuario_id': request.session.get('usuario_id'),
        'ingreso_id': request.session.get('ingreso_id'),
        'rol_id': request.session.get('rol_id'),
        'id_grupo': request.session.get('id_grupo')
    }
    
    # También mostrar todos los demás items en la sesión
    all_session = {key: request.session.get(key) for key in request.session.keys()}
    
    return render(request, 'debug_session.html', {
        'session_data': session_data,
        'all_session': all_session
    })

def logout(request):
    """Cierra la sesión del usuario y registra su salida"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Obtener información de la sesión
    usuario_id = request.session.get('usuario_id')
    ingreso_id = request.session.get('ingreso_id')
    
    logging.info(f"Cerrando sesión para usuario_id: {usuario_id}, ingreso_id: {ingreso_id}")
    
    # Registrar salida si tenemos un ingreso_id
    if ingreso_id:
        try:
            # Registrar la salida usando el procedimiento almacenado
            resultado = services.registrar_salida(ingreso_id)
            logging.info(f"Resultado de registrar_salida: {resultado}")
            
            # Verificar si la salida se registró correctamente
            if "exitosamente" not in str(resultado).lower():
                messages.warning(request, f"Advertencia: {resultado}")
        except Exception as e:
            logging.error(f"Error al registrar salida: {str(e)}")
            messages.error(request, f"Error al registrar tu salida: {str(e)}")
    else:
        logging.warning("No hay ingreso_id en la sesión")
    
    # Limpiar sesión
    request.session.flush()
    logging.info("Sesión cerrada correctamente")
    
    # Redirigir a login
    return redirect('login')


#------------------------------------------------------------------------------------------------------------------------------


def registro(request):
    """Vista para registrar un nuevo usuario y generar su credencial"""
    # Configurar logging al inicio
    from django.contrib.auth.hashers import make_password
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('registro_debug.log', mode='a')
        ]
    )
    
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES)
        
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            correo = form.cleaned_data['correo']
            telefono = form.cleaned_data['telefono']
            nickname = form.cleaned_data['nickname']
            password = form.cleaned_data['password']
            
            logging.info("="*50)
            logging.info("INICIO DEL PROCESO DE REGISTRO")
            logging.info(f"Nombre: {nombre}, Nickname: {nickname}, Correo: {correo}")
            
            # Procesar avatar
            avatar_data = ""
            try:
                # Opción 1: Imagen de cámara
                camera_image = request.POST.get('camera_image_data', '')
                if camera_image and camera_image.startswith('data:image'):
                    base64_data = camera_image.split(',')[1]
                    avatar_data = base64_data
                    logging.info(f"Avatar capturado desde cámara, tamaño: {len(avatar_data)} caracteres")
                
                # Opción 2: Archivo subido
                elif 'avatar' in request.FILES and request.FILES['avatar'].size > 0:
                    avatar_img = request.FILES['avatar']
                    avatar_data = base64.b64encode(avatar_img.read()).decode('utf-8')
                    logging.info(f"Avatar procesado correctamente, tamaño: {len(avatar_data)} caracteres")
                
                # Opción 3: Generar avatar predeterminado
                else:
                    from usuarios.utils import generar_avatar_predeterminado
                    avatar_data = generar_avatar_predeterminado(nickname)
                    logging.info(f"Avatar predeterminado generado para nickname: {nickname}")
                
                # Si aún no hay avatar_data, crear uno simple como respaldo
                if not avatar_data:
                    avatar_data = crear_avatar_simple_texto(nickname)
                    logging.info("Usando avatar simple de respaldo")
                    
            except Exception as e:
                logging.error(f"Error procesando avatar: {str(e)}")
                avatar_data = crear_avatar_simple_texto(nickname)
                logging.info("Avatar de respaldo creado debido a error")
            
            # Guardar usuario usando el procedimiento almacenado
            try:
                # Verificar que el procedimiento almacenado existe y funciona
                password_encriptada = make_password(password)
                logging.info("Llamando a services.registro_usuario...")
                logging.info(f"Parámetros: nombre={nombre}, nickname={nickname}, correo={correo}, telefono={telefono}")
                logging.info(f"Avatar data length: {len(avatar_data) if avatar_data else 0}")
                
                resultado = services.registro_usuario(
                    nombre, nickname, password, avatar_data, correo, telefono
                )
                logging.info(f"Resultado del registro: '{resultado}' (tipo: {type(resultado)})")
                
                # Si no hay excepción, asumimos que el registro fue exitoso
                # incluso si el resultado está vacío
            except Exception as e:
                logging.error(f"Error al registrar usuario: {str(e)}")
                logging.error(f"Tipo de error: {type(e)}")
                logging.error(traceback.format_exc())
                
                # Si el error es porque el usuario ya existe, intentar obtener su ID
                if "Duplicate entry" in str(e) or "ya existe" in str(e).lower():
                    logging.info("Parece que el usuario ya existe, intentando obtener su ID...")
                    try:
                        with services.get_mysql_connection() as cursor:
                            cursor.execute("SELECT id_usuario FROM tb_usuarios WHERE nickname = %s", [nickname])
                            row = cursor.fetchone()
                            if row:
                                messages.error(request, f"El nickname '{nickname}' ya está en uso. Por favor elige otro.")
                    except:
                        pass
                
                messages.error(request, f"Error al registrar usuario: {str(e)}")
                return render(request, 'usuarios/registro.html', {'form': form})
            
            # Verificar si el registro fue exitoso
            # Si resultado está vacío o es None, pero no hubo excepción, asumimos éxito
            if resultado is None or resultado == '' or "exitosamente" in str(resultado).lower():
                try:
                    # Obtener el id del usuario recién creado
                    with services.get_mysql_connection() as cursor:
                        cursor.execute("SELECT id_usuario FROM tb_usuarios WHERE nickname = %s", [nickname])
                        row = cursor.fetchone()
                        if not row:
                            raise Exception("No se pudo obtener el ID del usuario recién creado")
                        usuario_id = row[0]  # row es una tupla, usar índice 0
                        logging.info(f"ID del usuario creado: {usuario_id}")
                    
                    # IMPORTANTE: Importar las funciones al principio del try
                    from usuarios.utils import obtener_o_generar_pdf
                    from usuarios.messaging import enviar_credencial_email
                    
                    # Generar PDF de credencial
                    logging.info("Iniciando generación de PDF...")
                    pdf_path = None
                    try:
                        pdf_path = obtener_o_generar_pdf(
                            usuario_id=usuario_id,
                            nombre=nombre,
                            correo=correo,
                            telefono=telefono,
                            nickname=nickname,
                            avatar_data=avatar_data
                        )
                        logging.info(f"Resultado de obtener_o_generar_pdf: {pdf_path}")
                    except Exception as pdf_error:
                        logging.error(f"Error al generar PDF: {str(pdf_error)}")
                        logging.error(traceback.format_exc())
                    
                    # Verificar si se generó el PDF
                    email_result = "No se pudo enviar el correo."
                    if pdf_path and os.path.exists(pdf_path):
                        logging.info(f"PDF generado correctamente: {pdf_path}")
                        logging.info(f"Tamaño del PDF: {os.path.getsize(pdf_path)} bytes")
                        
                        # Enviar credencial por correo
                        logging.info("Iniciando envío de correo...")
                        try:
                            email_enviado = enviar_credencial_email(
                                nombre=nombre,
                                correo=correo,
                                pdf_path=pdf_path,
                                nickname=nickname,
                                usuario_id=usuario_id
                            )
                            
                            if email_enviado:
                                logging.info("✅ Correo electrónico enviado correctamente")
                                email_result = "El correo con la credencial se ha enviado correctamente."
                                messages.success(request, f"Se ha enviado la credencial a {correo}")
                            else:
                                logging.warning("❌ Error al enviar el correo electrónico")
                                email_result = "No se pudo enviar el correo. Por favor, descarga tu credencial directamente."
                                messages.warning(request, "No se pudo enviar el correo, pero puedes descargar tu credencial.")
                        except Exception as email_error:
                            logging.error(f"❌ Error enviando correo: {str(email_error)}")
                            logging.error(traceback.format_exc())
                            email_result = f"No se pudo enviar el correo: {str(email_error)}"
                    else:
                        logging.error("No se pudo generar el PDF o no existe en la ruta esperada")
                        if pdf_path:
                            logging.error(f"Ruta del PDF: {pdf_path}")
                            logging.error(f"¿Existe el archivo?: {os.path.exists(pdf_path) if pdf_path else 'N/A'}")
                        email_result = "No se pudo generar la credencial en PDF."
                    
                    # Crear URL para descargar la credencial
                    credencial_url = reverse('credencial', args=[usuario_id])
                    download_url = f"{credencial_url}?download=1"
                    
                    # Mensaje de éxito usando HTML
                    success_message = f"""
                    <div class="alert alert-success">
                        <h4 class="alert-heading">¡Registro exitoso!</h4>
                        <p>Se ha creado tu cuenta correctamente con el nickname: <strong>{nickname}</strong></p>
                        <p>{email_result}</p>
                        <p>Tu credencial está lista para descargar:</p>
                        <a href="{download_url}" class="download-btn">
                            <i class="bi bi-download"></i> Descargar Credencial
                        </a>
                    </div>
                    """
                    
                    # Guardar mensaje en la sesión y mostrarlo
                    request.session['registro_exitoso_message'] = success_message
                    # Quitar esta línea para evitar duplicado:
                    # messages.success(request, mark_safe(success_message))
                    
                    logging.info("="*50)
                    logging.info("FIN DEL PROCESO DE REGISTRO: EXITOSO")
                    logging.info("="*50)
                    
                    return redirect('login')
                    
                except Exception as e:
                    logging.error(f"Error en el proceso post-registro: {str(e)}")
                    logging.error(traceback.format_exc())
                    messages.warning(request, f"La cuenta se creó pero hubo un problema con la credencial: {str(e)}")
                    return redirect('login')
            else:
                logging.error(f"Error al registrar: {resultado}")
                messages.error(request, str(resultado))
        else:
            logging.error(f"Formulario no válido: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegistroForm()
    
    return render(request, 'usuarios/registro.html', {'form': form})
#----------------------------------------------------------------------------------------------------------------------------------------

def crear_avatar_simple_texto(nickname):
    """Crear avatar simple de texto como respaldo"""
    import base64
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    
    try:
        # Crear imagen simple
        img = Image.new('RGB', (200, 200), (70, 130, 180))
        draw = ImageDraw.Draw(img)
        
        # Dibujar círculo
        draw.ellipse([10, 10, 190, 190], fill=(240, 240, 240))
        
        # Fuente
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Calcular posición
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
        y = 130  # Más abajo
        
        # Contorno negro
        contorno = 3
        for dx in range(-contorno, contorno + 1):
            for dy in range(-contorno, contorno + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), nickname, fill=(0, 0, 0), font=font)
        
        # Texto principal en blanco
        draw.text((x, y), nickname, fill=(255, 255, 255), font=font)  # Blanco
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=95)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except:
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def credencial(request, usuario_id):
    """Vista para visualizar o descargar la credencial de un usuario"""
    import logging
    import os
    from django.http import FileResponse, HttpResponse
    from django.conf import settings
    from usuarios.utils import obtener_o_generar_pdf
    
    try:
        logging.info(f"Solicitud de credencial para usuario_id: {usuario_id}")
        
        # Usar la función unificada para obtener o generar el PDF
        pdf_path = obtener_o_generar_pdf(usuario_id=usuario_id)
        
        if pdf_path and os.path.exists(pdf_path):
            logging.info(f"PDF encontrado/generado: {os.path.getsize(pdf_path)} bytes")
            
            # Decidir si mostrar directamente o descargar
            if request.GET.get('download') == '1':
                response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="credencial_{usuario_id}.pdf"'
                return response
            else:
                # Mostrar en el navegador
                return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
        
        return HttpResponse("No se pudo generar la credencial", status=500)
            
    except Exception as e:
        logging.error(f"Error en la vista credencial: {str(e)}")
        return HttpResponse(f"Error al generar la credencial: {str(e)}", status=500)
    

    
    
def credencial_html(request, usuario_id):
    """Vista para ver la credencial en formato HTML"""
    try:
        # Obtener datos del usuario
        with services.get_mysql_connection() as cursor:
            cursor.execute("""
                SELECT nombre, correo, telefono, avatar, nickname 
                FROM tb_usuarios 
                WHERE id_usuario = %s
            """, [usuario_id])
            usuario = cursor.fetchone()
        
        if not usuario:
            return HttpResponse("Usuario no encontrado", status=404)
        
        nombre, correo, telefono, avatar_data, nickname = usuario
        
        # Importar función para generar QR
        from .utils import generar_qr_code
        
        # Generar código QR
        qr_data = f"ID:{usuario_id},Nickname:{nickname},Correo:{correo}"
        qr_code = generar_qr_code(qr_data)
        
        # Crear contexto para la plantilla
        context = {
            'usuario': {
                'nombre': nombre,
                'correo': correo, 
                'nickname': nickname,
                'id_usuario': usuario_id,
                'avatar': avatar_data
            },
            'qr_code': qr_code,
            'fecha': datetime.now().strftime('%d/%m/%Y'),
            'mostrar_botones_impresion': True
        }
        
        # Renderizar plantilla
        return render(request, 'usuarios/credencial.html', context)
        
    except Exception as e:
        print(f"Error al generar credencial HTML: {str(e)}")
        traceback.print_exc()
        return HttpResponse(f"Error al generar la credencial: {str(e)}", status=500)
    
def dashboard(request):
    """Vista para el dashboard de administración"""
    import logging
    logging.basicConfig(level=logging.INFO)
         
    # Verificar si el usuario está logueado
    if 'usuario_id' not in request.session:
        messages.error(request, "Debe iniciar sesión para acceder a esta página")
        return redirect('login')
         
    # Verificar si el usuario es administrador
    if request.session.get('rol_id') != 2:
        messages.error(request, "No tiene permisos para acceder a esta página")
        return redirect('editor')
         
    # Grupo 7 es nuestro grupo por defecto
    grupo_id = 7
    usuario_id = request.session.get('usuario_id')
         
    try:
        with services.get_mysql_connection() as cursor:
            # Obtener información del usuario actual (incluyendo avatar)
            cursor.execute("""
                SELECT nickname, avatar 
                FROM tb_usuarios 
                WHERE id_usuario = %s
            """, [usuario_id])
            
            usuario_actual = cursor.fetchone()
            user_nickname = usuario_actual[0] if usuario_actual else "Admin"
            user_avatar = None
            
            # Procesar avatar si existe
            if usuario_actual and usuario_actual[1]:
                try:
                    import base64
                    avatar_data = usuario_actual[1]
                    
                    if isinstance(avatar_data, str):
                        user_avatar = avatar_data
                    elif isinstance(avatar_data, bytes):
                        user_avatar = base64.b64encode(avatar_data).decode('utf-8')
                    else:
                        user_avatar = base64.b64encode(str(avatar_data).encode()).decode('utf-8')
                        
                except Exception as e:
                    logging.error(f"Error procesando avatar: {str(e)}")
                    user_avatar = None
            
            # Obtener ingresos del grupo 7 CON AVATARS
            cursor.execute("""
                SELECT i.id_ingreso, u.nickname, i.fecha_ingreso, i.fecha_salida, u.avatar
                FROM tb_ingresos i 
                JOIN tb_usuarios u ON i.id_usuario = u.id_usuario 
                WHERE i.id_grupo = %s 
                ORDER BY i.fecha_ingreso DESC 
                LIMIT 10
            """, [grupo_id])
                         
            ingresos = []
            for row in cursor.fetchall():
                # Procesar avatar del usuario
                avatar_procesado = None
                if row[4]:  # Si hay avatar
                    try:
                        import base64
                        avatar_data = row[4]
                        
                        if isinstance(avatar_data, str):
                            avatar_procesado = avatar_data
                        elif isinstance(avatar_data, bytes):
                            avatar_procesado = base64.b64encode(avatar_data).decode('utf-8')
                        else:
                            avatar_procesado = base64.b64encode(str(avatar_data).encode()).decode('utf-8')
                            
                    except Exception as e:
                        logging.error(f"Error procesando avatar actividad: {str(e)}")
                        avatar_procesado = None
                
                ingresos.append({
                    'id_ingreso': row[0],
                    'nickname': row[1],
                    'fecha_ingreso': row[2],
                    'fecha_salida': row[3],
                    'avatar': avatar_procesado
                })
                         
            # Si no hay ingresos del grupo 7, intentar obtener cualquier ingreso
            if not ingresos:
                cursor.execute("""
                    SELECT i.id_ingreso, u.nickname, i.fecha_ingreso, i.fecha_salida, u.avatar
                    FROM tb_ingresos i 
                    JOIN tb_usuarios u ON i.id_usuario = u.id_usuario 
                    ORDER BY i.fecha_ingreso DESC 
                    LIMIT 10
                """)
                                
                for row in cursor.fetchall():
                    # Procesar avatar del usuario
                    avatar_procesado = None
                    if row[4]:  # Si hay avatar
                        try:
                            import base64
                            avatar_data = row[4]
                            
                            if isinstance(avatar_data, str):
                                avatar_procesado = avatar_data
                            elif isinstance(avatar_data, bytes):
                                avatar_procesado = base64.b64encode(avatar_data).decode('utf-8')
                            else:
                                avatar_procesado = base64.b64encode(str(avatar_data).encode()).decode('utf-8')
                                
                        except Exception as e:
                            logging.error(f"Error procesando avatar actividad: {str(e)}")
                            avatar_procesado = None
                    
                    ingresos.append({
                        'id_ingreso': row[0],
                        'nickname': row[1],
                        'fecha_ingreso': row[2],
                        'fecha_salida': row[3],
                        'avatar': avatar_procesado
                    })
                         
            # Usuarios activos (sin fecha de salida) CON AVATARS
            cursor.execute("""
                SELECT u.nickname, i.id_grupo, i.fecha_ingreso, u.avatar
                FROM tb_ingresos i 
                JOIN tb_usuarios u ON i.id_usuario = u.id_usuario 
                WHERE i.fecha_salida IS NULL
                ORDER BY i.fecha_ingreso DESC
            """)
                         
            usuarios_activos = []
            for row in cursor.fetchall():
                # Procesar avatar del usuario activo
                avatar_procesado = None
                if row[3]:  # Si hay avatar
                    try:
                        import base64
                        avatar_data = row[3]
                        
                        if isinstance(avatar_data, str):
                            avatar_procesado = avatar_data
                        elif isinstance(avatar_data, bytes):
                            avatar_procesado = base64.b64encode(avatar_data).decode('utf-8')
                        else:
                            avatar_procesado = base64.b64encode(str(avatar_data).encode()).decode('utf-8')
                            
                    except Exception as e:
                        logging.error(f"Error procesando avatar usuario activo: {str(e)}")
                        avatar_procesado = None
                
                usuarios_activos.append({
                    'nickname': row[0],
                    'grupo_nombre': f"Grupo {row[1]}",
                    'fecha_ingreso': row[2],
                    'avatar': avatar_procesado
                })
                         
            # Estadísticas simples
            cursor.execute("SELECT COUNT(*) FROM tb_usuarios")
            total_usuarios = cursor.fetchone()[0]
                         
            estadisticas_grupos = [
                {
                    'grupo_nombre': f"Grupo {grupo_id}",
                    'cantidad_usuarios': total_usuarios
                }
            ]
                 
        context = {
            'ingresos': ingresos,
            'usuarios_activos': usuarios_activos,
            'estadisticas_grupos': estadisticas_grupos,
            'mi_grupo': f"Grupo {grupo_id}",
            'user_nickname': user_nickname,
            'user_avatar': user_avatar,
        }
                 
        return render(request, 'usuarios/dashboard.html', context)
             
    except Exception as e:
        logging.error(f"Error en dashboard: {str(e)}")
        messages.error(request, f"Error al cargar el dashboard: {str(e)}")
        return redirect('editor')
    
def editor(request):
    # Vista básica para el editor
    return render(request, 'editor/editor.html')


def test_pdf_generation(request):
    try:
        # Asegurarse de que la carpeta existe
        pdf_dir = os.path.join(os.getcwd(), 'media', 'credenciales')
        os.makedirs(pdf_dir, exist_ok=True)
        print(f"Directorio para PDFs: {pdf_dir}")
        
        # Ruta del archivo PDF
        pdf_path = os.path.join(pdf_dir, 'test.pdf')
        print(f"Ruta del PDF a generar: {pdf_path}")
        
        # Crear un PDF simple
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Añadir texto al PDF
        c.setFont("Helvetica", 16)
        c.drawString(100, height - 100, "Prueba de generación de PDF")
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 150, "Si puedes ver este mensaje, la generación de PDF funciona correctamente.")
        c.drawString(100, height - 180, f"Ruta del archivo: {os.path.abspath(pdf_path)}")
        
        # Guardar el PDF
        c.save()
        print(f"PDF de prueba guardado: {os.path.abspath(pdf_path)}")
        
        # Verificar si el archivo se creó
        if os.path.exists(pdf_path):
            size = os.path.getsize(pdf_path)
            return HttpResponse(f"PDF generado exitosamente en: {os.path.abspath(pdf_path)} ({size} bytes)<br><a href='/media/credenciales/test.pdf' target='_blank'>Ver PDF</a>")
        else:
            return HttpResponse("Error: El archivo no se creó aunque no se generó ninguna excepción.")
    except Exception as e:
        error_trace = traceback.format_exc()
        return HttpResponse(f"Error al generar PDF: {str(e)}<br><pre>{error_trace}</pre>")

def test_email(request):
    try:
        print("Iniciando prueba de envío de correo")
        print(f"Configuración de correo: {settings.EMAIL_HOST}, {settings.EMAIL_PORT}, {settings.EMAIL_HOST_USER}")
        
        # Enviar un correo simple sin adjuntos para probar
        resultado = send_mail(
            'Prueba de correo desde UMG Rover',
            'Este es un mensaje de prueba enviado desde Django.',
            settings.EMAIL_HOST_USER,
            ['ofmers1@gmail.com'],
            fail_silently=False,
        )
        
        # Si resultado es 1, el correo se envió correctamente
        if resultado == 1:
            print("Correo enviado con éxito!")
            return HttpResponse("Correo enviado con éxito! Resultado: " + str(resultado))
        else:
            print(f"El correo no se envió. Resultado: {resultado}")
            return HttpResponse("El correo no se envió. Resultado: " + str(resultado))
    except Exception as e:
        # Mostrar el error detallado
        error_trace = traceback.format_exc()
        print(f"Error al enviar correo: {str(e)}")
        print(error_trace)
        return HttpResponse(f"Error al enviar correo: {str(e)}<br><pre>{error_trace}</pre>")

def debug_view(request):
    """Vista para depurar el sistema"""
    import os
    from django.http import HttpResponse
    from django.conf import settings
    import traceback
    import sys
    import importlib
    
    response = ["<h1>Diagnóstico del Sistema</h1>"]
    response.append("<h2>1. Verificación de Directorios</h2>")
    
    # Verificar directorios
    media_root = os.path.join(os.getcwd(), 'media')
    credenciales_dir = os.path.join(media_root, 'credenciales')
    static_dir = os.path.join(os.getcwd(), 'static')
    img_dir = os.path.join(static_dir, 'img')
    
    # Crear directorios si no existen
    try:
        os.makedirs(media_root, exist_ok=True)
        response.append(f"<p>✅ Directorio media creado/verificado: {media_root}</p>")
    except Exception as e:
        response.append(f"<p>❌ Error al crear directorio media: {str(e)}</p>")
    
    try:
        os.makedirs(credenciales_dir, exist_ok=True)
        response.append(f"<p>✅ Directorio credenciales creado/verificado: {credenciales_dir}</p>")
    except Exception as e:
        response.append(f"<p>❌ Error al crear directorio credenciales: {str(e)}</p>")
    
    try:
        os.makedirs(static_dir, exist_ok=True)
        response.append(f"<p>✅ Directorio static creado/verificado: {static_dir}</p>")
    except Exception as e:
        response.append(f"<p>❌ Error al crear directorio static: {str(e)}</p>")
    
    try:
        os.makedirs(img_dir, exist_ok=True)
        response.append(f"<p>✅ Directorio img creado/verificado: {img_dir}</p>")
    except Exception as e:
        response.append(f"<p>❌ Error al crear directorio img: {str(e)}</p>")
    
    # Verificar permisos
    response.append("<h2>2. Verificación de Permisos</h2>")
    
    try:
        # Intentar crear un archivo de prueba
        test_file_path = os.path.join(credenciales_dir, 'test_permissions.txt')
        with open(test_file_path, 'w') as f:
            f.write('Test de permisos')
        
        # Verificar si se pudo crear
        if os.path.exists(test_file_path):
            response.append(f"<p>✅ Permisos de escritura correctos en {credenciales_dir}</p>")
            # Eliminar archivo de prueba
            os.remove(test_file_path)
        else:
            response.append(f"<p>❌ No se pudo crear archivo de prueba en {credenciales_dir}</p>")
    except Exception as e:
        response.append(f"<p>❌ Error al verificar permisos: {str(e)}</p>")
    
    # Verificar importaciones
    response.append("<h2>3. Verificación de Módulos</h2>")
    
    modules_to_check = [
        ('reportlab.pdfgen', 'canvas'), 
        ('qrcode', 'QRCode'),
        ('PIL', 'Image'),
        ('io', 'BytesIO'),
        ('base64', 'b64encode'),
        ('usuarios.utils', 'generar_credencial_pdf'),
        ('usuarios.messaging', 'enviar_credencial_email')
    ]
    
    for module_name, object_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, object_name):
                response.append(f"<p>✅ Módulo {module_name}.{object_name} importado correctamente</p>")
            else:
                response.append(f"<p>❌ Módulo {module_name} importado pero no contiene {object_name}</p>")
        except ImportError as e:
            response.append(f"<p>❌ Error al importar {module_name}: {str(e)}</p>")
        except Exception as e:
            response.append(f"<p>❌ Error desconocido al verificar {module_name}: {str(e)}</p>")
    
    # Probar generación de PDF con datos de ejemplo
    response.append("<h2>4. Prueba de Generación de PDF</h2>")
    
    try:
        from usuarios.utils import generar_credencial_pdf
        pdf_path = generar_credencial_pdf(
            usuario_id=999999,
            nombre="Usuario de Prueba",
            correo="prueba@example.com",
            telefono="12345678",
            nickname="test_user"
        )
        
        if pdf_path and os.path.exists(pdf_path):
            pdf_size = os.path.getsize(pdf_path)
            response.append(f"<p>✅ PDF generado correctamente en: {pdf_path} ({pdf_size} bytes)</p>")
            response.append(f'<p><a href="/media/credenciales/credencial_999999.pdf" target="_blank">Ver PDF de prueba</a></p>')
        else:
            response.append(f"<p>❌ PDF no generado. Ruta devuelta: {pdf_path}</p>")
    except Exception as e:
        error_trace = traceback.format_exc()
        response.append(f"<p>❌ Error al generar PDF de prueba: {str(e)}</p>")
        response.append(f"<pre>{error_trace}</pre>")
    
    # Mostrar configuración de correo
    response.append("<h2>5. Configuración de Correo</h2>")
    
    email_settings = [
        'EMAIL_BACKEND', 'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USE_TLS', 
        'EMAIL_HOST_USER', 'DEFAULT_FROM_EMAIL'
    ]
    
    for setting_name in email_settings:
        setting_value = getattr(settings, setting_name, 'No configurado')
        if setting_name == 'EMAIL_HOST_PASSWORD':
            # No mostrar la contraseña completa
            if setting_value != 'No configurado':
                setting_value = f"{setting_value[:4]}...{setting_value[-4:] if len(setting_value) > 8 else '****'}"
        response.append(f"<p>{setting_name}: {setting_value}</p>")
    
    # Mostrar información de Python y Django
    response.append("<h2>6. Información del Sistema</h2>")
    
    response.append(f"<p>Python: {sys.version}</p>")
    response.append(f"<p>Django: {settings.INSTALLED_APPS}</p>")
    response.append(f"<p>Directorio de trabajo: {os.getcwd()}</p>")
    response.append(f"<p>STATIC_URL: {settings.STATIC_URL}</p>")
    response.append(f"<p>MEDIA_URL: {settings.MEDIA_URL}</p>")
    
    return HttpResponse("<br>".join(response))
# Agrega esta función al final de tu views.py

def get_user_context(request):
    """Context processor para obtener datos del usuario en todos los templates"""
    if 'usuario_id' not in request.session:
        return {}
    
    try:
        from usuarios import services
        
        usuario_id = request.session.get('usuario_id')
        
        with services.get_mysql_connection() as cursor:
            # Usar la estructura exacta de tu base de datos
            cursor.execute("""
                SELECT nickname, avatar 
                FROM tb_usuarios 
                WHERE id_usuario = %s
            """, [usuario_id])
            
            usuario = cursor.fetchone()
            
            if usuario:
                # Tu configuración devuelve tuplas, así que accedemos por índice
                nickname = usuario[0]
                avatar = usuario[1] if usuario[1] else None
                
                return {
                    'user_nickname': nickname,
                    'user_avatar': avatar
                }
    except Exception as e:
        print(f"Error obteniendo contexto de usuario: {e}")
        import traceback
        traceback.print_exc()
    
    return {}
# Agregar estas funciones AL FINAL de tu archivo views.py

def test_registro_completo(request):
    """Vista para probar el proceso completo de registro"""
    import logging
    from usuarios.utils import obtener_o_generar_pdf
    from usuarios.messaging import enviar_credencial_email
    
    logging.basicConfig(level=logging.DEBUG)
    
    response_text = ["<h1>Test del Proceso de Registro</h1>"]
    
    # Datos de prueba
    usuario_id = 999
    nombre = "Test User"
    correo = "test@example.com"
    telefono = "12345678"
    nickname = "testuser"
    avatar_data = ""
    
    try:
        # Test 1: Generar avatar
        response_text.append("<h2>1. Generando avatar predeterminado</h2>")
        from usuarios.utils import generar_avatar_predeterminado
        avatar_data = generar_avatar_predeterminado(nickname)
        response_text.append(f"<p>✅ Avatar generado: {len(avatar_data)} caracteres</p>")
    except Exception as e:
        response_text.append(f"<p>❌ Error generando avatar: {str(e)}</p>")
        response_text.append(f"<pre>{traceback.format_exc()}</pre>")
    
    try:
        # Test 2: Generar PDF
        response_text.append("<h2>2. Generando PDF</h2>")
        pdf_path = obtener_o_generar_pdf(
            usuario_id=usuario_id,
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            nickname=nickname,
            avatar_data=avatar_data
        )
        
        if pdf_path and os.path.exists(pdf_path):
            response_text.append(f"<p>✅ PDF generado: {pdf_path}</p>")
            response_text.append(f"<p>Tamaño: {os.path.getsize(pdf_path)} bytes</p>")
        else:
            response_text.append(f"<p>❌ PDF no generado o no existe</p>")
    except Exception as e:
        response_text.append(f"<p>❌ Error generando PDF: {str(e)}</p>")
        response_text.append(f"<pre>{traceback.format_exc()}</pre>")
    
    try:
        # Test 3: Enviar correo
        response_text.append("<h2>3. Enviando correo</h2>")
        if pdf_path and os.path.exists(pdf_path):
            resultado = enviar_credencial_email(
                nombre=nombre,
                correo=correo,
                pdf_path=pdf_path,
                nickname=nickname,
                usuario_id=usuario_id
            )
            
            if resultado:
                response_text.append(f"<p>✅ Correo enviado correctamente</p>")
            else:
                response_text.append(f"<p>❌ Error al enviar correo</p>")
        else:
            response_text.append(f"<p>❌ No se puede enviar correo sin PDF</p>")
    except Exception as e:
        response_text.append(f"<p>❌ Error enviando correo: {str(e)}</p>")
        response_text.append(f"<pre>{traceback.format_exc()}</pre>")
    
    return HttpResponse("<br>".join(response_text))


def test_stored_procedure(request):
    """Vista para probar el procedimiento almacenado de registro"""
    import random
    import string
    
    response_text = ["<h1>Test del Procedimiento Almacenado</h1>"]
    
    # Generar datos únicos para evitar duplicados
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    
    nombre = f"Test User {random_suffix}"
    nickname = f"test_{random_suffix}"
    password = "password123"
    avatar_data = "test_avatar_data"
    correo = f"test_{random_suffix}@example.com"
    telefono = "12345678"
    
    response_text.append(f"<h2>Datos de prueba:</h2>")
    response_text.append(f"<p>Nombre: {nombre}</p>")
    response_text.append(f"<p>Nickname: {nickname}</p>")
    response_text.append(f"<p>Correo: {correo}</p>")
    response_text.append(f"<p>Teléfono: {telefono}</p>")
    
    try:
        # Probar el procedimiento almacenado directamente
        response_text.append("<h2>Probando procedimiento almacenado...</h2>")
        
        with services.get_mysql_connection() as cursor:
            # Llamar al procedimiento almacenado
            cursor.callproc('insertar_usuario', [
                nombre, nickname, password, avatar_data, correo, telefono, ''
            ])
            
            # Obtener el resultado
            cursor.execute("SELECT @_insertar_usuario_6")
            result = cursor.fetchone()
            
            if result:
                response_text.append(f"<p>✅ Resultado: {result[0]}</p>")
            else:
                response_text.append("<p>❌ No se obtuvo resultado del procedimiento</p>")
            
            # Verificar si el usuario se creó
            cursor.execute("SELECT id_usuario, nickname FROM tb_usuarios WHERE nickname = %s", [nickname])
            usuario = cursor.fetchone()
            
            if usuario:
                response_text.append(f"<p>✅ Usuario creado con ID: {usuario['id_usuario']}</p>")
            else:
                response_text.append("<p>❌ Usuario no encontrado después de la inserción</p>")
                
    except Exception as e:
        response_text.append(f"<p>❌ Error: {str(e)}</p>")
        response_text.append(f"<pre>{traceback.format_exc()}</pre>")
    
    return HttpResponse("<br>".join(response_text))


# Variable global para controlar ejecución
_execution_control = {
    "active": False,
    "should_stop": False,
    "lock": threading.Lock()
}
#------------------------------------------------------------------------Funcion de Stop-------------------------------------------------
# views.py - VERSIÓN FINAL CORREGIDA

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import time
import threading
import requests

logger = logging.getLogger(__name__)

# Variables globales ÚNICAS
_execution_thread = None
_stop_signal = threading.Event()

@csrf_exempt
def emergency_stop_view(request):
    """
    PARADA DE EMERGENCIA MEJORADA
    - Activa la señal de parada inmediatamente
    - Envía comandos STOP directos al rover
    - Permite que el thread termine el comando actual
    """
    global _execution_thread, _stop_signal
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            rover_ip = data.get('rover_ip', '192.168.1.98')

            print(f"🚨 PARADA DE EMERGENCIA para IP: {rover_ip}")

            # PASO 1: ACTIVAR SEÑAL DE PARADA INMEDIATAMENTE
            _stop_signal.set()
            print("💀 SEÑAL DE PARADA ACTIVADA")

            # PASO 2: ENVIAR STOP INMEDIATO AL ROVER (solo 1 vez, rápido)
            try:
                # Usar timeout muy corto para no bloquear
                response = requests.get(f"http://{rover_ip}/?State=S", timeout=0.3)
                print(f"📡 STOP directo enviado: HTTP {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error al enviar STOP directo: {e}")

            # PASO 3: NO ESPERAR AL THREAD - dejar que termine naturalmente
            thread_status = "No hay thread activo"
            if _execution_thread and _execution_thread.is_alive():
                thread_status = "Thread activo - se detendrá después del comando actual"
                print("⚠️ Thread ejecutándose - terminará el comando actual y se detendrá")
            else:
                print("✅ No hay thread activo o ya terminó")

            # PASO 4: RESPONDER RÁPIDAMENTE AL CLIENTE
            response_data = {
                "success": True,
                "message": "Parada de emergencia activada",
                "rover_ip": rover_ip,
                "thread_status": thread_status,
                "stop_signal_active": _stop_signal.is_set()
            }

            # PASO 5: Limpiar en un thread separado para no bloquear
            def cleanup_after_stop(ip_rover):
                global _execution_thread, _stop_signal  # Declarar global AL PRINCIPIO
                
                try:
                    if _execution_thread and _execution_thread.is_alive():
                        # Esperar máximo 5 segundos
                        _execution_thread.join(timeout=5.0)
                        
                        if _execution_thread.is_alive():
                            print("⚠️ Thread no terminó en 5 segundos")
                        else:
                            print("✅ Thread terminado correctamente")
                    
                    # Enviar un STOP final de confirmación
                    time.sleep(0.5)
                    try:
                        requests.get(f"http://{ip_rover}/?State=S", timeout=0.3)
                        print("✅ STOP de confirmación enviado")
                    except:
                        pass
                    
                except Exception as e:
                    print(f"Error en cleanup: {e}")
                finally:
                    # Limpiar variables
                    _execution_thread = None
                    _stop_signal.clear()
                    print("✅ Sistema reseteado")

            # Ejecutar limpieza en background
            import threading
            cleanup_thread = threading.Thread(
                target=cleanup_after_stop, 
                args=(rover_ip,),  # Pasar rover_ip como argumento
                daemon=True
            )
            cleanup_thread.start()

            return JsonResponse(response_data)

        except Exception as e:
            print(f"❌ Error en emergency_stop: {str(e)}")
            # En caso de error, asegurar reset
            _stop_signal.clear()
            _execution_thread = None
            
            return JsonResponse({
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            })

    return JsonResponse({
        "success": False,
        "message": "Método no permitido"
    })

def _execute_commands_in_thread(commands, rover_ip):
    """
    Ejecuta comandos respetando sus duraciones pero verificando stop frecuentemente
    """
    global _stop_signal
    
    try:
        from .rover_communication import RoverCommunicator
        rover_comm = RoverCommunicator(rover_ip)
        
        total_commands = len(commands)
        print(f"🚀 Thread ejecutando {total_commands} comandos")
        
        for i, cmd_data in enumerate(commands):
            # Verificar STOP antes de cada comando
            if _stop_signal.is_set():
                print(f"💀 STOP detectado en comando {i+1}/{total_commands}")
                rover_comm.send_command('S', 0)
                print(f"🗑️ Thread terminado. Descartados {total_commands - i} comandos")
                return
            
            try:
                cmd, duration = cmd_data
                
                print(f"📡 Ejecutando comando {i+1}/{total_commands}: {cmd} por {duration}ms")
                
                # Enviar comando
                result = rover_comm.send_command(cmd, duration)
                
                # IMPORTANTE: Esperar la duración del comando
                # Pero dividir en chunks pequeños para verificar stop signal
                elapsed = 0
                check_interval = 50  # Verificar cada 50ms
                
                while elapsed < duration:
                    # Si hay señal de stop, salir inmediatamente
                    if _stop_signal.is_set():
                        print(f"💀 STOP detectado durante comando {i+1}")
                        rover_comm.send_command('S', 0)
                        return
                    
                    # Esperar el mínimo entre check_interval y el tiempo restante
                    wait_time = min(check_interval, duration - elapsed)
                    time.sleep(wait_time / 1000.0)  # Convertir a segundos
                    elapsed += wait_time
                
                # Delay mínimo entre comandos (5ms)
                time.sleep(0.005)
                
            except Exception as cmd_error:
                print(f"❌ Error en comando {i+1}: {str(cmd_error)}")
                continue
        
        print(f"✅ Thread completado: {total_commands} comandos ejecutados")
        
    except Exception as e:
        print(f"❌ Error crítico en thread: {str(e)}")
        if _stop_signal.is_set():
            try:
                from .rover_communication import RoverCommunicator
                rover_comm = RoverCommunicator(rover_ip)
                rover_comm.send_command('S', 0)
            except:
                pass
# Reemplaza execute_view en views.py con esta versión

@csrf_exempt 
def execute_view(request):
    """
    Ejecución ASÍNCRONA - No espera que termine
    """
    global _execution_thread, _stop_signal

    if request.method == 'POST':
        try:
            if _execution_thread and _execution_thread.is_alive():
                return JsonResponse({
                    "success": False,
                    "message": "Ya hay una ejecución en progreso. Use STOP para cancelar.",
                    "error": "Thread activo"
                })

            data = json.loads(request.body)
            code = data.get('code', '')
            rover_ip = data.get('rover_ip', '192.168.1.98')

            print(f"🚀 Iniciando ejecución para rover {rover_ip}")

            from .umg_transpiler import UMGTranspiler
            transpiler = UMGTranspiler()

            # Compilar
            commands = transpiler.parse(code)
            if isinstance(commands, dict) and "error" in commands:
                return JsonResponse(commands)

            print(f"📋 {len(commands)} comandos compilados")

            # LIMPIAR SEÑAL DE PARADA
            _stop_signal.clear()

            # CREAR Y LANZAR THREAD
            _execution_thread = threading.Thread(
                target=_execute_commands_in_thread,
                args=(commands, rover_ip),
                daemon=True,
                name="RoverExecutionThread"
            )
            
            _execution_thread.start()
            print("🚀 Thread lanzado")

            # RESPONDER INMEDIATAMENTE - NO ESPERAR
            return JsonResponse({
                "success": True,
                "message": "Ejecución iniciada en segundo plano",
                "commands_total": len(commands),
                "status": "running"
            })

        except Exception as e:
            print(f"❌ Error en execute_view: {str(e)}")
            _execution_thread = None
            _stop_signal.clear()
            
            return JsonResponse({
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            })

    return JsonResponse({
        "success": False,
        "message": "Método no permitido"
    })

@csrf_exempt
def compile_view(request):
    """
    Vista para compilar código UMG++
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            
            if not code:
                return JsonResponse({
                    "success": False,
                    "message": "No se proporcionó código para compilar"
                })
            
            from .umg_transpiler import UMGTranspiler
            transpiler = UMGTranspiler()
            
            commands = transpiler.parse(code)
            
            if isinstance(commands, dict) and "error" in commands:
                return JsonResponse({
                    "success": False,
                    "message": commands["error"]
                })
            
            return JsonResponse({
                "success": True,
                "message": f"Código compilado exitosamente. {len(commands)} comandos generados.",
                "commands": commands
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Error al compilar: {str(e)}"
            })
    
    return JsonResponse({
        "success": False,
        "message": "Método no permitido"
    })

@csrf_exempt
def simulate_view(request):
    """
    Vista para simular ejecución
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            
            from .umg_transpiler import UMGTranspiler
            transpiler = UMGTranspiler()
            
            commands = transpiler.parse(code)
            
            if isinstance(commands, dict) and "error" in commands:
                return JsonResponse({
                    "success": False,
                    "message": commands["error"]
                })
            
            # Crear traza de simulación
            simulation_trace = []
            for i, cmd_data in enumerate(commands):
                if isinstance(cmd_data, tuple):
                    cmd, duration = cmd_data
                    simulation_trace.append({
                        "step": i + 1,
                        "command": cmd,
                        "duration": duration,
                        "description": f"Comando {cmd} por {duration}ms"
                    })
            
            return JsonResponse({
                "success": True,
                "message": "Simulación completada",
                "simulation_trace": simulation_trace
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Error en simulación: {str(e)}"
            })
    
    return JsonResponse({
        "success": False,
        "message": "Método no permitido"
    })

@csrf_exempt
def status_view(request):
    """
    Vista para verificar estado del sistema
    """
    if request.method == 'GET':
        global _execution_thread, _stop_signal
        
        is_running = _execution_thread is not None and _execution_thread.is_alive()
        stop_requested = _stop_signal.is_set()
        
        return JsonResponse({
            "success": True,
            "execution_active": is_running,
            "stop_requested": stop_requested,
            "system_ready": not is_running and not stop_requested
        })
    
    return JsonResponse({
        "success": False,
        "message": "Método no permitido"
    })
# Agrega esta vista en views.py si no la tienes:

def execution_status_view(request):
    """
    Vista para verificar el estado de la ejecución actual
    """
    global _execution_thread, _stop_signal
    
    is_running = _execution_thread is not None and _execution_thread.is_alive()
    
    return JsonResponse({
        "success": True,
        "is_running": is_running,
        "stop_requested": _stop_signal.is_set() if _stop_signal else False
    })

# Y agrega en urls.py:
# 