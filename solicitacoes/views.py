from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db import IntegrityError, transaction

from .forms import (
    OrcamentoForm,
    SolicitacaoForm,
)

from usuarios.models import Usuario
from .models import (
    Solicitacao,
    SolicitacaoFoto,
    Orcamento,
    Contratacao,
    Pagamento,
)


def cliente_obrigatorio(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        if request.user.tipo_usuario != Usuario.TipoUsuario.CLIENTE:

            messages.error(
                request,
                "Esta área é exclusiva para clientes.",
            )

            return redirect("usuarios:perfil")

        cliente = getattr(
            request.user,
            "cliente",
            None,
        )

        if cliente is None:

            messages.error(
                request,
                "Seu perfil de cliente não foi encontrado.",
            )

            return redirect("usuarios:perfil")

        return view_func(
            request,
            cliente=cliente,
            *args,
            **kwargs,
        )

    return wrapper


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

        return view_func(
            request,
            profissional=profissional,
            *args,
            **kwargs,
        )

    return wrapper


@cliente_obrigatorio
def lista_solicitacoes(request, cliente):

    solicitacoes = (
        Solicitacao.objects
        .filter(cliente=cliente)
        .select_related("categoria")
    )

    return render(
        request,
        "solicitacoes/lista_solicitacoes.html",
        {
            "solicitacoes": solicitacoes,
            "cliente": cliente,
        },
    )


@cliente_obrigatorio
def nova_solicitacao(request, cliente):

    if request.method == "POST":

        form = SolicitacaoForm(
            request.POST
        )

        arquivos = request.FILES.getlist(
            "fotos"
        )

        if len(arquivos) > 5:

            form.add_error(
                None,
                "Você pode enviar no máximo 5 fotos.",
            )

        if form.is_valid():

            solicitacao = form.save(
                commit=False
            )

            solicitacao.cliente = cliente

            solicitacao.save()

            for arquivo in arquivos:

                SolicitacaoFoto.objects.create(
                    solicitacao=solicitacao,
                    imagem=arquivo,
                )

            messages.success(
                request,
                "Sua solicitação foi criada com sucesso.",
            )

            return redirect(
                "solicitacoes:detalhe",
                pk=solicitacao.pk,
            )

    else:

        form = SolicitacaoForm()

    return render(
        request,
        "solicitacoes/nova_solicitacao.html",
        {
            "form": form,
            "cliente": cliente,
        },
    )


@cliente_obrigatorio
def detalhe_solicitacao(
    request,
    cliente,
    pk,
):

    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related(
            "categoria",
            "cliente",
        ),
        pk=pk,
        cliente=cliente,
    )

    fotos = solicitacao.fotos.all()

    return render(
        request,
        "solicitacoes/detalhe_solicitacao.html",
        {
            "solicitacao": solicitacao,
            "fotos": fotos,
        },
    )


@cliente_obrigatorio
def orcamentos_solicitacao(
    request,
    cliente,
    pk,
):

    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related(
            "categoria",
            "cliente",
        ),
        pk=pk,
        cliente=cliente,
    )

    orcamentos = (
        Orcamento.objects
        .filter(
            solicitacao=solicitacao,
            status=Orcamento.Status.ENVIADO,
        )
        .select_related(
            "profissional",
        )
        .order_by(
            "valor",
            "data_criacao",
        )
    )

    return render(
        request,
        "solicitacoes/orcamentos_solicitacao.html",
        {
            "solicitacao": solicitacao,
            "orcamentos": orcamentos,
        },
    )


@cliente_obrigatorio
def cancelar_solicitacao(
    request,
    cliente,
    pk,
):

    solicitacao = get_object_or_404(
        Solicitacao,
        pk=pk,
        cliente=cliente,
    )

    if request.method == "POST":

        if solicitacao.status in [
            Solicitacao.Status.ABERTA,
            Solicitacao.Status.RECEBENDO_ORCAMENTOS,
        ]:

            solicitacao.status = (
                Solicitacao.Status.CANCELADA
            )

            solicitacao.save(
                update_fields=[
                    "status",
                    "data_atualizacao",
                ]
            )

            messages.success(
                request,
                "Solicitação cancelada.",
            )

        else:

            messages.error(
                request,
                "Esta solicitação não pode mais ser cancelada.",
            )

    return redirect(
        "solicitacoes:detalhe",
        pk=solicitacao.pk,
    )


