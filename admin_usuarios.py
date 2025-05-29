import os
import django
import bcrypt

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'umg_rover.settings')
django.setup()

from django.db import connections

def crear_admin_sp(nombre, nickname, password, correo, telefono, avatar_data=""):
    """
    Crea un nuevo usuario administrador usando el procedimiento almacenado
    """
    print(f"Creando nuevo administrador: {nickname}")
    
    # Encriptar la contraseña
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hashed_password_str = hashed_password.decode('utf-8')
    
    # Llamar al procedimiento almacenado
    resultado = None
    conn = connections['mysql']
    with conn.cursor() as cursor:
        resultado = cursor.callproc('insertar_admin', [
            nombre, nickname, hashed_password_str, avatar_data, correo, telefono, ''])
        # El último parámetro es el OUT parameter que contendrá el resultado
    
    final_result = resultado[-1] if resultado else "Error desconocido"
    print(f"Resultado: {final_result}")
    return "exitosamente" in str(final_result).lower()


def modificar_usuario_sp(nickname_original, nombre, nickname, password, correo, telefono, id_rol, avatar_data=""):
    """
    Modifica un usuario existente usando el procedimiento almacenado, conservando el avatar si no se pasa uno nuevo.
    """
    print(f"Modificando usuario: {nickname_original}")
    
    conn = connections['mysql']

    # Obtener la contraseña y avatar actuales si no se proporcionan nuevos
    with conn.cursor() as cursor:
        cursor.execute("SELECT password, avatar FROM tb_usuarios WHERE nickname = %s", [nickname_original])
        result = cursor.fetchone()
        if not result:
            print(f"Error: No se encontró el usuario {nickname_original}")
            return False
        current_password, current_avatar = result

    # Encriptar la nueva contraseña si se proporciona
    if password:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    else:
        hashed_password = current_password

    # Conservar el avatar actual si no se pasa uno nuevo
    if avatar_data in [None, ""]:
        avatar_data = current_avatar

    # Llamar al procedimiento almacenado
    resultado = None
    with conn.cursor() as cursor:
        resultado = cursor.callproc('modificar_usuario', [
            nickname_original, nombre, nickname, hashed_password, avatar_data, correo, telefono, id_rol, ''])

    final_result = resultado[-1] if resultado else "Error desconocido"
    print(f"Resultado: {final_result}")
    return "exitosamente" in str(final_result).lower()




def buscar_usuario(nickname):
    """
    Busca un usuario por su nickname y muestra sus datos
    """
    conn = connections['mysql']
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id_usuario, nombre, correo, telefono, id_rol, nickname
            FROM tb_usuarios
            WHERE nickname = %s
        """, [nickname])
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"No se encontró ningún usuario con el nickname '{nickname}'")
            return None
        
        id_usuario, nombre, correo, telefono, id_rol, nickname = usuario
        
        rol_texto = "Administrador" if id_rol == 2 else "Usuario Regular"
        
        print("-" * 50)
        print(f"ID: {id_usuario}")
        print(f"Nombre: {nombre}")
        print(f"Nickname: {nickname}")
        print(f"Correo: {correo}")
        print(f"Teléfono: {telefono}")
        print(f"Rol: {rol_texto} (ID: {id_rol})")
        print("-" * 50)
        
        return usuario

def listar_usuarios():
    """
    Lista todos los usuarios en la base de datos
    """
    conn = connections['mysql']
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id_usuario, nombre, nickname, correo, id_rol
            FROM tb_usuarios
            ORDER BY id_usuario
        """)
        usuarios = cursor.fetchall()
        
        if not usuarios:
            print("No hay usuarios en la base de datos.")
            return
        
        print("\n=== LISTA DE USUARIOS ===")
        print(f"{'ID':<5} {'Nickname':<15} {'Nombre':<20} {'Correo':<25} {'Rol':<5}")
        print("-" * 70)
        
        for usuario in usuarios:
            id_usuario, nombre, nickname, correo, id_rol = usuario
            rol_texto = "Admin" if id_rol == 2 else "User"
            print(f"{id_usuario:<5} {nickname:<15} {nombre:<20} {correo:<25} {rol_texto:<5}")

if __name__ == "__main__":
    print("\n=== HERRAMIENTA DE ADMINISTRACIÓN DE USUARIOS ===")
    print("1. Crear nuevo administrador")
    print("2. Convertir usuario existente en administrador")
    print("3. Buscar usuario")
    print("4. Listar todos los usuarios")
    
    opcion = input("\nSelecciona una opción (1/2/3/4): ")
    
    if opcion == "1":
        nombre = input("Nombre completo: ")
        nickname = input("Nickname: ")
        correo = input("Correo electrónico: ")
        telefono = input("Teléfono: ")
        password = input("Contraseña: ")
        
        crear_admin_sp(nombre, nickname, password, correo, telefono)
    
    elif opcion == "2":
        nickname = input("Ingresa el nickname del usuario que quieres convertir en administrador: ")
        usuario = buscar_usuario(nickname)
        
        # CORRECCIÓN: Esta línea debe estar dentro del elif, no fuera
        if usuario:
            id_usuario, nombre, correo, telefono, id_rol, nickname = usuario
            
            if id_rol == 2:
                print(f"El usuario '{nickname}' ya es administrador.")
            else:
                confirmar = input(f"¿Estás seguro de convertir a '{nickname}' en administrador? (s/n): ")
                
                if confirmar.lower() == 's':
                    # Modificar el rol a 2 (administrador) - CAMBIO: Pasar None para preservar avatar
                    modificar_usuario_sp(nickname, nombre, nickname, "", correo, telefono, 2, None)

    
    elif opcion == "3":
        nickname = input("Ingresa el nickname del usuario que quieres buscar: ")
        buscar_usuario(nickname)
    
    elif opcion == "4":
        listar_usuarios()
    
    else:
        print("Opción no válida.")
    
    input("\nPresiona Enter para salir...")