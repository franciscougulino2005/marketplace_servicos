import mercadopago
import json
import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from usuarios.models import Usuario
from .forms import OrcamentoForm, SolicitacaoForm
from .models import Contratacao, Orcamento, Pagamento, Solicitacao, SolicitacaoFoto

logger = logging.getLogger(__name__)


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
        Solicitacao.objects.filter(cliente=cliente).select_related("categoria")
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

        form = SolicitacaoForm(request.POST)

        arquivos = request.FILES.getlist("fotos")

        if len(arquivos) > 5:

            form.add_error(
                None,
                "Você pode enviar no máximo 5 fotos.",
            )

        if form.is_valid():

            solicitacao = form.save(commit=False)

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


@login_required
def detalhe_solicitacao(request, pk):
    """Permite visualização tanto por Clientes (donos) quanto por Profissionais (contratados)."""
    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related("categoria", "cliente", "cliente__usuario"),
        pk=pk,
    )

    usuario = request.user

    # Identifica a relação do usuário logado com a solicitação
    is_cliente = hasattr(usuario, "cliente") and solicitacao.cliente == usuario.cliente
    is_profissional_contratado = (
        hasattr(usuario, "profissional")
        and Contratacao.objects.filter(
            solicitacao=solicitacao, profissional=usuario.profissional
        ).exists()
    )

    # Bloqueia apenas quem não for nem o cliente dono nem o profissional contratado
    if not (is_cliente or is_profissional_contratado):
        messages.error(request, "Você não tem permissão para acessar esta solicitação.")
        return redirect("usuarios:perfil")

    fotos = solicitacao.fotos.all()

    return render(
        request,
        "solicitacoes/detalhe_solicitacao.html",
        {
            "solicitacao": solicitacao,
            "fotos": fotos,
            "is_cliente": is_cliente,
            "is_profissional": is_profissional_contratado,
        },
    )