@profissional_obrigatorio
def lista_solicitacoes_disponiveis(
    request,
    profissional,
):

    solicitacoes = (
        Solicitacao.objects
        .filter(
            categoria__servicos__profissional=profissional,
            categoria__servicos__ativo=True,
            status__in=[
                Solicitacao.Status.ABERTA,
                Solicitacao.Status.RECEBENDO_ORCAMENTOS,
            ],
        )
        .exclude(
            orcamentos__profissional=profissional,
        )
        .select_related(
            "categoria",
            "cliente",
        )
        .distinct()
    )

    return render(
        request,
        "solicitacoes/disponiveis.html",
        {
            "solicitacoes": solicitacoes,
        },
    )


@profissional_obrigatorio
def novo_orcamento(
    request,
    profissional,
    pk,
):

    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related(
            "categoria",
            "cliente",
        ),
        pk=pk,
        categoria__servicos__profissional=profissional,
        categoria__servicos__ativo=True,
        status__in=[
            Solicitacao.Status.ABERTA,
            Solicitacao.Status.RECEBENDO_ORCAMENTOS,
        ],
    )

    if Orcamento.objects.filter(
        solicitacao=solicitacao,
        profissional=profissional,
    ).exists():

        messages.warning(
            request,
            "Você já enviou um orçamento para esta solicitação.",
        )

        return redirect(
            "solicitacoes:meus_orcamentos"
        )

    if request.method == "POST":

        form = OrcamentoForm(request.POST)

        if form.is_valid():

            try:

                with transaction.atomic():

                    orcamento = form.save(
                        commit=False
                    )

                    orcamento.solicitacao = solicitacao
                    orcamento.profissional = profissional
                    orcamento.save()

                    if solicitacao.status == (
                        Solicitacao.Status.ABERTA
                    ):

                        solicitacao.status = (
                            Solicitacao.Status.RECEBENDO_ORCAMENTOS
                        )

                        solicitacao.save(
                            update_fields=[
                                "status",
                                "data_atualizacao",
                            ]
                        )

            except IntegrityError:

                messages.warning(
                    request,
                    "Você já enviou um orçamento para esta solicitação.",
                )

                return redirect(
                    "solicitacoes:disponiveis"
                )

            messages.success(
                request,
                "Orçamento enviado com sucesso.",
            )

            return redirect(
                "solicitacoes:meus_orcamentos"
            )

    else:

        form = OrcamentoForm()

    return render(
        request,
        "solicitacoes/novo_orcamento.html",
        {
            "form": form,
            "solicitacao": solicitacao,
        },
    )


@profissional_obrigatorio
def meus_orcamentos(
    request,
    profissional,
):

    orcamentos = (
        Orcamento.objects
        .filter(
            profissional=profissional,
        )
        .select_related(
            "solicitacao",
            "solicitacao__categoria",
        )
    )

    return render(
        request,
        "solicitacoes/meus_orcamentos.html",
        {
            "orcamentos": orcamentos,
        },
    )


