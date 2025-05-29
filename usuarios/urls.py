# urls.py - Archivo completo corregido

from django.contrib import admin
from django.urls import path, include  # Asegúrate de importar include si lo necesitas
from django.conf import settings
from django.conf.urls.static import static
from usuarios import views
from django.urls import path
from . import views

urlpatterns = [
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Autenticación
    path('', views.login, name='login'),
    path('registro/', views.registro, name='registro'),
    path('logout/', views.logout, name='logout'),
    path('registro-exitoso/', views.registro_exitoso, name='registro_exitoso'),
    
    # Credenciales
    path('credencial/<int:usuario_id>/', views.credencial, name='credencial'),
    path('credencial/<int:usuario_id>/html/', views.credencial_html, name='credencial_html'),
    
    # Dashboard y editor
    path('dashboard/', views.dashboard, name='dashboard'),
    path('editor/', views.editor, name='editor'),
    path('test_rover/', views.test_rover_view, name='test_rover'),

    # APIs del compilador
    path('api/compile/', views.compile_code, name='compile_code'),
    path('api/execute/', views.execute_code, name='execute_code'),
    path('api/simulate/', views.simulate_code, name='simulate_code'),
    path('api/test-rover-connection/', views.test_rover_connection, name='test_rover_connection'),
    path('api/emergency_stop/', views.emergency_stop_view, name='emergency_stop'),
    path('api/execute/', views.execute_view, name='execute'),
    path('api/simulate/', views.simulate_view, name='simulate'),
    path('api/status/', views.status_view, name='api_status'),
    
    # Rutas de prueba y debug
    path('debug/', views.debug_view, name='debug'),
    path('debug-rover/', views.debug_rover, name='debug_rover'),
    path('test-pdf/', views.test_pdf_generation, name='test_pdf'),
    path('test-email/', views.test_email, name='test_email'),
    path('test-rover/', views.test_rover_view, name='test_rover'),
    path('direct-control/', views.direct_control, name='direct_control'),
    path('session-info/', views.session_info, name='session_info'),
    path('test-registro-completo/', views.test_registro_completo, name='test_registro_completo'),
    path('test-sp/', views.test_stored_procedure, name='test_stored_procedure'),
]

# Agregar archivos estáticos y media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)