@login_required
def orcamentos_solicitacao(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    usuario = request.user

    # Valida se é o cliente ou um profissional
    is_cliente = hasattr(usuario, "cliente") and solicitacao.cliente == usuario.cliente
    is_profissional = hasattr(usuario, "profissional")

    if not (is_cliente or is_profissional):
        messages.error(request, "Acesso não permitido.")
        return redirect("usuarios:perfil")

    orcamentos = Orcamento.objects.filter(solicitacao=solicitacao)
    return render(request, "solicitacoes/orcamentos_solicitacao.html", {
        "solicitacao": solicitacao,
        "orcamentos": orcamentos
    })


@cliente_obrigatorio
def aceitar_orcamento(
    request,
    cliente,
    pk,
):
    if request.method != "POST":
        return redirect(
            "solicitacoes:orcamentos",
            pk=pk,
        )

    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related(
            "cliente",
            "categoria",
        ),
        pk=pk,
        cliente=cliente,
    )

    orcamento = get_object_or_404(
        Orcamento.objects.select_related(
            "profissional",
        ),
        pk=request.POST.get("orcamento_id"),
        solicitacao=solicitacao,
        status=Orcamento.Status.ENVIADO,
    )

    if hasattr(solicitacao, "contratacao"):
        messages.error(
            request,
            "Esta solicitação já possui uma contratação.",
        )

        return redirect(
            "solicitacoes:orcamentos",
            pk=solicitacao.pk,
        )

    with transaction.atomic():

        orcamento.status = Orcamento.Status.ACEITO

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

        percentual = (
            solicitacao.contratacao.percentual_comissao
            if hasattr(solicitacao, "contratacao")
            else 10
        )

        valor = orcamento.valor

        valor_comissao = valor * percentual / 100

        valor_profissional = valor - valor_comissao

        Contratacao.objects.create(
            solicitacao=solicitacao,
            orcamento=orcamento,
            cliente=cliente,
            profissional=orcamento.profissional,
            valor=valor,
            percentual_comissao=percentual,
            valor_comissao=valor_comissao,
            valor_profissional=valor_profissional,
            status=Contratacao.Status.AGUARDANDO_PAGAMENTO,
        )

        solicitacao.status = Solicitacao.Status.ORCAMENTO_ACEITO

        solicitacao.save(
            update_fields=[
                "status",
                "data_atualizacao",
            ]
        )

    messages.success(
        request,
        "Orçamento aceito com sucesso! Agora você poderá realizar o pagamento.",
    )

    return redirect(
        "solicitacoes:detalhe",
        pk=solicitacao.pk,
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

            solicitacao.status = Solicitacao.Status.CANCELADA

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
        Solicitacao.objects.filter(
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

        return redirect("solicitacoes:meus_orcamentos")

    if request.method == "POST":

        form = OrcamentoForm(request.POST)

        if form.is_valid():

            try:

                with transaction.atomic():

                    orcamento = form.save(commit=False)

                    orcamento.solicitacao = solicitacao
                    orcamento.profissional = profissional
                    orcamento.save()

                    if solicitacao.status == (Solicitacao.Status.ABERTA):

                        solicitacao.status = Solicitacao.Status.RECEBENDO_ORCAMENTOS

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

                return redirect("solicitacoes:disponiveis")

            messages.success(
                request,
                "Orçamento enviado com sucesso.",
            )

            return redirect("solicitacoes:meus_orcamentos")

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

    orcamentos = Orcamento.objects.filter(
        profissional=profissional,
    ).select_related(
        "solicitacao",
        "solicitacao__categoria",
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

        return redirect("solicitacoes:lista_solicitacoes")

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

    valor_comissao = valor * percentual_comissao / 100

    valor_profissional = valor - valor_comissao

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

            orcamento.status = Orcamento.Status.ACEITO

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

            solicitacao.status = Solicitacao.Status.ORCAMENTO_ACEITO

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
def pagamento(request, cliente, pk):
    contratacao = get_object_or_404(
        Contratacao.objects.select_related(
            "solicitacao", "profissional", "orcamento"
        ),
        pk=pk,
        solicitacao__cliente=cliente,
    )

    if request.method == "POST":
        metodo = request.POST.get("metodo_pagamento")

        if metodo not in [
            Pagamento.Metodo.PIX,
            Pagamento.Metodo.CARTAO,
            Pagamento.Metodo.BOLETO,
        ]:
            messages.error(
                request, "Selecione um método de pagamento válido."
            )
            return redirect("solicitacoes:pagamento", pk=contratacao.pk)

        # Valida se o token foi configurado antes de prosseguir
        access_token = getattr(settings, "MERCADO_PAGO_ACCESS_TOKEN", None)
        if not access_token:
            messages.error(
                request,
                "Erro de configuração: MERCADO_PAGO_ACCESS_TOKEN não foi encontrado.",
            )
            return redirect("solicitacoes:pagamento", pk=contratacao.pk)

        # Cria ou recupera o registro de Pagamento
        pagamento_obj, created = Pagamento.objects.get_or_create(
            contratacao=contratacao,
            cliente=cliente,
            defaults={
                "valor": contratacao.valor,
                "metodo": metodo,
                "status": Pagamento.Status.PROCESSANDO,
            },
        )

        if not created and pagamento_obj.metodo != metodo:
            pagamento_obj.metodo = metodo
            pagamento_obj.save(update_fields=["metodo", "data_atualizacao"])

        return redirect(
            "solicitacoes:processar_pagamento", pk=pagamento_obj.pk
        )

    return render(
        request,
        "solicitacoes/pagamento.html",
        {
            "contratacao": contratacao,
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
            "cliente__usuario",
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

    # Geração do PIX no Mercado Pago
    if (
        pagamento_obj.metodo == Pagamento.Metodo.PIX
        and not pagamento_obj.mercado_pago_id
    ):

        access_token = getattr(settings, "MERCADO_PAGO_ACCESS_TOKEN", None)

        if not access_token:
            messages.error(
                request,
                "Erro: MERCADO_PAGO_ACCESS_TOKEN não foi encontrado. Verifique o arquivo .env",
            )
            return redirect("solicitacoes:pagamento", pk=contratacao.pk)

        # Inicializa a SDK passando o token explicitamente
        # Forma correta:
        sdk = mercadopago.SDK(access_token=access_token)

        cpf_limpo = (
            getattr(cliente, "cpf", "").replace(".", "").replace("-", "")
            or "00000000000"
        )

        notification_url = request.build_absolute_uri(
            "/solicitacoes/webhook/mercadopago/"
        )

        payment_data = {
            "transaction_amount": float(pagamento_obj.valor),
            "description": f"Contratação #{contratacao.pk} - {contratacao.solicitacao.titulo}",
            "payment_method_id": "pix",
            "external_reference": str(pagamento_obj.pk),
            # "notification_url": notification_url,  # Comentado para evitar erro de URL inválida
            "payer": {
                "email": cliente.usuario.email,
                "first_name": cliente.usuario.first_name
                or cliente.usuario.username,
                "last_name": cliente.usuario.last_name or "",
                "identification": {
                    "type": "CPF",
                    "number": cpf_limpo,
                },
            },
        }

        try:
            payment_response = sdk.payment().create(payment_data)
            resposta = payment_response.get("response", {})

            if payment_response.get("status") in [200, 201]:
                point_of_interaction = resposta.get(
                    "point_of_interaction", {}
                )
                transaction_data = point_of_interaction.get(
                    "transaction_data", {}
                )

                pagamento_obj.mercado_pago_id = str(resposta.get("id"))
                pagamento_obj.mercado_pago_status = resposta.get("status")
                pagamento_obj.mercado_pago_status_detail = resposta.get(
                    "status_detail"
                )
                pagamento_obj.identificador_transacao = str(
                    resposta.get("id")
                )

                pagamento_obj.qr_code = transaction_data.get("qr_code")
                pagamento_obj.qr_code_base64 = transaction_data.get(
                    "qr_code_base64"
                )
                pagamento_obj.ticket_url = transaction_data.get("ticket_url")

                if resposta.get("status") == "approved":
                    pagamento_obj.status = Pagamento.Status.APROVADO
                    contratacao.status = (
                        Contratacao.Status.PAGAMENTO_CONFIRMADO
                    )
                    contratacao.save(
                        update_fields=["status", "data_atualizacao"]
                    )

                pagamento_obj.save(
                    update_fields=[
                        "mercado_pago_id",
                        "mercado_pago_status",
                        "mercado_pago_status_detail",
                        "identificador_transacao",
                        "qr_code",
                        "qr_code_base64",
                        "ticket_url",
                        "status",
                        "data_atualizacao",
                    ]
                )

            else:
                mensagem_erro = (
                    resposta.get("message")
                    or (
                        resposta.get("cause", [{}])[0].get("description")
                        if isinstance(resposta.get("cause"), list)
                        and resposta.get("cause")
                        else None
                    )
                    or "Falha na comunicação com o Mercado Pago."
                )

                messages.error(
                    request,
                    f"Erro ao gerar cobrança PIX: {mensagem_erro}",
                )
                return redirect("solicitacoes:pagamento", pk=contratacao.pk)

        except Exception as e:
            messages.error(
                request,
                f"Exceção ao conectar com o gateway de pagamento: {str(e)}",
            )
            return redirect("solicitacoes:pagamento", pk=contratacao.pk)

    return render(
        request,
        "solicitacoes/processar_pagamento.html",
        {
            "pagamento": pagamento_obj,
            "contratacao": contratacao,
        },
    )


@csrf_exempt
def webhook_mercadopago(request):
    """
    Endpoint para receber notificações automáticas do Mercado Pago.
    """
    if request.method == "POST":
        topic = request.GET.get("type") or request.GET.get("topic")
        payment_id = request.GET.get("data.id") or request.GET.get("id")

        if topic == "payment" and payment_id:
            access_token = getattr(settings, "MERCADO_PAGO_ACCESS_TOKEN", None)
            if not access_token:
                return HttpResponse(status=500)

            sdk = mercadopago.SDK(access_token=access_token)

            try:
                payment_info = sdk.payment().get(payment_id)
                resposta = payment_info.get("response", {})

                external_reference = resposta.get("external_reference")
                mp_status = resposta.get("status")

                if external_reference:
                    pagamento_obj = Pagamento.objects.filter(
                        pk=external_reference
                    ).first()

                    if pagamento_obj:
                        pagamento_obj.mercado_pago_status = mp_status
                        pagamento_obj.mercado_pago_status_detail = (
                            resposta.get("status_detail")
                        )

                        if (
                            mp_status == "approved"
                            and pagamento_obj.status != Pagamento.Status.APROVADO
                        ):
                            with transaction.atomic():
                                pagamento_obj.status = Pagamento.Status.APROVADO

                                contratacao = pagamento_obj.contratacao
                                contratacao.status = (
                                    Contratacao.Status.PAGAMENTO_CONFIRMADO
                                )
                                contratacao.save(
                                    update_fields=["status", "data_atualizacao"]
                                )

                                solicitacao = contratacao.solicitacao
                                solicitacao.status = (
                                    Solicitacao.Status.EM_ANDAMENTO
                                )
                                solicitacao.save(
                                    update_fields=["status", "data_atualizacao"]
                                )

                        pagamento_obj.save(
                            update_fields=[
                                "mercado_pago_status",
                                "mercado_pago_status_detail",
                                "status",
                                "data_atualizacao",
                            ]
                        )
            except Exception:
                return HttpResponse(status=500)

        return HttpResponse(status=200)

    return HttpResponse(status=405)


@csrf_exempt
def webhook_mercadopago(request):
    """Webhook para receber atualizações de pagamento do Mercado Pago."""
    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        # Tenta capturar o ID do pagamento enviado no corpo ou query params
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
        action = data.get("action")
        payment_id = None

        if "data" in data and "id" in data["data"]:
            payment_id = data["data"]["id"]
        elif "id" in request.GET:
            payment_id = request.GET.get("id")

        # Se não for uma notificação de pagamento ou não tiver ID, encerra com OK
        if not payment_id:
            return JsonResponse(
                {"status": "ignored", "reason": "no_payment_id"}, status=200
            )

        # Inicializa a SDK do Mercado Pago
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        payment_info = sdk.payment().get(payment_id)

        if payment_info.get("status") == 200:
            payment_data = payment_info["response"]
            mp_status = payment_data.get("status")

            # Busca o registro de pagamento no banco pelo ID do Mercado Pago ou ID externo
            pagamento = Pagamento.objects.filter(
                mercado_pago_id=payment_id
            ).first()

            if not pagamento:
                # Tenta buscar pelo external_reference se cadastrado
                ext_ref = payment_data.get("external_reference")
                if ext_ref:
                    pagamento = Pagamento.objects.filter(pk=ext_ref).first()

            if pagamento:
                pagamento.mercado_pago_status = mp_status

                # Atualiza status interno
                if mp_status == "approved":
                    pagamento.status = "APROVADO"

                    # Sincroniza a Contratacao e Solicitação associadas
                    contratacao = pagamento.contratacao
                    if contratacao:
                        contratacao.status = "PAGO"
                        contratacao.save()

                        solicitacao = contratacao.solicitacao
                        if solicitacao:
                            solicitacao.status = "CONTRATADA"
                            solicitacao.save()

                elif mp_status in ["cancelled", "rejected", "refunded"]:
                    pagamento.status = "FALHOU"

                pagamento.save()
                return JsonResponse({"status": "success"}, status=200)

        return JsonResponse({"status": "not_processed"}, status=200)

    except Exception as e:
        logger.error(f"Erro no processamento do webhook: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def meus_servicos_profissional(request):
    """Lista os serviços em que o orçamento do profissional foi aceito/pago."""
    profissional = getattr(request.user, "profissional", None)

    if not profissional:
        contratacoes = Contratacao.objects.none()
    else:
        contratacoes = (
            Contratacao.objects.filter(profissional=profissional)
            .select_related(
                "solicitacao",
                "solicitacao__categoria",
                "solicitacao__cliente",
                "solicitacao__cliente__usuario",
            )
            .order_by("-data_contratacao")
        )

    return render(
        request,
        "solicitacoes/meus_servicos_profissional.html",
        {
            "contratacoes": contratacoes,
        },
    )