@cliente_obrigatorio
def contratar_orcamento(
    request,
    cliente,
    pk,
):

    if request.method != "POST":

        messages.error(
            request,
            "A contratação deve ser realizada através do formulário.",
        )

        return redirect(
            "solicitacoes:lista_solicitacoes"
        )

    orcamento = get_object_or_404(
        Orcamento.objects.select_related(
            "solicitacao",
            "solicitacao__cliente",
            "profissional",
        ),
        pk=pk,
        solicitacao__cliente=cliente,
    )

    solicitacao = orcamento.solicitacao

    if solicitacao.status not in [
        Solicitacao.Status.ABERTA,
        Solicitacao.Status.RECEBENDO_ORCAMENTOS,
    ]:

        messages.error(
            request,
            "Esta solicitação não está mais disponível para contratação.",
        )

        return redirect(
            "solicitacoes:orcamentos_solicitacao",
            pk=solicitacao.pk,
        )

    if orcamento.status != Orcamento.Status.ENVIADO:

        messages.error(
            request,
            "Este orçamento não está mais disponível para contratação.",
        )

        return redirect(
            "solicitacoes:orcamentos_solicitacao",
            pk=solicitacao.pk,
        )

    if not orcamento.profissional.ativo:

        messages.error(
            request,
            "Este profissional não está mais ativo na plataforma.",
        )

        return redirect(
            "solicitacoes:orcamentos_solicitacao",
            pk=solicitacao.pk,
        )

    if not orcamento.profissional.aprovado:

        messages.error(
            request,
            "Este profissional ainda não está aprovado pela plataforma.",
        )

        return redirect(
            "solicitacoes:orcamentos_solicitacao",
            pk=solicitacao.pk,
        )

    if Contratacao.objects.filter(
        solicitacao=solicitacao,
    ).exists():

        messages.error(
            request,
            "Esta solicitação já possui uma contratação.",
        )

        return redirect(
            "solicitacoes:orcamentos_solicitacao",
            pk=solicitacao.pk,
        )

    percentual_comissao = 10

    valor = orcamento.valor

    valor_comissao = (
        valor * percentual_comissao / 100
    )

    valor_profissional = (
        valor - valor_comissao
    )

    try:

        with transaction.atomic():

            contratacao = Contratacao.objects.create(
                solicitacao=solicitacao,
                orcamento=orcamento,
                cliente=cliente,
                profissional=orcamento.profissional,
                valor=valor,
                percentual_comissao=percentual_comissao,
                valor_comissao=valor_comissao,
                valor_profissional=valor_profissional,
                status=Contratacao.Status.AGUARDANDO_PAGAMENTO,
            )

            Pagamento.objects.create(
                contratacao=contratacao,
                cliente=cliente,
                valor=valor,
                status=Pagamento.Status.PENDENTE,
            )

            orcamento.status = (
                Orcamento.Status.ACEITO
            )

            orcamento.save(
                update_fields=[
                    "status",
                    "data_atualizacao",
                ]
            )

            Orcamento.objects.filter(
                solicitacao=solicitacao,
            ).exclude(
                pk=orcamento.pk,
            ).filter(
                status=Orcamento.Status.ENVIADO,
            ).update(
                status=Orcamento.Status.RECUSADO,
            )

            solicitacao.status = (
                Solicitacao.Status.ORCAMENTO_ACEITO
            )

            solicitacao.save(
                update_fields=[
                    "status",
                    "data_atualizacao",
                ]
            )

    except IntegrityError:

        messages.error(
            request,
            "Não foi possível concluir a contratação. Tente novamente.",
        )

        return redirect(
            "solicitacoes:orcamentos_solicitacao",
            pk=solicitacao.pk,
        )

    messages.success(
        request,
        "Orçamento contratado com sucesso! Agora realize o pagamento.",
    )

    return redirect(
        "solicitacoes:pagamento",
        pk=contratacao.pk,
    )


@cliente_obrigatorio
def pagamento(
    request,
    cliente,
    pk,
):

    contratacao = get_object_or_404(
        Contratacao.objects.select_related(
            "solicitacao",
            "profissional",
            "cliente",
            "orcamento",
        ),
        pk=pk,
        cliente=cliente,
    )

    pagamento_obj = get_object_or_404(
        Pagamento,
        contratacao=contratacao,
        cliente=cliente,
    )

    if pagamento_obj.status == Pagamento.Status.APROVADO:

        messages.info(
            request,
            "Este pagamento já foi aprovado.",
        )

        return redirect(
            "solicitacoes:detalhe",
            pk=contratacao.solicitacao.pk,
        )

    if request.method == "POST":

        metodo = request.POST.get(
            "metodo"
        )

        if metodo not in [
            Pagamento.Metodo.PIX,
            Pagamento.Metodo.CARTAO,
            Pagamento.Metodo.BOLETO,
        ]:

            messages.error(
                request,
                "Selecione um método de pagamento.",
            )

        else:

            pagamento_obj.metodo = metodo

            pagamento_obj.status = (
                Pagamento.Status.PROCESSANDO
            )

            pagamento_obj.save(
                update_fields=[
                    "metodo",
                    "status",
                    "data_atualizacao",
                ]
            )

            return redirect(
                "solicitacoes:processar_pagamento",
                pk=pagamento_obj.pk,
            )

    return render(
        request,
        "solicitacoes/pagamento.html",
        {
            "contratacao": contratacao,
            "pagamento": pagamento_obj,
        },
    )


@cliente_obrigatorio
def processar_pagamento(
    request,
    cliente,
    pk,
):

    pagamento_obj = get_object_or_404(
        Pagamento.objects.select_related(
            "contratacao",
            "contratacao__solicitacao",
            "contratacao__profissional",
            "contratacao__orcamento",
            "cliente",
        ),
        pk=pk,
        cliente=cliente,
    )

    contratacao = pagamento_obj.contratacao

    if pagamento_obj.status == Pagamento.Status.APROVADO:

        messages.info(
            request,
            "Este pagamento já foi aprovado.",
        )

        return redirect(
            "solicitacoes:detalhe",
            pk=contratacao.solicitacao.pk,
        )

    if pagamento_obj.status != Pagamento.Status.PROCESSANDO:

        messages.error(
            request,
            "Este pagamento não está disponível para processamento.",
        )

        return redirect(
            "solicitacoes:pagamento",
            pk=contratacao.pk,
        )

    return render(
        request,
        "solicitacoes/processar_pagamento.html",
        {
            "pagamento": pagamento_obj,
            "contratacao": contratacao,
        },
    )