from django.urls import path
from . import views

app_name = 'relatorios_administrativos'

urlpatterns = [
    path('', views.dashboard_administrativo, name='dashboard_administrativo'),
    path('comissoes/', views.relatorio_comissoes, name='comissoes'),
]