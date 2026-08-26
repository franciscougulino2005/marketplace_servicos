from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import conectar_mercado_pago

from .views import (
    UsuarioLoginView,
    cadastro,
    cadastro_profissional,
    perfil,
)


app_name = "usuarios"


urlpatterns = [
    path(
        "login/",
        UsuarioLoginView.as_view(),
        name="login",
    ),

    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),

    path(
        "cadastro/",
        cadastro,
        name="cadastro",
    ),

    path(
        "cadastro/profissional/",
        cadastro_profissional,
        name="cadastro_profissional",
    ),

    path(
        "perfil/",
        perfil,
        name="perfil",
    ),

    path(
        "mercadopago/conectar/",
        conectar_mercado_pago,
        name="conectar_mercado_pago",
    ),

]