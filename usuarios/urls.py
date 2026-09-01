from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from .views import (
    UsuarioLoginView,
    cadastro,
    cadastro_profissional,
    conectar_mercado_pago,
    mercado_pago_callback,
    perfil,
)

app_name = "usuarios"

urlpatterns = [
    # Autenticação e Perfil
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
    # Integração Mercado Pago
    path(
        "mercadopago/conectar/",
        conectar_mercado_pago,
        name="conectar_mercado_pago",
    ),
    path(
        "mercadopago/callback/",
        mercado_pago_callback,
        name="mercado_pago_callback",
    ),
    # Recuperação de Senha
    path(
        "esqueci-senha/",
        auth_views.PasswordResetView.as_view(
            template_name="usuarios/password_reset.html",
            email_template_name="usuarios/password_reset_email.txt",
            subject_template_name="usuarios/password_reset_subject.txt",
            success_url=reverse_lazy("usuarios:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "esqueci-senha/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="usuarios/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "redefinir/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="usuarios/password_reset_confirm.html",
            success_url=reverse_lazy("usuarios:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "redefinir/concluido/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="usuarios/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]