import secrets
from datetime import timedelta
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils import timezone

from servicos.models import Servico
from solicitacoes.models import ContaGateway

from .forms import (
    CadastroForm,
    ClienteForm,
    LoginForm,
    ProfissionalForm,
)
from .models import (
    Cliente,
    Profissional,
    Usuario,
)


def home(request):
    """View para a Landing Page na raiz (/)"""
    if request.user.is_authenticated:
        return redirect("usuarios:perfil")

    # Busca até 6 serviços ativos para a vitrine
    servicos_destaque = Servico.objects.filter(ativo=True)[:6]

    return render(
        request,
        "usuarios/home.html",
        {
            "servicos_destaque": servicos_destaque,
        },
    )


class UsuarioLoginView(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("usuarios:perfil")

    if request.method == "POST":
        form = CadastroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            if usuario.tipo_usuario == Usuario.TipoUsuario.CLIENTE:
                Cliente.objects.create(usuario=usuario)
                login(request, usuario)
                return redirect("usuarios:perfil")

            if usuario.tipo_usuario == Usuario.TipoUsuario.PROFISSIONAL:
                request.session["usuario_cadastro_id"] = usuario.id
                return redirect("usuarios:cadastro_profissional")
    else:
        form = CadastroForm()

    return render(
        request,
        "usuarios/cadastro.html",
        {"form": form},
    )


# def cadastro_profissional(request):
#     usuario_id = request.session.get("usuario_cadastro_id")
#
#     if not usuario_id:
#         return redirect("usuarios:cadastro")
#
#     try:
#         usuario = Usuario.objects.get(
#             id=usuario_id,
#             tipo_usuario=Usuario.TipoUsuario.PROFISSIONAL,
#         )
#     except Usuario.DoesNotExist:
#         return redirect("usuarios:cadastro")
#
#     if request.method == "POST":
#         form = ProfissionalForm(request.POST, request.FILES)
#         if form.is_valid():
#             profissional = form.save(commit=False)
#             profissional.usuario = usuario
#             profissional.save()
#
#             del request.session["usuario_cadastro_id"]
#
#             messages.success(
#                 request,
#                 "Cadastro realizado. Seu perfil será analisado pela plataforma.",
#             )
#             login(request, usuario)
#             return redirect("usuarios:perfil")
#     else:
#         form = ProfissionalForm()
#
#     return render(
#         request,
#         "usuarios/cadastro_profissional.html",
#         {
#             "form": form,
#             "usuario": usuario,
#         },
#     )
def cadastro_profissional(request):
    # Se o usuário já estiver logado, editamos diretamente o perfil dele
    if request.user.is_authenticated:
        if request.user.tipo_usuario != Usuario.TipoUsuario.PROFISSIONAL:
            return redirect("usuarios:perfil")

        profissional, _ = Profissional.objects.get_or_create(usuario=request.user)

        if request.method == "POST":
            # Se o usuário clicou em cancelar, redireciona sem salvar
            if "cancelar" in request.POST:
                return redirect("usuarios:perfil")

            form = ProfissionalForm(request.POST, request.FILES, instance=profissional)

            if form.is_valid():
                prof = form.save(commit=False)
                prof.usuario = request.user
                prof.save()

                # Salva as categorias ManyToMany se houver
                form.save_m2m()

                messages.success(request, "Cadastro atualizado com sucesso!")
                return redirect("usuarios:perfil")
        else:
            form = ProfissionalForm(instance=profissional)

        return render(
            request,
            "usuarios/cadastro_profissional.html",
            {
                "form": form,
                "usuario": request.user,
            },
        )

    # Caso contrário, mantém o fluxo original para novos cadastros via sessão
    usuario_id = request.session.get("usuario_cadastro_id")
    if not usuario_id:
        return redirect("usuarios:cadastro")

    try:
        usuario = Usuario.objects.get(
            id=usuario_id,
            tipo_usuario=Usuario.TipoUsuario.PROFISSIONAL,
        )
    except Usuario.DoesNotExist:
        return redirect("usuarios:cadastro")

    # Verifica se já existe perfil profissional associado para evitar duplicidade
    profissional, _ = Profissional.objects.get_or_create(usuario=usuario)

    if request.method == "POST":
        if "cancelar" in request.POST:
            return redirect("usuarios:perfil")

        form = ProfissionalForm(request.POST, request.FILES, instance=profissional)

        if form.is_valid():
            prof = form.save(commit=False)
            prof.usuario = usuario
            prof.save()

            form.save_m2m()

            if "usuario_cadastro_id" in request.session:
                del request.session["usuario_cadastro_id"]

            messages.success(
                request,
                "Cadastro realizado. Seu perfil será analisado pela plataforma.",
            )
            login(request, usuario)
            return redirect("usuarios:perfil")
    else:
        form = ProfissionalForm(instance=profissional)

    return render(
        request,
        "usuarios/cadastro_profissional.html",
        {
            "form": form,
            "usuario": usuario,
        },
    )

def perfil(request):
    if not request.user.is_authenticated:
        return redirect("usuarios:login")

    contexto = {
        "usuario": request.user,
        "conta_gateway": None,
    }

    if request.user.tipo_usuario == Usuario.TipoUsuario.CLIENTE:
        contexto["cliente"] = getattr(request.user, "cliente", None)

    elif request.user.tipo_usuario == Usuario.TipoUsuario.PROFISSIONAL:
        contexto["profissional"] = getattr(request.user, "profissional", None)

        if contexto["profissional"]:
            contexto["conta_gateway"] = (
                ContaGateway.objects.filter(
                    profissional=contexto["profissional"],
                    gateway=ContaGateway.Gateway.MERCADO_PAGO,
                    ativo=True,
                ).first()
            )

    return render(
        request,
        "usuarios/perfil.html",
        contexto,
    )


@login_required
def conectar_mercado_pago(request):
    if request.user.tipo_usuario != Usuario.TipoUsuario.PROFISSIONAL:
        messages.error(request, "Esta área é exclusiva para profissionais.")
        return redirect("usuarios:perfil")

    profissional = getattr(request.user, "profissional", None)

    if profissional is None:
        messages.error(request, "Seu perfil profissional não foi encontrado.")
        return redirect("usuarios:perfil")

    if not profissional.aprovado:
        messages.error(request, "Seu cadastro profissional ainda não foi aprovado.")
        return redirect("usuarios:perfil")

    client_id = getattr(settings, "MERCADO_PAGO_CLIENT_ID", None)
    redirect_uri = getattr(settings, "MERCADO_PAGO_REDIRECT_URI", None)

    if not client_id:
        messages.error(request, "MERCADO_PAGO_CLIENT_ID não está configurado.")
        return redirect("usuarios:perfil")

    if not redirect_uri:
        messages.error(request, "MERCADO_PAGO_REDIRECT_URI não está configurado.")
        return redirect("usuarios:perfil")

    state = secrets.token_urlsafe(32)
    request.session["mercado_pago_oauth_state"] = state
    request.session["mercado_pago_oauth_profissional_id"] = profissional.id
    request.session.modified = True

    params = {
        "client_id": client_id,
        "response_type": "code",
        "platform_id": "mp",
        "state": state,
        "redirect_uri": redirect_uri,
    }

    authorization_url = "https://auth.mercadopago.com.br/authorization?" + urlencode(params)
    return redirect(authorization_url)


@login_required
def mercado_pago_callback(request):
    if request.user.tipo_usuario != Usuario.TipoUsuario.PROFISSIONAL:
        messages.error(request, "Esta área é exclusiva para profissionais.")
        return redirect("usuarios:perfil")

    profissional = getattr(request.user, "profissional", None)

    if profissional is None:
        messages.error(request, "Seu perfil profissional não foi encontrado.")
        return redirect("usuarios:perfil")

    error = request.GET.get("error")

    if error:
        error_description = request.GET.get(
            "error_description",
            "O Mercado Pago recusou a autorização.",
        )
        messages.error(
            request,
            f"Não foi possível conectar sua conta ao Mercado Pago: {error_description}",
        )
        request.session.pop("mercado_pago_oauth_state", None)
        request.session.pop("mercado_pago_oauth_profissional_id", None)
        return redirect("usuarios:perfil")

    code = request.GET.get("code")
    state = request.GET.get("state")

    state_session = request.session.get("mercado_pago_oauth_state")
    profissional_session_id = request.session.get("mercado_pago_oauth_profissional_id")

    if not code:
        messages.error(request, "O Mercado Pago não retornou o código de autorização.")
        return redirect("usuarios:perfil")

    if not state or state != state_session:
        messages.error(request, "Não foi possível validar a autorização do Mercado Pago.")
        return redirect("usuarios:perfil")

    if profissional_session_id != profissional.id:
        messages.error(request, "A autorização do Mercado Pago não pertence ao profissional atual.")
        return redirect("usuarios:perfil")

    client_id = getattr(settings, "MERCADO_PAGO_CLIENT_ID", None)
    client_secret = getattr(settings, "MERCADO_PAGO_CLIENT_SECRET", None)
    redirect_uri = getattr(settings, "MERCADO_PAGO_REDIRECT_URI", None)

    if not client_id or not client_secret or not redirect_uri:
        messages.error(
            request,
            "As credenciais do Mercado Pago não estão configuradas corretamente no servidor.",
        )
        return redirect("usuarios:perfil")

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    try:
        response = requests.post(
            "https://api.mercadopago.com/oauth/token",
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=20,
        )
    except requests.RequestException:
        messages.error(request, "Não foi possível comunicar com o Mercado Pago.")
        return redirect("usuarios:perfil")

    if not response.ok:
        try:
            erro = response.json()
        except ValueError:
            erro = {}

        detalhe = erro.get("message") or erro.get("error") or "Erro desconhecido."
        messages.error(request, f"O Mercado Pago não autorizou a conexão: {detalhe}")
        return redirect("usuarios:perfil")

    try:
        dados = response.json()
    except ValueError:
        messages.error(request, "O Mercado Pago retornou uma resposta inválida.")
        return redirect("usuarios:perfil")

    access_token = dados.get("access_token")
    refresh_token = dados.get("refresh_token")
    user_id = dados.get("user_id")
    expires_in = dados.get("expires_in")

    if not access_token:
        messages.error(request, "O Mercado Pago não retornou um Access Token.")
        return redirect("usuarios:perfil")

    token_expires_at = None
    if expires_in:
        try:
            token_expires_at = timezone.now() + timedelta(seconds=int(expires_in))
        except (TypeError, ValueError):
            token_expires_at = None

    gateway, created = ContaGateway.objects.update_or_create(
        profissional=profissional,
        defaults={
            "gateway": ContaGateway.Gateway.MERCADO_PAGO,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expires_at": token_expires_at,
            "ativo": True,
        },
    )

    update_fields = ["mercado_pago_connected", "mercado_pago_connected_at"]
    profissional.mercado_pago_connected = True
    profissional.mercado_pago_connected_at = timezone.now()

    if user_id:
        profissional.mercado_pago_user_id = str(user_id)
        update_fields.append("mercado_pago_user_id")

    profissional.save(update_fields=update_fields)

    request.session.pop("mercado_pago_oauth_state", None)
    request.session.pop("mercado_pago_oauth_profissional_id", None)

    messages.success(
        request,
        "Sua conta do Mercado Pago foi conectada com sucesso. Agora você poderá receber pagamentos através da plataforma.",
    )

    return redirect("usuarios:perfil")