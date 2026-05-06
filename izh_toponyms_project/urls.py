from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Админка Django (с изменённым URL для безопасности)
    path('izhevsk-admin/', admin.site.urls),

    # Страницы авторизации для администратора
    path('admin-login/', auth_views.LoginView.as_view(template_name='toponyms/admin_login.html'), name='admin_login'),
    path('admin-logout/', auth_views.LogoutView.as_view(next_page='/'), name='admin_logout'),

    # Твои существующие маршруты (подключаются из приложения toponyms)
    path('', include('toponyms.urls')),
]