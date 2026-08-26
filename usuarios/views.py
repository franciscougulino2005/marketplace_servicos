from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .forms import (
    CadastroForm,
    ClienteForm,
    LoginForm,
    ProfissionalForm,
)
from .models import Cliente, Profissional, Usuario


class UsuarioLoginView(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = LoginForm


def cadastro(request):

    if request.user.is_authenticated:
        return redirect("usuarios:perfil")

    if request.method == "POST":

        form = CadastroForm(request.POST)

        if form.is_valid():

            usuario = form.save()

            if usuario.tipo_usuario == Usuario.TipoUsuario.CLIENTE:

                Cliente.objects.create(
                    usuario=usuario
                )

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


def cadastro_profissional(request):

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

    if request.method == "POST":

        form = ProfissionalForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            profissional = form.save(commit=False)
            profissional.usuario = usuario
            profissional.save()

            del request.session["usuario_cadastro_id"]

            messages.success(
                request,
                "Cadastro realizado. Seu perfil será analisado pela plataforma.",
            )

            login(request, usuario)

            return redirect("usuarios:perfil")

    else:
        form = ProfissionalForm()

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
    }

    if request.user.tipo_usuario == Usuario.TipoUsuario.CLIENTE:

        contexto["cliente"] = getattr(
            request.user,
            "cliente",
            None,
        )

    elif request.user.tipo_usuario == Usuario.TipoUsuario.PROFISSIONAL:

        contexto["profissional"] = getattr(
            request.user,
            "profissional",
            None,
        )

    return render(
        request,
        "usuarios/perfil.html",
        contexto,
    )

@login_required
def conectar_mercado_pago(request):

    if request.user.tipo_usuario != Usuario.TipoUsuario.PROFISSIONAL:

        messages.error(
            request,
            "Esta área é exclusiva para profissionais.",
        )

        return redirect(
            "usuarios:perfil"
        )

    profissional = getattr(
        request.user,
        "profissional",
        None,
    )

    if profissional is None:

        messages.error(
            request,
            "Seu perfil profissional não foi encontrado.",
        )

        return redirect(
            "usuarios:perfil"
        )

    if not profissional.aprovado:

        messages.error(
            request,
            "Seu cadastro profissional ainda não foi aprovado.",
        )

        return redirect(
            "usuarios:perfil"
        )

    # A URL OAuth será construída na próxima etapa.
    messages.info(
        request,
        "A conexão com o Mercado Pago será iniciada.",
    )

    return redirect(
        "usuarios:perfil"
    )