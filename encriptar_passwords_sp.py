import os
import django
import bcrypt

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'umg_rover.settings')
django.setup()

from django.db import connections

def listar_usuarios():
    """
    Lista todos los usuarios en la base de datos
    """
    conn = connections['mysql']
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id_usuario, nombre, nickname, password, id_rol
            FROM tb_usuarios
            ORDER BY id_usuario
        """)
        usuarios = cursor.fetchall()
        
        if not usuarios:
            print("No hay usuarios en la base de datos.")
            return []
        
        print("\n=== LISTA DE USUARIOS ===")
        print(f"{'ID':<5} {'Nickname':<15} {'Nombre':<20} {'Contraseña Encriptada':<15} {'Rol':<5}")
        print("-" * 80)
        
        resultado = []
        for usuario in usuarios:
            id_usuario, nombre, nickname, password, id_rol = usuario
            encriptada = len(password) > 50 and (password.startswith('$2a$') or password.startswith('$2b$'))
            estado = "Sí" if encriptada else "No"
            rol_texto = "Admin" if id_rol == 2 else "User"
            
            print(f"{id_usuario:<5} {nickname:<15} {nombre:<20} {estado:<15} {rol_texto:<5}")
            resultado.append((id_usuario, nickname, nombre, password, id_rol, encriptada))
        
        return resultado

def encriptar_usuario(nickname):
    """
    Encripta la contraseña de un usuario específico
    """
    conn = connections['mysql']
    with conn.cursor() as cursor:
        # Obtener los datos del usuario
        cursor.execute("""
            SELECT id_usuario, nombre, nickname, correo, telefono, id_rol, password, avatar
            FROM tb_usuarios
            WHERE nickname = %s
        """, [nickname])
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"Error: No se encontró el usuario {nickname}")
            return False
        
        id_usuario, nombre, nickname, correo, telefono, id_rol, password, avatar = usuario
        
        # Verificar si la contraseña ya está encriptada
        if password and len(password) > 50 and (password.startswith('$2a$') or password.startswith('$2b$')):
            print(f"La contraseña del usuario {nickname} ya está encriptada.")
            return True
        
        try:
            # Encriptar la contraseña
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            hashed_str = hashed.decode('utf-8')
            
            print(f"Contraseña original: {password}")
            print(f"Contraseña encriptada: {hashed_str}")
            
            # Preguntar si desea proceder
            confirmar = input("\n¿Estás seguro de encriptar esta contraseña? (s/n): ")
            if confirmar.lower() != 's':
                print("Operación cancelada.")
                return False
            
            # Actualizar usando el procedimiento almacenado
            resultado = None
            with conn.cursor() as proc_cursor:
                resultado = proc_cursor.callproc('modificar_usuario', [
                    nickname, nombre, nickname, hashed_str, avatar or '', correo, telefono, id_rol, ''])
            
            # Verificar resultado
            result_msg = resultado[-1] if resultado else "Error desconocido"
            if "exitosamente" in str(result_msg).lower():
                print(f"Contraseña del usuario {nickname} encriptada exitosamente.")
                return True
            else:
                print(f"Error al encriptar contraseña: {result_msg}")
                return False
        except Exception as e:
            print(f"Error al encriptar contraseña: {str(e)}")
            return False

if __name__ == "__main__":
    print("=== ENCRIPTACIÓN DE CONTRASEÑAS ===")
    
    # Listar usuarios
    usuarios = listar_usuarios()
    
    if usuarios:
        print("\nOpciones:")
        print("1. Encriptar contraseña de un usuario específico")
        print("2. Salir")
        
        opcion = input("\nSelecciona una opción (1/2): ")
        
        if opcion == "1":
            nickname = input("\nIngresa el nickname del usuario cuya contraseña quieres encriptar: ")
            encriptar_usuario(nickname)
        else:
            print("Operación cancelada.")
    
    input("\nPresiona Enter para salir...")