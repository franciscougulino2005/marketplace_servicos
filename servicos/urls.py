from django.urls import path

from .views import (
    alterar_status_servico,
    editar_servico,
    lista_servicos,
    novo_servico,
)


app_name = "servicos"


urlpatterns = [

    path(
        "",
        lista_servicos,
        name="lista",
    ),

    path(
        "novo/",
        novo_servico,
        name="novo",
    ),

    path(
        "<int:pk>/editar/",
        editar_servico,
        name="editar",
    ),

    path(
        "<int:pk>/status/",
        alterar_status_servico,
        name="status",
    ),

]