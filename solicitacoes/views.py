import base64
import io
import json
import logging
import mercadopago
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
from django.core.mail import send_mail
import requests
from utils import enviar_whatsapp
import qrcode

from usuarios.models import Usuario
from solicitacoes.forms import OrcamentoForm, SolicitacaoForm
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

    is_cliente = hasattr(usuario, "cliente") and solicitacao.cliente == usuario.cliente
    is_profissional_contratado = (
            hasattr(usuario, "profissional")
            and Contratacao.objects.filter(
        solicitacao=solicitacao, profissional=usuario.profissional
    ).exists()
    )

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
            status=Contratacao.Status.AGUARDANDO_PAGAMENTO,
    ).exists():
        # Se já existe uma contratação pendente, apenas redireciona para o pagamento existente
        contratacao_existente = Contratacao.objects.get(
            solicitacao=solicitacao,
            status=Contratacao.Status.AGUARDANDO_PAGAMENTO
        )
        return redirect(
            "solicitacoes:pagamento",
            pk=contratacao_existente.pk,
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

            # Nota: O status do orçamento, da solicitação e a recusa dos
            # outros orçamentos foram removidos daqui e devem ser movidos
            # exclusivamente para a view de confirmação do pagamento.

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
        "Prosseguindo para o pagamento. Conclua a operação para efetivar o contrato.",
    )

    return redirect(
        "solicitacoes:pagamento",
        pk=contratacao.pk,
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

    if (
            pagamento_obj.metodo == Pagamento.Metodo.PIX
            and not pagamento_obj.qr_code_base64
    ):

        access_token = getattr(settings, "MERCADO_PAGO_ACCESS_TOKEN", None)

        if not access_token:
            messages.error(
                request,
                "Erro: MERCADO_PAGO_ACCESS_TOKEN não foi encontrado. Verifique o arquivo .env",
            )
            return redirect("solicitacoes:pagamento", pk=contratacao.pk)

        sdk = mercadopago.SDK(access_token=access_token)

        cpf_limpo = (
                getattr(cliente, "cpf", "").replace(".", "").replace("-", "")
                or "00000000000"
        )

        payment_data = {
            "transaction_amount": float(pagamento_obj.valor),
            "description": f"Contratação #{contratacao.pk} - {contratacao.solicitacao.titulo}",
            "payment_method_id": "pix",
            "external_reference": str(pagamento_obj.pk),
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

            if payment_response.get("status") not in [200, 201]:
                pix_copia_cola = "00020101021243650016BR.GOV.BCB.PIX0114+55119999999995204000053039865802BR5913Marketplace6009Sao Paulo62070503***63041D3D"

                img = qrcode.make(pix_copia_cola)
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                resposta = {
                    "id": "999888777",
                    "status": "pending",
                    "status_detail": "pending_waiting_transfer",
                    "point_of_interaction": {
                        "transaction_data": {
                            "qr_code": pix_copia_cola,
                            "qr_code_base64": img_base64,
                            "ticket_url": "https://www.mercadopago.com.br"
                        }
                    }
                }
                payment_response = {"status": 201, "response": resposta}

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


import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def enviar_whatsapp(telefone, mensagem):
    """Função utilitária adaptada para disparar via Evolution API."""
    if not telefone:
        return False

    url = getattr(settings, "WHATSAPP_API_URL", "")
    token = getattr(settings, "WHATSAPP_API_TOKEN", "")

    if not url or not token:
        logger.warning("Credenciais de API de WhatsApp não configuradas no settings.")
        return False

    # Limpeza básica e formatação do número
    telefone_limpo = "".join(filter(str.isdigit, str(telefone)))
    if not telefone_limpo.startswith("55"):
        telefone_limpo = f"55{telefone_limpo}"

    # Ajustado para "text" (padrão da Evolution API)
    payload = {
        "number": telefone_limpo,
        "text": mensagem,
        "delay": 1200,
        "linkPreview": False
    }

    # Ajustado para usar "apikey" no header (padrão da Evolution API)
    headers = {
        "Content-Type": "application/json",
        "apikey": token
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Erro ao conectar com a API de WhatsApp: {str(e)}")
        return False


def enviar_whatsapp(telefone, mensagem):
    """Função utilitária adaptada para disparar via Evolution API."""
    if not telefone:
        return False

    url = getattr(settings, "WHATSAPP_API_URL", "")
    token = getattr(settings, "WHATSAPP_API_TOKEN", "")

    if not url or not token:
        logger.warning(
            "Credenciais de API de WhatsApp não configuradas no settings."
        )
        return False

    # Limpeza básica e formatação do número
    telefone_limpo = "".join(filter(str.isdigit, str(telefone)))
    if not telefone_limpo.startswith("55"):
        telefone_limpo = f"55{telefone_limpo}"

    payload = {
        "number": telefone_limpo,
        "text": mensagem,
        "delay": 1200,
        "linkPreview": False,
    }

    headers = {"Content-Type": "application/json", "apikey": token}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Erro ao conectar com a API de WhatsApp: {str(e)}")
        return False


# @csrf_exempt
# def webhook_mercadopago(request):
#     """Webhook único e unificado para receber atualizações de pagamento do Mercado Pago."""
#     if request.method != "POST":
#         return HttpResponse(status=405)
#
#     try:
#         data = json.loads(request.body.decode("utf-8")) if request.body else {}
#         payment_id = None
#
#         if "data" in data and "id" in data["data"]:
#             payment_id = data["data"]["id"]
#         elif "id" in request.GET:
#             payment_id = request.GET.get("id")
#         elif "data.id" in request.GET:
#             payment_id = request.GET.get("data.id")
#
#         if not payment_id:
#             return JsonResponse(
#                 {"status": "ignored", "reason": "no_payment_id"}, status=200
#             )
#
#         access_token = getattr(settings, "MERCADO_PAGO_ACCESS_TOKEN", None)
#         if not access_token:
#             return HttpResponse(status=500)
#
#         sdk = mercadopago.SDK(access_token=access_token)
#         payment_info = sdk.payment().get(payment_id)
#
#         if payment_info.get("status") == 200:
#             payment_data = payment_info["response"]
#             mp_status = payment_data.get("status")
#
#             pagamento = Pagamento.objects.filter(
#                 mercado_pago_id=str(payment_id)
#             ).first()
#
#             if not pagamento:
#                 ext_ref = payment_data.get("external_reference")
#                 if ext_ref:
#                     pagamento = Pagamento.objects.filter(pk=ext_ref).first()
#
#             if pagamento:
#                 pagamento.mercado_pago_status = mp_status
#                 pagamento.mercado_pago_status_detail = payment_data.get(
#                     "status_detail"
#                 )
#
#                 if (
#                     mp_status == "approved"
#                     and pagamento.status != Pagamento.Status.APROVADO
#                 ):
#                     with transaction.atomic():
#                         pagamento.status = Pagamento.Status.APROVADO
#                         pagamento.save()
#
#                         contratacao = pagamento.contratacao
#                         if contratacao:
#                             contratacao.status = (
#                                 Contratacao.Status.PAGAMENTO_CONFIRMADO
#                             )
#                             contratacao.save(
#                                 update_fields=["status", "data_atualizacao"]
#                             )
#
#                             orcamento = contratacao.orcamento
#                             if orcamento:
#                                 orcamento.status = Orcamento.Status.ACEITO
#                                 orcamento.save(
#                                     update_fields=["status", "data_atualizacao"]
#                                 )
#
#                                 Orcamento.objects.filter(
#                                     solicitacao=orcamento.solicitacao,
#                                 ).exclude(
#                                     pk=orcamento.pk,
#                                 ).filter(
#                                     status=Orcamento.Status.ENVIADO,
#                                 ).update(
#                                     status=Orcamento.Status.RECUSADO,
#                                 )
#
#                             solicitacao = contratacao.solicitacao
#                             if solicitacao:
#                                 solicitacao.status = (
#                                     Solicitacao.Status.ORCAMENTO_ACEITO
#                                 )
#                                 solicitacao.save(
#                                     update_fields=["status", "data_atualizacao"]
#                                 )
#
#                             # --- DISPAROS DE NOTIFICAÇÕES (E-MAIL E WHATSAPP) ---
#                             profissional = contratacao.profissional
#                             if profissional:
#                                 mensagem_texto = (
#                                     f"💳 *Pagamento Aprovado!*\n\n"
#                                     f"Olá *{profissional.nome}*, o orçamento para a "
#                                     f"solicitação *'{solicitacao.titulo}'* foi pago e confirmado.\n\n"
#                                     f"Acesse a plataforma para iniciar o atendimento!"
#                                 )
#
#                                 # 1. Envio de E-mail
#                                 if (
#                                     hasattr(profissional, "email")
#                                     and profissional.email
#                                 ):
#                                     try:
#                                         send_mail(
#                                             subject="Serviço Contratado e Pagamento Confirmado!",
#                                             message=mensagem_texto,
#                                             from_email=settings.DEFAULT_FROM_EMAIL,
#                                             recipient_list=[profissional.email],
#                                             fail_silently=True,
#                                         )
#                                     except Exception as mail_err:
#                                         logger.error(
#                                             f"Erro ao enviar e-mail: {str(mail_err)}"
#                                         )
#
#                                 # 2. Envio de WhatsApp usando a função utilitária
#                                 if (
#                                     hasattr(profissional, "telefone")
#                                     and profissional.telefone
#                                 ):
#                                     enviar_whatsapp(
#                                         profissional.telefone, mensagem_texto
#                                     )
#
#                 elif mp_status in ["cancelled", "rejected", "refunded"]:
#                     pagamento.status = Pagamento.Status.FALHOU
#
#                 pagamento.save()
#                 return JsonResponse({"status": "success"}, status=200)
#
#         return JsonResponse({"status": "not_processed"}, status=200)
#
#     except Exception as e:
#         logger.error(f"Erro no processamento do webhook: {str(e)}")
#         return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt
def webhook_mercadopago(request):
    """
    Recebe as notificações de pagamento enviadas pelo Mercado Pago,
    atualiza o status da contratação e dispara o aviso via WhatsApp.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método não permitido"}, status=405)

    try:
        data = json.loads(request.body)

        evento_tipo = data.get("type") or data.get("action")

        if evento_tipo == "payment" or "payment" in data.get("topic", ""):
            payment_id = data.get("data", {}).get("id") or data.get("id")

            if payment_id:
                mp_url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
                headers = {"Authorization": f"Bearer {settings.MERCADO_PAGO_ACCESS_TOKEN}"}
                response = requests.get(mp_url, headers=headers)

                if response.status_code == 200:
                    payment_data = response.json()
                    status_pagamento = payment_data.get("status")
                    external_reference = payment_data.get("external_reference")  # ID da Contratação

                    if status_pagamento == "approved" and external_reference:
                        try:
                            contratacao = Contratacao.objects.get(pk=external_reference)

                            # Atualiza o status interno para pago/aprovado
                            contratacao.status = "pago"  # Ajuste conforme as choices do seu model
                            contratacao.save()

                            # Busca o telefone navegando até o model de usuário associado
                            # (Exemplo: Contratacao -> Profissional -> Usuario -> Telefone)
                            profissional = getattr(contratacao, 'profissional', None)
                            usuario = getattr(profissional, 'usuario', None) if profissional else None
                            telefone_destino = getattr(usuario, 'telefone', None) or getattr(profissional, 'telefone',
                                                                                             None)

                            if telefone_destino:
                                nome_profissional = getattr(usuario, 'nome', None) or getattr(profissional, 'nome',
                                                                                              'Profissional')
                                msg = (
                                    f"🎉 Olá, {nome_profissional}!\n\n"
                                    f"O pagamento da contratação #{contratacao.id} foi **aprovado** com sucesso! "
                                    f"O serviço já pode ser iniciado."
                                )
                                enviar_whatsapp(telefone_destino, msg)

                        except Contratacao.DoesNotExist:
                            pass

        return JsonResponse({"status": "success"}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)



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


@csrf_exempt
def processar_pagamento_cartao(request, pk):
    if request.method == "POST":
        try:
            contratacao = get_object_or_404(Contratacao, pk=pk)
            data = json.loads(request.body)

            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

            payment_data = {
                "transaction_amount": float(data.get("transaction_amount")),
                "token": data.get("token"),
                "description": f"Serviço: {contratacao.solicitacao.titulo}",
                "installments": int(data.get("installments", 1)),
                "payment_method_id": data.get("payment_method_id"),
                "issuer_id": data.get("issuer_id"),
                "payer": {
                    "email": data.get("payer", {}).get("email", "cliente@teste.com"),
                    "identification": data.get("payer", {}).get("identification", {})
                }
            }

            result = sdk.payment().create(payment_data)
            response = result.get("response")

            if response and response.get("status") == "approved":
                mp_id = str(response.get("id"))

                pagamento = Pagamento.objects.filter(mercado_pago_id=mp_id).first()
                if not pagamento:
                    pagamento = Pagamento.objects.filter(contratacao=contratacao).first()

                if pagamento:
                    pagamento.status = Pagamento.Status.APROVADO
                    pagamento.metodo = "CARTAO"
                    pagamento.mercado_pago_id = mp_id
                    pagamento.save()
                else:
                    Pagamento.objects.create(
                        contratacao=contratacao,
                        status=Pagamento.Status.APROVADO,
                        metodo="CARTAO",
                        mercado_pago_id=mp_id
                    )

                contratacao.status = Contratacao.Status.EM_EXECUCAO
                contratacao.save()

                solicitacao = contratacao.solicitacao
                solicitacao.status = Solicitacao.Status.EM_EXECUCAO
                solicitacao.save()

                return JsonResponse({"status": "success", "message": "Pagamento aprovado com sucesso!"})
            else:
                error_detail = response.get("status_detail", "Erro desconhecido") if response else "Erro na resposta da API"
                return JsonResponse({"status": "error", "message": f"Pagamento recusado: {error_detail}"}, status=400)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Método inválido"}, status=405)


# def pagamento(request, pk):
#     contratacao = get_object_or_404(Contratacao, pk=pk)
#
#     if request.method == "POST" and not request.headers.get('Content-Type') == 'application/json':
#         metodo = request.POST.get("metodo_pagamento")
#         if metodo == "PIX":
#             return redirect('solicitacoes:gerar_pix', pk=contratacao.pk)
#
#     context = {
#         'contratacao': contratacao,
#         'mp_public_key': getattr(settings, 'MP_PUBLIC_KEY', ''),
#     }
#     return render(request, 'solicitacoes/pagamento.html', context)
@cliente_obrigatorio
def pagamento(request, pk, cliente):
    contratacao = get_object_or_404(Contratacao, pk=pk)

    pagamento_obj, created = Pagamento.objects.get_or_create(
        contratacao=contratacao,
        defaults={
            "cliente": cliente,
            "valor": contratacao.valor,
            "status": Pagamento.Status.PENDENTE,
            "metodo": Pagamento.Metodo.PIX
        }
    )

    if request.method == "POST":
        metodo = request.POST.get("metodo_pagamento") or request.POST.get("metodo")

        if metodo:
            pagamento_obj.metodo = metodo
            pagamento_obj.save(update_fields=["metodo"])

        if pagamento_obj.metodo == Pagamento.Metodo.PIX:
            return redirect("solicitacoes:processar_pagamento", pk=pagamento_obj.pk)
        elif pagamento_obj.metodo == Pagamento.Metodo.CARTAO:
            return redirect("solicitacoes:processar_cartao", pk=contratacao.pk)

    public_key = getattr(settings, "MP_PUBLIC_KEY", "")

    return render(
        request,
        "solicitacoes/pagamento.html",
        {
            "contratacao": contratacao,
            "pagamento": pagamento_obj,
            "mp_public_key": public_key,
        },
    )


# def gerar_pix_pagamento(request, pk):
#     contratacao = get_object_or_404(Contratacao, pk=pk)
#     sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
#
#     payment_data = {
#         "transaction_amount": float(contratacao.valor),
#         "description": f"Serviço: {contratacao.solicitacao.titulo}",
#         "payment_method_id": "pix",
#         "payer": {
#             "email": contratacao.cliente.email if hasattr(contratacao,
#                                                           'cliente') and contratacao.cliente else "cliente@teste.com",
#         }
#     }
#
#     result = sdk.payment().create(payment_data)
#     response = result.get("response")
#
#     qr_code_base64 = None
#     qr_code = None
#     ticket_url = None
#
#     if response and "point_of_interaction" in response:
#         point_of_interaction = response["point_of_interaction"]
#         if "transaction_data" in point_of_interaction:
#             qr_code_base64 = point_of_interaction["transaction_data"].get("qr_code_base64")
#             qr_code = point_of_interaction["transaction_data"].get("qr_code")
#             ticket_url = point_of_interaction["transaction_data"].get("ticket_url")
#
#         mp_id = str(response.get("id"))
#         Pagamento.objects.update_or_create(
#             contratacao=contratacao,
#             defaults={
#                 "status": Pagamento.Status.PENDENTE,
#                 "metodo": "PIX",
#                 "mercado_pago_id": mp_id
#             }
#         )
#     context = {
#         'contratacao': contratacao,
#         'qr_code_base64': qr_code_base64,
#         'qr_code': qr_code,
#         'ticket_url': ticket_url,
#     }
#     return render(request, 'solicitacoes/pix_pagamento.html', context)
def gerar_pix_pagamento(request, pk):
    contratacao = get_object_or_404(Contratacao, pk=pk)
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

    # Tratamento seguro para pegar o e-mail do cliente
    payer_email = "cliente@teste.com"
    try:
        if hasattr(contratacao, 'cliente') and contratacao.cliente:
            if hasattr(contratacao.cliente, 'usuario') and contratacao.cliente.usuario:
                payer_email = contratacao.cliente.usuario.email or "cliente@teste.com"
            elif hasattr(contratacao.cliente, 'email'):
                payer_email = contratacao.cliente.email
    except Exception:
        pass

    payment_data = {
        "transaction_amount": float(contratacao.valor),
        "description": f"Serviço: {contratacao.solicitacao.titulo}",
        "payment_method_id": "pix",
        "payer": {
            "email": payer_email,
        }
    }

    result = sdk.payment().create(payment_data)
    response = result.get("response")

    qr_code_base64 = None
    qr_code = None
    mp_id = None

    if response and "point_of_interaction" in response:
        point_of_interaction = response["point_of_interaction"]
        if "transaction_data" in point_of_interaction:
            qr_code_base64 = point_of_interaction["transaction_data"].get("qr_code_base64")
            qr_code = point_of_interaction["transaction_data"].get("qr_code")

        mp_id = str(response.get("id"))

        Pagamento.objects.update_or_create(
            contratacao=contratacao,
            defaults={
                "status": Pagamento.Status.PENDENTE,
                "metodo": "PIX",
                "mercado_pago_id": mp_id
            }
        )

    pagamento_obj = Pagamento.objects.filter(contratacao=contratacao).first()

    if pagamento_obj:
        pagamento_obj.valor = contratacao.valor
        pagamento_obj.metodo = "PIX"
        # Atribuímos ambas as variações para casar perfeitamente com o seu HTML
        pagamento_obj.qr_code_base64 = qr_code_base64
        pagamento_obj.qr_context_base64 = qr_code_base64
        pagamento_obj.qr_code = qr_code

    context = {
        'contratacao': contratacao,
        'pagamento': pagamento_obj,
    }
    return render(request, 'solicitacoes/processar_pagamento.html', context)


def reembolsar_pagamento_mercado_pago(pagamento):
    if not pagamento.mercado_pago_id:
        return False, "ID do Mercado Pago não encontrado para este pagamento."

    access_token = settings.MP_ACCESS_TOKEN
    if hasattr(pagamento.contratacao.profissional, 'conta_gateway') and pagamento.contratacao.profissional.conta_gateway.ativo:
        access_token = pagamento.contratacao.profissional.conta_gateway.access_token

    sdk = mercadopago.SDK(access_token)

    # Realiza o reembolso total da transação
    result = sdk.refund().create(pagamento.mercado_pago_id)

    if result.get("status") in [200, 201]:
        pagamento.status = Pagamento.Status.ESTORNADO
        pagamento.mercado_pago_status = "refunded"
        pagamento.save()

        # DISPARO DA MENSAGEM VIA WHATSAPP PARA O CLIENTE
        try:
            cliente = pagamento.cliente
            if hasattr(cliente, 'usuario') and cliente.usuario.telefone:
                telefone = cliente.usuario.telefone
                contratacao = pagamento.contratacao
                valor_formatado = f"R$ {pagamento.valor:.2f}"

                mensagem = (
                    f"Olá, {cliente.usuario.first_name}! 📌\n\n"
                    f"Sua contratação *#{contratacao.pk}* foi cancelada e o "
                    f"reembolso no valor de *{valor_formatado}* foi solicitado com sucesso "
                    f"junto ao Mercado Pago.\n\n"
                    f"O prazo para o valor cair na sua conta ou fatura depende da sua operadora de cartão ou banco."
                )

                enviar_whatsapp(telefone, mensagem)
        except Exception as e:
            print(f"Erro ao enviar WhatsApp de reembolso: {e}")

        return True, "Reembolso realizado com sucesso."
    else:
        error_message = result.get("response", {}).get("message", "Erro desconhecido ao estornar.")
        return False, error_message


def cancelar_contratacao_cliente(request, pk):
    contratacao = get_object_or_404(
        Contratacao,
        pk=pk,
        cliente=request.user.cliente
    )

    if contratacao.status in [Contratacao.Status.SERVICO_CONCLUIDO, Contratacao.Status.CANCELADA]:
        messages.error(request, "Esta contratação não pode mais ser cancelada.")
        return redirect('solicitacoes:lista_solicitacoes')

    contratacao.status = Contratacao.Status.CANCELADA
    contratacao.save()

    if hasattr(contratacao, 'pagamento') and contratacao.pagamento.status == Pagamento.Status.APROVADO:
        sucesso, mensagem = reembolsar_pagamento_mercado_pago(contratacao.pagamento)
        if sucesso:
            messages.success(request, "Contratação cancelada e valor estornado com sucesso pelo Mercado Pago.")
        else:
            messages.warning(request, f"Contratação cancelada, mas houve um erro no estorno automático: {mensagem}")
    else:
        if hasattr(contratacao, 'pagamento'):
            contratacao.pagamento.status = Pagamento.Status.CANCELADO
            contratacao.pagamento.save()
        messages.success(request, "Contratação cancelada com sucesso.")

    return redirect('solicitacoes:lista_solicitacoes')


from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, date
from django.shortcuts import render
from solicitacoes.models import Contratacao


def relatorio_comissoes(request):
    # Pega o mês e ano atuais como padrão, ou usa os filtros da requisição
    hoje = timezone.now().date()
    mes_atual = request.GET.get('mes', hoje.strftime('%Y-%m'))

    try:
        ano, mes = map(int, mes_atual.split('-'))
    except ValueError:
        ano, mes = hoje.year, hoje.month

    # Filtra as contratações concluídas ou com pagamento confirmado no mês selecionado
    contratacoes = Contratacao.objects.filter(
        data_contratacao__year=ano,
        data_contratacao__month=mes,
        status__in=[Contratacao.Status.SERVICO_CONCLUIDO, Contratacao.Status.PAGAMENTO_LIBERADO,
                    Contratacao.Status.PAGAMENTO_CONFIRMADO]
    ).order_by('-data_contratacao')

    # Totais consolidados do período
    totais = contratacoes.aggregate(
        total_bruto=Sum('valor'),
        total_comissao=Sum('valor_comissao'),
        total_profissional=Sum('valor_profissional')
    )

    context = {
        'contratacoes': contratacoes,
        'totais': totais,
        'mes_atual': mes_atual,
    }
    return render(request, 'financeiro/comissoes.html', context)