from django.urls import path
from . import views

app_name = 'categorias'

urlpatterns = [
    path('', views.lista_categorias, name='lista'),
    path('nova/', views.criar_categoria, name='criar'),
    path('<int:pk>/editar/', views.editar_categoria, name='editar'),
    path('<int:pk>/alternar-status/', views.alternar_status_categoria, name='alternar_status'),
]