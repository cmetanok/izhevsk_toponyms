from django.urls import path
from . import views

urlpatterns = [
    path('map/', views.map_view, name='map'),
    path('list/', views.toponym_list, name='list'),
    path('stats/', views.stats_view, name='stats'),
    path('toponym/<str:toponym_id>/', views.toponym_detail, name='detail'),
    path('api/toponyms/', views.api_toponyms, name='api_toponyms'),
    path('export/', views.export_toponyms, name='export'),
]