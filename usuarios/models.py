from django.db import models

class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    
    class Meta:
        managed = False  # Django no intentará crear/modificar esta tabla
        db_table = 'tb_roles'

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    correo = models.CharField(max_length=100)
    telefono = models.CharField(max_length=100)
    id_rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    password = models.TextField()
    avatar = models.TextField()
    nickname = models.CharField(max_length=45)
    id_grupo = models.IntegerField(default=7)  # Grupo 7 por defecto (tu grupo)
    
    class Meta:
        managed = False  # Django no intentará crear/modificar esta tabla
        db_table = 'tb_usuarios'

class Ingreso(models.Model):
    id_ingreso = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    id_grupo = models.IntegerField(default=1)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        managed = False  # Django no intentará crear/modificar esta tabla
        db_table = 'tb_ingresos'

        # Agregar este modelo a tu archivo usuarios/models.py

class Coreografia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    codigo = models.TextField()
    audio_file = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'coreografias'
        ordering = ['nombre']
        verbose_name = 'Coreografía'
        verbose_name_plural = 'Coreografías'
    
    def __str__(self):
        return self.nombre