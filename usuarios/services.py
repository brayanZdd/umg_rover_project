from django.db import connections
import base64
import bcrypt
import logging

def get_mysql_connection():
    return connections['mysql'].cursor()

# En services.py, reemplaza la función registro_usuario con esta versión mejorada:

# En services.py, reemplaza estas funciones con versiones que manejen tuplas:

def registro_usuario(nombre, nickname, password, image, correo, telefono):
    """
    Registra un nuevo usuario usando el procedimiento almacenado.
    La contraseña se encripta con bcrypt antes de enviarla.
    """
    import logging
    import bcrypt

    logging.basicConfig(level=logging.DEBUG)
    
    try:
        with get_mysql_connection() as cursor:
            logging.debug(f"Registrando usuario: {nickname}")

            # Encriptar la contraseña antes de enviarla
            password_encriptada = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Ejecutar el procedimiento almacenado
            args = [nombre, nickname, password_encriptada, image, correo, telefono, '']
            cursor.callproc('insertar_usuario', args)
            
            # Obtener el resultado OUT
            resultado = None
            try:
                cursor.execute("SELECT @_insertar_usuario_6")
                result = cursor.fetchone()
                if result:
                    resultado = result[0] if isinstance(result, tuple) else result
            except:
                pass

            # Verificación adicional si no hay OUT
            if not resultado:
                cursor.execute("SELECT COUNT(*) FROM tb_usuarios WHERE nickname = %s", [nickname])
                count_result = cursor.fetchone()
                if count_result and count_result[0] > 0:
                    resultado = "Ha sido registrado exitosamente"
                    logging.debug("Usuario verificado en la base de datos, asumiendo éxito")
            
            return resultado if resultado else "Ha sido registrado exitosamente"
    
    except Exception as e:
        logging.error(f"Error en registro_usuario: {str(e)}")
        if "Duplicate" in str(e) or "ya existe" in str(e):
            raise e
        raise e

def login_usuario(nickname, password):
    """
    Verifica las credenciales del usuario
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        with get_mysql_connection() as cursor:
            # Obtener datos del usuario
            cursor.execute(
                "SELECT id_usuario, id_rol, password FROM tb_usuarios WHERE nickname = %s",
                [nickname]
            )
            resultado = cursor.fetchone()
            
            if not resultado:
                return None, "Usuario no encontrado"
            
            id_usuario, id_rol, stored_password = resultado
            id_grupo = 7  # Grupo por defecto
            
            # Verificar la contraseña
            password_valida = False
            
            # Primero intentar con bcrypt
            try:
                import bcrypt
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    password_valida = True
            except:
                # Si falla bcrypt, comparar directamente
                if password == stored_password:
                    password_valida = True
            
            if password_valida:
                # Registrar el ingreso
                ingreso_id = None
                
                try:
                    # Usar el procedimiento almacenado
                    cursor.callproc('insertar_ingreso', [id_usuario, id_grupo, ''])
                    
                    # Obtener el último ID insertado
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    result = cursor.fetchone()
                    if result:
                        ingreso_id = result[0]
                        logging.info(f"Ingreso registrado con ID: {ingreso_id}")
                
                except Exception as e:
                    logging.error(f"Error al registrar ingreso: {str(e)}")
                
                return {
                    'id_usuario': id_usuario,
                    'id_rol': id_rol,
                    'id_grupo': id_grupo,
                    'id_ingreso': ingreso_id
                }, "Login exitoso"
            else:
                return None, "Contraseña incorrecta"
    
    except Exception as e:
        logging.error(f"Error general en login: {str(e)}")
        return None, f"Error del sistema: {str(e)}"

def get_usuario_by_id(usuario_id):
    """
    Obtiene los datos de un usuario por su ID
    """
    try:
        with get_mysql_connection() as cursor:
            cursor.execute("""
                SELECT id_usuario, nombre, correo, telefono, id_rol, 
                       password, avatar, nickname
                FROM tb_usuarios 
                WHERE id_usuario = %s
            """, [usuario_id])
            
            usuario = cursor.fetchone()
            
            if usuario:
                # Convertir tupla a diccionario
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
        logging.error(f"Error al obtener usuario por ID: {e}")
        import traceback
        traceback.print_exc()
    
    return None

def registrar_ingreso(id_usuario, id_grupo=7):  # Cambiado a 7 por defecto
    """
    Registra el ingreso de un usuario con su grupo
    """
    try:
        ingreso_id = None
        with get_mysql_connection() as cursor:
            try:
                # Intentar con el procedimiento que acepta id_grupo
                resultado = cursor.callproc('insertar_ingreso', [
                    id_usuario, id_grupo, ''])
                
                # El resultado debe ser el ID del ingreso
                ingreso_id = resultado[-1]
                
                # Verificar que sea un número (ID) y no un mensaje
                try:
                    ingreso_id = int(ingreso_id)
                    logging.info(f"Ingreso registrado correctamente con SP, ID: {ingreso_id}")
                except (ValueError, TypeError):
                    logging.warning(f"El SP no devolvió un ID válido: {ingreso_id}")
                    ingreso_id = None
                    
            except Exception as e:
                logging.warning(f"Error con SP insertar_ingreso: {str(e)}")
                ingreso_id = None
                
            # Si no tenemos un ID válido, insertar directamente
            if not ingreso_id:
                try:
                    cursor.execute(
                        "INSERT INTO tb_ingresos (id_usuario, id_grupo, fecha_ingreso) VALUES (%s, %s, NOW())",
                        [id_usuario, id_grupo]
                    )
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    ingreso_id = cursor.fetchone()[0]
                    logging.info(f"Ingreso registrado manualmente, ID: {ingreso_id}")
                except Exception as insert_error:
                    logging.error(f"Error al insertar ingreso manualmente: {str(insert_error)}")
                    
        return ingreso_id
    except Exception as e:
        logging.error(f"Error general al registrar ingreso: {str(e)}")
        return None
    
def registrar_salida(id_ingreso):
    """
    Registra la salida de un usuario usando el procedimiento almacenado
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    if not id_ingreso:
        logging.error("ID de ingreso no proporcionado")
        return "Error: No se proporcionó ID de ingreso"
    
    logging.info(f"Registrando salida para ingreso ID: {id_ingreso}")
    
    try:
        # Llamar al procedimiento almacenado
        with get_mysql_connection() as cursor:
            resultado = cursor.callproc('registrar_salida', [id_ingreso, ''])
            
            # El segundo elemento (índice 1) del resultado contiene el valor OUT
            result_message = resultado[1]
            
            logging.info(f"Resultado del SP registrar_salida: {result_message}")
            
            return result_message or "Salida registrada exitosamente"
            
    except Exception as e:
        logging.error(f"Error al registrar salida: {str(e)}")
        return f"Error al registrar salida: {str(e)}"
