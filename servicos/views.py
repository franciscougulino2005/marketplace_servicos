from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.models import Usuario

from .forms import ServicoForm
from .models import Servico


def profissional_obrigatorio(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        if request.user.tipo_usuario != Usuario.TipoUsuario.PROFISSIONAL:
            messages.error(
                request,
                "Esta área é exclusiva para profissionais.",
            )

            return redirect("usuarios:perfil")

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

            return redirect("usuarios:perfil")

        if not profissional.aprovado:

            messages.warning(
                request,
                "Seu cadastro profissional ainda está em análise.",
            )

            return redirect("usuarios:perfil")

        return view_func(
            request,
            profissional=profissional,
            *args,
            **kwargs,
        )

    return wrapper


@profissional_obrigatorio
def lista_servicos(request, profissional):

    servicos = (
        Servico.objects
        .filter(profissional=profissional)
        .select_related("categoria")
    )

    return render(
        request,
        "servicos/lista_servicos.html",
        {
            "profissional": profissional,
            "servicos": servicos,
        },
    )


@profissional_obrigatorio
def novo_servico(request, profissional):

    if request.method == "POST":

        form = ServicoForm(request.POST)

        if form.is_valid():

            servico = form.save(commit=False)

            servico.profissional = profissional

            servico.save()

            messages.success(
                request,
                "Serviço cadastrado com sucesso.",
            )

            return redirect(
                "servicos:lista"
            )

    else:

        form = ServicoForm()

    return render(
        request,
        "servicos/novo_servico.html",
        {
            "form": form,
            "profissional": profissional,
        },
    )


@profissional_obrigatorio
def editar_servico(
    request,
    profissional,
    pk,
):

    servico = get_object_or_404(
        Servico,
        pk=pk,
        profissional=profissional,
    )

    if request.method == "POST":

        form = ServicoForm(
            request.POST,
            instance=servico,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Serviço atualizado com sucesso.",
            )

            return redirect(
                "servicos:lista"
            )

    else:

        form = ServicoForm(
            instance=servico
        )

    return render(
        request,
        "servicos/editar_servico.html",
        {
            "form": form,
            "servico": servico,
            "profissional": profissional,
        },
    )


@profissional_obrigatorio
def alterar_status_servico(
    request,
    profissional,
    pk,
):

    servico = get_object_or_404(
        Servico,
        pk=pk,
        profissional=profissional,
    )

    if request.method == "POST":

        servico.ativo = not servico.ativo
        servico.save(
            update_fields=[
                "ativo",
                "data_atualizacao",
            ]
        )

        if servico.ativo:

            messages.success(
                request,
                "Serviço ativado.",
            )

        else:

            messages.success(
                request,
                "Serviço desativado.",
            )

    return redirect(
        "servicos:lista"
    )