import uuid
import requests
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
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, date, timedelta
import qrcode


from usuarios.models import Usuario, Profissional
from solicitacoes.forms import OrcamentoForm, SolicitacaoForm
from categorias.models import Categoria
from .models import (
    Contratacao,
    Orcamento,
    Pagamento,
    Solicitacao,
    SolicitacaoFoto,
    ContaGateway,
)

logger = logging.getLogger(__name__)


def obter_access_token_mercado_pago(conta_gateway):
    """
    Retorna um Access Token OAuth válido para a ContaGateway.

    Se o token estiver vencido ou a até 5 minutos do vencimento,
    renova automaticamente usando o refresh_token e persiste as
    novas credenciais retornadas pelo Mercado Pago.

    Retorno:
        (access_token, None) em caso de sucesso
        (None, mensagem_erro) em caso de falha
    """

    if not conta_gateway:
        return None, "Conta Mercado Pago não encontrada."

    if not conta_gateway.ativo:
        return None, "A conta Mercado Pago está desativada."

    access_token = conta_gateway.access_token

    if not access_token:
        return None, (
            "A conta Mercado Pago não possui Access Token válido."
        )

    # Sem data de expiração conhecida, preservamos o token atual.
    if not conta_gateway.token_expires_at:
        return access_token, None

    margem_renovacao = timezone.now() + timedelta(minutes=5)

    if conta_gateway.token_expires_at > margem_renovacao:
        return access_token, None

    refresh_token = conta_gateway.refresh_token

    if not refresh_token:
        return None, (
            "A conexão Mercado Pago expirou e não possui "
            "Refresh Token para renovação automática."
        )

    client_id = getattr(settings, "MERCADO_PAGO_CLIENT_ID", None)
    client_secret = getattr(
        settings,
        "MERCADO_PAGO_CLIENT_SECRET",
        None,
    )

    if not client_id or not client_secret:
        return None, (
            "As credenciais OAuth do Mercado Pago não estão "
            "configuradas corretamente no servidor."
        )

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    try:
        response = requests.post(
            "https://api.mercadopago.com/oauth/token",
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": (
                    "application/x-www-form-urlencoded"
                ),
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        logger.exception(
            "Falha ao renovar OAuth Mercado Pago. ContaGateway=%s: %s",
            conta_gateway.pk,
            exc,
        )
        return None, (
            "Não foi possível renovar a conexão com o Mercado Pago."
        )

    try:
        dados = response.json()
    except ValueError:
        dados = {}

    if not response.ok:
        detalhe = (
            dados.get("message")
            or dados.get("error")
            or f"HTTP {response.status_code}"
        )
        logger.error(
            "Mercado Pago recusou renovação OAuth. "
            "ContaGateway=%s HTTP=%s detalhe=%s",
            conta_gateway.pk,
            response.status_code,
            detalhe,
        )
        return None, (
            "Não foi possível renovar automaticamente a conexão "
            "Mercado Pago do profissional."
        )

    novo_access_token = dados.get("access_token")
    novo_refresh_token = dados.get("refresh_token")
    expires_in = dados.get("expires_in")

    if not novo_access_token:
        logger.error(
            "Renovação OAuth sem Access Token. ContaGateway=%s",
            conta_gateway.pk,
        )
        return None, (
            "O Mercado Pago não retornou uma credencial válida "
            "na renovação da conexão."
        )

    nova_expiracao = None
    if expires_in:
        try:
            nova_expiracao = (
                timezone.now()
                + timedelta(seconds=int(expires_in))
            )
        except (TypeError, ValueError):
            nova_expiracao = None

    conta_gateway.access_token = novo_access_token

    # O Mercado Pago pode rotacionar o refresh token.
    # Quando vier um novo, substituímos o anterior.
    if novo_refresh_token:
        conta_gateway.refresh_token = novo_refresh_token

    conta_gateway.token_expires_at = nova_expiracao
    conta_gateway.save(
        update_fields=[
            "access_token",
            "refresh_token",
            "token_expires_at",
            "data_atualizacao",
        ]
    )

    logger.info(
        "OAuth Mercado Pago renovado automaticamente. ContaGateway=%s",
        conta_gateway.pk,
    )

    return novo_access_token, None


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


def _notificar_profissionais_nova_solicitacao(solicitacao):
    """Notifica profissionais elegíveis da mesma categoria, cidade e UF."""
    profissionais = (
        Profissional.objects.filter(
            servicos__categoria=solicitacao.categoria,
            servicos__ativo=True,
            ativo=True,
            aprovado=True,
            cidade__iexact=(solicitacao.cidade or "").strip(),
            estado__iexact=(solicitacao.estado or "").strip(),
        )
        .select_related("usuario")
        .distinct()
    )

    categoria = getattr(solicitacao.categoria, "nome", str(solicitacao.categoria))
    descricao = (solicitacao.descricao or "").strip()
    if len(descricao) > 300:
        descricao = descricao[:297].rstrip() + "..."

    for profissional in profissionais:
        usuario = profissional.usuario
        nome = (
            profissional.nome_profissional
            or usuario.first_name
            or "profissional"
        )

        mensagem = (
            f"Olá, {nome}!\n\n"
            "Uma nova solicitação compatível com seus serviços foi publicada "
            "no ChamaPro.\n\n"
            f"Solicitação #{solicitacao.pk}\n"
            f"Categoria: {categoria}\n"
            f"Serviço: {solicitacao.titulo}\n"
        )

        if descricao:
            mensagem += f"Descrição: {descricao}\n"

        mensagem += (
            f"Local: {solicitacao.cidade} - {solicitacao.estado}\n\n"
            "Acesse o ChamaPro para visualizar a solicitação e enviar seu orçamento."
        )

        if usuario.telefone:
            try:
                enviar_whatsapp(usuario.telefone, mensagem)
            except Exception as exc:
                logger.exception(
                    "Erro ao enviar WhatsApp da Solicitação %s ao profissional %s: %s",
                    solicitacao.pk,
                    profissional.pk,
                    exc,
                )

        if usuario.email:
            try:
                send_mail(
                    subject=f"Nova Solicitação #{solicitacao.pk} - ChamaPro Serviços",
                    message=mensagem,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[usuario.email],
                    fail_silently=False,
                )
            except Exception as exc:
                logger.exception(
                    "Erro ao enviar e-mail da Solicitação %s ao profissional %s: %s",
                    solicitacao.pk,
                    profissional.pk,
                    exc,
                )


def _notificar_cliente_novo_orcamento(orcamento):
    """Notifica o cliente quando um profissional envia um novo orçamento."""
    solicitacao = orcamento.solicitacao
    cliente = solicitacao.cliente
    usuario = cliente.usuario
    profissional = orcamento.profissional

    nome_cliente = usuario.first_name or "cliente"
    nome_profissional = (
        profissional.nome_profissional
        or profissional.usuario.first_name
        or "Profissional"
    )
    valor_formatado = f"R$ {orcamento.valor:.2f}".replace(".", ",")

    mensagem = (
        f"Olá, {nome_cliente}!\n\n"
        f"Você recebeu um novo orçamento para a Solicitação #{solicitacao.pk}.\n\n"
        f"Serviço: {solicitacao.titulo}\n"
        f"Profissional: {nome_profissional}\n"
        f"Valor: {valor_formatado}\n\n"
        "Acesse o ChamaPro para visualizar os orçamentos recebidos."
    )

    if usuario.telefone:
        try:
            enviar_whatsapp(usuario.telefone, mensagem)
        except Exception as exc:
            logger.exception(
                "Erro ao enviar WhatsApp do Orçamento %s ao cliente %s: %s",
                orcamento.pk,
                cliente.pk,
                exc,
            )

    if usuario.email:
        try:
            send_mail(
                subject=f"Novo orçamento para a Solicitação #{solicitacao.pk} - ChamaPro Serviços",
                message=mensagem,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[usuario.email],
                fail_silently=False,
            )
        except Exception as exc:
            logger.exception(
                "Erro ao enviar e-mail do Orçamento %s ao cliente %s: %s",
                orcamento.pk,
                cliente.pk,
                exc,
            )


def _notificar_profissional_orcamento_contratado(contratacao):
    """Notifica o profissional após a confirmação do pagamento."""
    solicitacao = contratacao.solicitacao
    profissional = contratacao.profissional
    usuario = profissional.usuario

    nome = (
        profissional.nome_profissional
        or usuario.first_name
        or "profissional"
    )
    valor_formatado = f"R$ {contratacao.valor:.2f}".replace(".", ",")

    mensagem = (
        f"Olá, {nome}!\n\n"
        f"Seu orçamento para a Solicitação #{solicitacao.pk} foi contratado pelo cliente.\n\n"
        f"Serviço: {solicitacao.titulo}\n"
        f"Valor: {valor_formatado}\n"
        f"Local: {solicitacao.cidade} - {solicitacao.estado}\n\n"
        "O pagamento foi confirmado e a contratação está efetivada. "
        "Acesse o ChamaPro para acompanhar o serviço."
    )

    if usuario.telefone:
        try:
            enviar_whatsapp(usuario.telefone, mensagem)
        except Exception as exc:
            logger.exception(
                "Erro ao enviar WhatsApp da contratação %s ao profissional %s: %s",
                contratacao.pk,
                profissional.pk,
                exc,
            )

    if usuario.email:
        try:
            send_mail(
                subject=(
                    f"Contratação confirmada - Solicitação #{solicitacao.pk} "
                    "- ChamaPro Serviços"
                ),
                message=mensagem,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[usuario.email],
                fail_silently=False,
            )
        except Exception as exc:
            logger.exception(
                "Erro ao enviar e-mail da contratação %s ao profissional %s: %s",
                contratacao.pk,
                profissional.pk,
                exc,
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

            _notificar_profissionais_nova_solicitacao(solicitacao)

            messages.success(
                request,
                "Sua solicitação foi criada com sucesso.",
            )

            return redirect(
                "solicitacoes:detalhe",
                pk=solicitacao.pk,
            )

    else:

        categoria_nome = request.GET.get(
            "categoria",
            ""
        ).strip()

        if categoria_nome:

            try:

                categoria = Categoria.objects.get(
                    nome__iexact=categoria_nome
                )

                form = SolicitacaoForm(
                    initial={
                        "categoria": categoria,
                        "titulo": categoria.descricao or "",

                        # Dados cadastrados no perfil do cliente
                        "cidade": cliente.cidade,
                        "estado": cliente.estado,
                        "endereco": cliente.endereco,
                        "numero": cliente.numero,
                        "bairro": cliente.bairro,
                        "cep": cliente.cep,
                    }
                )

            except Categoria.DoesNotExist:

                form = SolicitacaoForm(
                    initial={
                        "cidade": cliente.cidade,
                        "estado": cliente.estado,
                        "endereco": cliente.endereco,
                        "numero": cliente.numero,
                        "bairro": cliente.bairro,
                        "cep": cliente.cep,
                    }
                )

        else:

            form = SolicitacaoForm(
                initial={
                    "cidade": cliente.cidade,
                    "estado": cliente.estado,
                    "endereco": cliente.endereco,
                    "numero": cliente.numero,
                    "bairro": cliente.bairro,
                    "cep": cliente.cep,
                }
            )

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
    """
    Compatibilidade com o fluxo antigo.

    Alguns templates/URLs ainda utilizam aceitar_orcamento.
    Esta view não cria mais a contratação diretamente.

    Ela identifica o orçamento selecionado e encaminha o
    processamento para contratar_orcamento, que é o fluxo
    oficial de contratação/pagamento.
    """

    if request.method != "POST":
        return redirect(
            "solicitacoes:orcamentos",
            pk=pk,
        )

    solicitacao = get_object_or_404(
        Solicitacao,
        pk=pk,
        cliente=cliente,
    )

    orcamento_id = request.POST.get("orcamento_id")

    if not orcamento_id:
        messages.error(
            request,
            "Nenhum orçamento foi selecionado.",
        )

        return redirect(
            "solicitacoes:orcamentos",
            pk=solicitacao.pk,
        )

    orcamento = get_object_or_404(
        Orcamento,
        pk=orcamento_id,
        solicitacao=solicitacao,
        status=Orcamento.Status.ENVIADO,
    )

    return contratar_orcamento(
        request,
        cliente=cliente,
        pk=orcamento.pk,
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

            _notificar_cliente_novo_orcamento(orcamento)

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
def processar_pagamento(request, cliente, pk):
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

    # ==========================================================
    # MODO DE TESTE
    # ==========================================================
    # A Order de teste do Mercado Pago pode mudar sozinha para
    # processed/accredited poucos segundos após a criação. Isso
    # não representa um PIX efetivamente pago pelo cliente.
    #
    # Por isso, no modo de teste NÃO sincronizamos a aprovação
    # local a partir da Order ao reabrir esta página. A aprovação
    # de teste deve ser explícita, pela rotina pagamento_teste.
    # O fluxo REAL continua sendo sincronizado normalmente.
    # ==========================================================

    modo_teste = getattr(
        settings,
        "MP_PAGAMENTO_TESTE",
        False,
    )

    # ==========================================================
    # PAGAMENTO JÁ APROVADO
    # ==========================================================

    if pagamento_obj.status == Pagamento.Status.APROVADO:
        messages.info(
            request,
            "Este pagamento já foi aprovado.",
        )

        return redirect(
            "solicitacoes:detalhe",
            pk=contratacao.solicitacao.pk,
        )

    # ==========================================================
    # PIX
    # ==========================================================

    if (
        pagamento_obj.metodo == Pagamento.Metodo.PIX
        and not pagamento_obj.qr_code_base64
    ):

        modo_teste = getattr(
            settings,
            "MP_PAGAMENTO_TESTE",
            False,
        )

        # ======================================================
        # MODO DE TESTE
        #
        # Usa:
        #   POST /v1/orders
        #   Access Token das credenciais de teste
        #
        # Não utiliza o OAuth do profissional para criar
        # a cobrança.
        #
        # APRO faz o Mercado Pago simular a aprovação do PIX.
        # ======================================================

        if modo_teste:

            access_token = getattr(
                settings,
                "MERCADO_PAGO_TEST_ACCESS_TOKEN",
                "",
            )

            if not access_token:
                messages.error(
                    request,
                    "O Access Token de teste do Mercado Pago "
                    "não está configurado.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            # --------------------------------------------------
            # PAYLOAD DA ORDER DE TESTE
            # --------------------------------------------------

            order_data = {
                "type": "online",

                "external_reference": str(
                    pagamento_obj.pk
                ),

                "total_amount": (
                    f"{pagamento_obj.valor:.2f}"
                ),

                "payer": {
                    "email": "test_user_br@testuser.com",
                    "first_name": "APRO",
                },

                "transactions": {
                    "payments": [
                        {
                            "amount": (
                                f"{pagamento_obj.valor:.2f}"
                            ),

                            "payment_method": {
                                "id": "pix",
                                "type": "bank_transfer",
                            },
                        }
                    ]
                },
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": str(uuid.uuid4()),
            }

            # --------------------------------------------------
            # LOG
            # --------------------------------------------------

            print(
                "=== PIX MERCADO PAGO - MODO TESTE ==="
            )

            print(
                {
                    "modo": "TESTE",
                    "endpoint": "/v1/orders",
                    "pagamento_local_id": pagamento_obj.pk,
                    "contratacao_id": contratacao.pk,
                    "valor": str(pagamento_obj.valor),
                    "payer_email": (
                        "test_user_br@testuser.com"
                    ),
                    "cenario": "APRO",
                }
            )

            # --------------------------------------------------
            # CRIA ORDER
            # --------------------------------------------------

            try:
                response = requests.post(
                    "https://api.mercadopago.com/v1/orders",
                    json=order_data,
                    headers=headers,
                    timeout=30,
                )

            except requests.RequestException as exc:
                logger.exception(
                    "Erro de comunicação com Mercado Pago "
                    "no modo de teste: %s",
                    exc,
                )

                messages.error(
                    request,
                    "Erro ao gerar PIX de teste: "
                    "falha na comunicação com o Mercado Pago.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            print(
                "=== RESPOSTA MERCADO PAGO /v1/orders ==="
            )
            print("HTTP:", response.status_code)
            print(response.text)

            try:
                resposta = response.json()
            except ValueError:
                resposta = {}

            if response.status_code not in (200, 201):
                mensagem_erro = (
                    resposta.get("message")
                    or resposta.get("error")
                    or "Não foi possível gerar o PIX de teste."
                )

                logger.error(
                    "Mercado Pago recusou PIX de teste. "
                    "HTTP %s - %s",
                    response.status_code,
                    response.text,
                )

                messages.error(
                    request,
                    f"Erro ao gerar PIX de teste: "
                    f"{mensagem_erro}",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            # --------------------------------------------------
            # ORDER ID
            # --------------------------------------------------

            order_id = resposta.get("id")

            if not order_id:
                logger.error(
                    "Mercado Pago criou Order de teste "
                    "sem retornar ID: %s",
                    resposta,
                )

                messages.error(
                    request,
                    "O Mercado Pago não retornou o "
                    "identificador da cobrança de teste.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            order_id = str(order_id)

            # --------------------------------------------------
            # PRIMEIRO PAYMENT DA ORDER
            # --------------------------------------------------

            transactions_data = (
                resposta.get("transactions") or {}
            )

            payments = (
                transactions_data.get("payments") or []
            )

            if not payments:
                logger.error(
                    "Order PIX de teste sem payments: %s",
                    resposta,
                )

                messages.error(
                    request,
                    "O Mercado Pago criou a cobrança, "
                    "mas não retornou o pagamento PIX.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            payment_mp = payments[0]

            payment_id = payment_mp.get("id")

            if not payment_id:
                logger.error(
                    "Order PIX de teste sem Payment ID: %s",
                    resposta,
                )

                messages.error(
                    request,
                    "O Mercado Pago não retornou o "
                    "identificador do pagamento PIX.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            payment_id = str(payment_id)

            # --------------------------------------------------
            # STATUS
            # --------------------------------------------------

            mp_status = resposta.get("status")
            mp_status_detail = resposta.get(
                "status_detail"
            )

            # --------------------------------------------------
            # DADOS PIX
            # --------------------------------------------------

            payment_method = (
                payment_mp.get("payment_method") or {}
            )

            qr_code = payment_method.get("qr_code")
            qr_code_base64 = payment_method.get(
                "qr_code_base64"
            )
            ticket_url = payment_method.get(
                "ticket_url"
            )

            # --------------------------------------------------
            # SALVA IDENTIFICADORES
            #
            # mercado_pago_id:
            #     ORDER ID no modo de teste
            #
            # identificador_transacao:
            #     PAYMENT ID da order
            # --------------------------------------------------

            pagamento_obj.mercado_pago_id = order_id

            pagamento_obj.identificador_transacao = (
                payment_id
            )

            pagamento_obj.mercado_pago_status = (
                mp_status
            )

            pagamento_obj.mercado_pago_status_detail = (
                mp_status_detail
            )

            pagamento_obj.qr_code = qr_code
            pagamento_obj.qr_code_base64 = (
                qr_code_base64
            )
            pagamento_obj.ticket_url = ticket_url

            # --------------------------------------------------
            # STATUS LOCAL INICIAL
            #
            # Normalmente:
            #
            # action_required / waiting_transfer
            #
            # Alguns segundos depois o APRO passa para:
            #
            # processed / accredited
            # --------------------------------------------------

            # No ambiente de teste a Order pode chegar a
            # processed/accredited automaticamente, sem que um PIX
            # tenha sido efetivamente pago. Portanto, a criação do
            # QR Code sempre começa como PENDENTE no banco local.
            # A aprovação de teste será feita explicitamente pela
            # rotina pagamento_teste.
            pagamento_obj.status = Pagamento.Status.PENDENTE
            pagamento_obj.data_pagamento = None

            pagamento_obj.save()

            print(
                "=== PIX DE TESTE CRIADO ==="
            )
            print("ORDER ID:", order_id)
            print("PAYMENT ID:", payment_id)
            print("STATUS:", mp_status)
            print(
                "STATUS DETAIL:",
                mp_status_detail,
            )
            print(
                "QR CODE:",
                bool(qr_code),
            )
            print(
                "QR CODE BASE64:",
                bool(qr_code_base64),
            )

        # ======================================================
        # MODO REAL
        #
        # Split 1:1
        #
        # Usa:
        #   POST /v1/payments
        #   Access Token OAuth do PROFISSIONAL
        #   application_fee
        # ======================================================

        else:

            # --------------------------------------------------
            # CONTA MERCADO PAGO DO PROFISSIONAL
            # --------------------------------------------------

            conta_gateway = ContaGateway.objects.filter(
                profissional=contratacao.profissional,
                gateway=ContaGateway.Gateway.MERCADO_PAGO,
                ativo=True,
            ).first()

            if not conta_gateway:
                messages.error(
                    request,
                    "O profissional ainda não conectou "
                    "sua conta do Mercado Pago.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            # --------------------------------------------------
            # ACCESS TOKEN OAUTH VÁLIDO / RENOVAÇÃO AUTOMÁTICA
            # --------------------------------------------------

            access_token, erro_token = (
                obter_access_token_mercado_pago(conta_gateway)
            )

            if not access_token:
                messages.error(
                    request,
                    erro_token
                    or "Não foi possível validar a conexão Mercado Pago.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            # --------------------------------------------------
            # E-MAIL DO PAGADOR
            # --------------------------------------------------

            payer_email = None

            try:
                payer_email = (
                    pagamento_obj.cliente.usuario.email
                )
            except Exception:
                pass

            if not payer_email:
                messages.error(
                    request,
                    "O cliente não possui um e-mail "
                    "válido para o pagamento.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            # --------------------------------------------------
            # PAYLOAD REAL
            # --------------------------------------------------

            payment_data = {
                "transaction_amount": float(
                    pagamento_obj.valor
                ),

                "description": (
                    f"ChamaPro - "
                    f"{contratacao.solicitacao.titulo}"
                ),

                "payment_method_id": "pix",

                "payer": {
                    "email": payer_email,
                },

                "external_reference": str(
                    pagamento_obj.pk
                ),

                "application_fee": float(
                    contratacao.valor_comissao
                ),
            }

            headers = {
                "Authorization": (
                    f"Bearer {access_token}"
                ),
                "Content-Type": "application/json",
                "X-Idempotency-Key": str(
                    uuid.uuid4()
                ),
            }

            # --------------------------------------------------
            # LOG
            # --------------------------------------------------

            print(
                "=== PIX MERCADO PAGO - MODO REAL ==="
            )

            print(
                {
                    "modo": "REAL",
                    "endpoint": "/v1/payments",
                    "transaction_amount": (
                        payment_data[
                            "transaction_amount"
                        ]
                    ),
                    "external_reference": (
                        payment_data[
                            "external_reference"
                        ]
                    ),
                    "payment_method_id": "pix",
                    "application_fee": (
                        payment_data[
                            "application_fee"
                        ]
                    ),
                    "payer_email": payer_email,
                    "profissional_id": (
                        contratacao.profissional_id
                    ),
                    "conta_gateway_id": (
                        conta_gateway.pk
                    ),
                }
            )

            # --------------------------------------------------
            # CRIA PAYMENT
            # --------------------------------------------------

            try:
                response = requests.post(
                    "https://api.mercadopago.com/v1/payments",
                    json=payment_data,
                    headers=headers,
                    timeout=30,
                )

            except requests.RequestException as exc:
                logger.exception(
                    "Erro de comunicação com "
                    "Mercado Pago: %s",
                    exc,
                )

                messages.error(
                    request,
                    "Erro ao gerar cobrança PIX: "
                    "falha na comunicação com "
                    "o Mercado Pago.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            print(
                "=== RESPOSTA MERCADO PAGO "
                "/v1/payments ==="
            )
            print("HTTP:", response.status_code)
            print(response.text)

            try:
                resposta = response.json()
            except ValueError:
                resposta = {}

            if response.status_code not in (200, 201):
                mensagem_erro = (
                    resposta.get("message")
                    or resposta.get("error")
                    or (
                        "Não foi possível gerar "
                        "a cobrança PIX."
                    )
                )

                logger.error(
                    "Mercado Pago recusou criação "
                    "do PIX. HTTP %s - %s",
                    response.status_code,
                    response.text,
                )

                messages.error(
                    request,
                    f"Erro ao gerar cobrança PIX: "
                    f"{mensagem_erro}",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            # --------------------------------------------------
            # PAYMENT ID
            # --------------------------------------------------

            payment_id = resposta.get("id")

            if not payment_id:
                logger.error(
                    "Mercado Pago criou pagamento "
                    "sem retornar ID: %s",
                    resposta,
                )

                messages.error(
                    request,
                    "O Mercado Pago não retornou "
                    "o identificador do pagamento.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            payment_id = str(payment_id)

            # --------------------------------------------------
            # STATUS
            # --------------------------------------------------

            mp_status = resposta.get("status")

            mp_status_detail = resposta.get(
                "status_detail"
            )

            # --------------------------------------------------
            # DADOS PIX
            # --------------------------------------------------

            point_of_interaction = (
                resposta.get(
                    "point_of_interaction"
                ) or {}
            )

            transaction_data = (
                point_of_interaction.get(
                    "transaction_data"
                ) or {}
            )

            qr_code = transaction_data.get(
                "qr_code"
            )

            qr_code_base64 = transaction_data.get(
                "qr_code_base64"
            )

            ticket_url = transaction_data.get(
                "ticket_url"
            )

            if not qr_code and not qr_code_base64:
                logger.error(
                    "Pagamento PIX criado, mas "
                    "Mercado Pago não retornou "
                    "QR Code. Resposta: %s",
                    resposta,
                )

                messages.error(
                    request,
                    "O pagamento foi criado, mas "
                    "o Mercado Pago não retornou "
                    "o QR Code PIX.",
                )

                return redirect(
                    "solicitacoes:pagamento",
                    pk=contratacao.pk,
                )

            # --------------------------------------------------
            # SALVA PAYMENT REAL
            # --------------------------------------------------

            pagamento_obj.mercado_pago_id = (
                payment_id
            )

            pagamento_obj.identificador_transacao = (
                payment_id
            )

            pagamento_obj.mercado_pago_status = (
                mp_status
            )

            pagamento_obj.mercado_pago_status_detail = (
                mp_status_detail
            )

            pagamento_obj.qr_code = qr_code

            pagamento_obj.qr_code_base64 = (
                qr_code_base64
            )

            pagamento_obj.ticket_url = ticket_url

            # --------------------------------------------------
            # STATUS LOCAL
            # --------------------------------------------------

            if mp_status == "approved":
                pagamento_obj.status = (
                    Pagamento.Status.APROVADO
                )

                if hasattr(
                    pagamento_obj,
                    "data_pagamento",
                ):
                    pagamento_obj.data_pagamento = (
                        timezone.now()
                    )

            elif mp_status in (
                "in_process",
                "in_mediation",
            ):
                pagamento_obj.status = (
                    Pagamento.Status.PROCESSANDO
                )

            elif mp_status in (
                "rejected",
                "cancelled",
            ):
                pagamento_obj.status = (
                    Pagamento.Status.RECUSADO
                )

            else:
                pagamento_obj.status = (
                    Pagamento.Status.PENDENTE
                )

            pagamento_obj.save()

        # ======================================================
        # PAGAMENTO JÁ APROVADO NA RESPOSTA
        #
        # Funciona para:
        #
        # REAL:
        #   approved
        #
        # TESTE:
        #   processed / accredited
        #
        # Normalmente o PIX de teste inicialmente retorna
        # waiting_transfer. A confirmação posterior será
        # tratada pelo webhook/consulta.
        # ======================================================

        pagamento_aprovado = False

        if modo_teste:
            # A aprovação automática da Order de teste é ignorada.
            # Somente uma simulação explícita altera o estado local.
            pagamento_aprovado = False
        else:
            pagamento_aprovado = (
                mp_status == "approved"
            )

        if pagamento_aprovado:

            contratacao_ja_confirmada = contratacao.status in [
                Contratacao.Status.PAGAMENTO_CONFIRMADO,
                Contratacao.Status.EM_EXECUCAO,
                Contratacao.Status.SERVICO_CONCLUIDO,
                Contratacao.Status.PAGAMENTO_LIBERADO,
            ]

            with transaction.atomic():

                contratacao.status = (
                    Contratacao.Status.PAGAMENTO_CONFIRMADO
                )

                contratacao.save(
                    update_fields=[
                        "status",
                        "data_atualizacao",
                    ]
                )

                solicitacao = contratacao.solicitacao

                solicitacao.status = (
                    Solicitacao.Status.EM_EXECUCAO
                )

                solicitacao.save(
                    update_fields=[
                        "status",
                        "data_atualizacao",
                    ]
                )

                orcamento = contratacao.orcamento

                if orcamento:
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
                        status=Orcamento.Status.ENVIADO,
                    ).exclude(
                        pk=orcamento.pk,
                    ).update(
                        status=Orcamento.Status.RECUSADO,
                    )

            if not contratacao_ja_confirmada:
                _notificar_profissional_orcamento_contratado(contratacao)

    # ==========================================================
    # EXIBE O QR CODE
    # ==========================================================

    return render(
        request,
        "solicitacoes/processar_pagamento.html",
        {
            "pagamento": pagamento_obj,
            "contratacao": contratacao,
        },
    )


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


@profissional_obrigatorio
def concluir_servico(request, profissional, pk):
    """
    Permite ao profissional contratado informar que terminou o serviço.

    A conclusão informada pelo profissional NÃO encerra definitivamente
    a solicitação. O cliente ainda deverá confirmar a conclusão.
    """

    contratacao = get_object_or_404(
        Contratacao.objects.select_related(
            "solicitacao",
            "profissional",
            "pagamento",
        ),
        pk=pk,
        profissional=profissional,
    )

    solicitacao = contratacao.solicitacao

    if request.method != "POST":
        return redirect(
            "solicitacoes:detalhe_servico_profissional",
            pk=contratacao.pk,
        )

    # ----------------------------------------------------------
    # O serviço somente pode ser concluído depois do pagamento
    # ----------------------------------------------------------

    try:
        pagamento = contratacao.pagamento
    except Pagamento.DoesNotExist:
        messages.error(
            request,
            "Não existe pagamento vinculado a esta contratação.",
        )

        return redirect(
            "solicitacoes:detalhe_servico_profissional",
            pk=contratacao.pk,
        )

    if pagamento.status != Pagamento.Status.APROVADO:
        messages.error(
            request,
            "O serviço não pode ser concluído porque o pagamento "
            "ainda não foi confirmado.",
        )

        return redirect(
            "solicitacoes:detalhe_servico_profissional",
            pk=contratacao.pk,
        )

    # ----------------------------------------------------------
    # Valida o estado atual da contratação
    # ----------------------------------------------------------

    if contratacao.status == Contratacao.Status.SERVICO_CONCLUIDO:
        messages.info(
            request,
            "Você já informou a conclusão deste serviço.",
        )

        return redirect(
            "solicitacoes:detalhe_servico_profissional",
            pk=contratacao.pk,
        )

    if contratacao.status == Contratacao.Status.PAGAMENTO_LIBERADO:
        messages.info(
            request,
            "Este serviço já foi concluído pelo cliente.",
        )

        return redirect(
            "solicitacoes:detalhe_servico_profissional",
            pk=contratacao.pk,
        )

    if contratacao.status == Contratacao.Status.CANCELADA:
        messages.error(
            request,
            "Uma contratação cancelada não pode ser concluída.",
        )

        return redirect(
            "solicitacoes:detalhe_servico_profissional",
            pk=contratacao.pk,
        )

    if contratacao.status not in [
        Contratacao.Status.PAGAMENTO_CONFIRMADO,
        Contratacao.Status.EM_EXECUCAO,
    ]:
        messages.error(
            request,
            "Esta contratação não está em uma situação que permita "
            "informar a conclusão do serviço.",
        )

        return redirect(
            "solicitacoes:detalhe_servico_profissional",
            pk=contratacao.pk,
        )

    # ----------------------------------------------------------
    # Marca como concluído pelo profissional
    # ----------------------------------------------------------

    with transaction.atomic():

        contratacao.status = Contratacao.Status.SERVICO_CONCLUIDO

        contratacao.save(
            update_fields=[
                "status",
                "data_atualizacao",
            ]
        )

        # A solicitação continua EM_EXECUCAO.
        # Ela somente será CONCLUIDA quando o cliente confirmar.

        if solicitacao.status != Solicitacao.Status.EM_EXECUCAO:
            solicitacao.status = Solicitacao.Status.EM_EXECUCAO

            solicitacao.save(
                update_fields=[
                    "status",
                    "data_atualizacao",
                ]
            )

    messages.success(
        request,
        "Conclusão do serviço informada com sucesso. "
        "Agora aguardamos a confirmação do cliente.",
    )

    return redirect(
        "solicitacoes:detalhe_servico_profissional",
        pk=contratacao.pk,
    )



def validar_assinatura_webhook_mercado_pago(request):
    """
    Valida a assinatura do webhook usando o validador oficial
    do SDK Python do Mercado Pago.

    Retorna:
        (True, None) quando a assinatura é válida.
        (False, mensagem) quando é inválida ou não pode ser validada.

    Em desenvolvimento/teste, se a chave secreta ainda não estiver
    configurada, a validação é temporariamente ignorada para não
    interromper os testes locais já existentes.

    Em produção, a ausência da chave faz o webhook falhar fechado.
    """

    secret = getattr(
        settings,
        "MERCADO_PAGO_WEBHOOK_SECRET",
        "",
    )

    modo_teste = getattr(
        settings,
        "MP_PAGAMENTO_TESTE",
        False,
    )

    if not secret:
        if settings.DEBUG and modo_teste:
            logger.warning(
                "MERCADO_PAGO_WEBHOOK_SECRET não configurada. "
                "Validação de assinatura ignorada somente em DEBUG + TESTE."
            )
            return True, None

        return False, (
            "Chave secreta do webhook Mercado Pago não configurada."
        )

    x_signature = request.headers.get("x-signature", "")
    x_request_id = request.headers.get("x-request-id", "")
    data_id = (
        request.GET.get("data.id")
        or request.GET.get("data_id")
        or ""
    )

    if not x_signature or not x_request_id:
        return False, (
            "Cabeçalhos de assinatura do Mercado Pago ausentes."
        )

    if not data_id:
        return False, (
            "Identificador data.id ausente na notificação do Mercado Pago."
        )

    # Para notificações de Order, o Mercado Pago envia data.id
    # em maiúsculas na URL, mas documenta que o valor deve ser
    # convertido para minúsculas antes da validação HMAC.
    # IDs numéricos de Payment não são afetados por lower().
    data_id = str(data_id).lower()

    try:
        from mercadopago.webhook import (
            WebhookSignatureValidator,
            InvalidWebhookSignatureError,
        )
    except ImportError:
        logger.exception(
            "SDK Mercado Pago sem WebhookSignatureValidator disponível."
        )
        return False, (
            "Validador oficial de webhook do Mercado Pago indisponível no SDK instalado."
        )

    try:
        WebhookSignatureValidator.validate(
            x_signature,
            x_request_id,
            data_id,
            secret,
        )
    except InvalidWebhookSignatureError:
        return False, (
            "Assinatura do webhook Mercado Pago inválida."
        )
    except Exception:
        logger.exception(
            "Erro inesperado ao validar assinatura do webhook Mercado Pago."
        )
        return False, (
            "Não foi possível validar a assinatura do webhook Mercado Pago."
        )

    return True, None


@csrf_exempt
def webhook_mercadopago(request):
    """
    Webhook do Mercado Pago.

    Trata dois fluxos:

    TESTE
        Evento de Order.
        Consulta:
            GET /v1/orders/{order_id}
        Token:
            settings.MERCADO_PAGO_TEST_ACCESS_TOKEN

    REAL
        Evento de Payment.
        Consulta:
            GET /v1/payments/{payment_id}
        Token:
            OAuth do profissional (ContaGateway)
    """

    # ==========================================================
    # MÉTODO HTTP
    # ==========================================================

    if request.method != "POST":
        return JsonResponse(
            {
                "status": "error",
                "message": "Método não permitido.",
            },
            status=405,
        )

    # ==========================================================
    # VALIDAÇÃO DA ASSINATURA DO MERCADO PAGO
    # ==========================================================

    assinatura_valida, erro_assinatura = (
        validar_assinatura_webhook_mercado_pago(request)
    )

    if not assinatura_valida:
        logging.warning(
            "Webhook Mercado Pago rejeitado: %s",
            erro_assinatura,
        )

        return JsonResponse(
            {
                "status": "unauthorized",
                "message": erro_assinatura,
            },
            status=401,
        )

    try:

        # ======================================================
        # LEITURA DO JSON
        # ======================================================

        data = json.loads(request.body or "{}")

        logging.info(
            "Webhook Mercado Pago recebido: %s",
            data,
        )

        # ======================================================
        # IDENTIFICAÇÃO DO EVENTO
        # ======================================================

        evento_tipo = str(data.get("type") or "").lower()
        evento_acao = str(data.get("action") or "").lower()

        identificador_evento = (
            f"{evento_tipo} {evento_acao}"
        )

        evento_order = "order" in identificador_evento
        evento_payment = "payment" in identificador_evento

        if not evento_order and not evento_payment:

            logging.info(
                "Webhook ignorado. type=%s action=%s",
                evento_tipo,
                evento_acao,
            )

            return JsonResponse(
                {
                    "status": "ignored",
                    "event_type": evento_tipo,
                    "action": evento_acao,
                },
                status=200,
            )

        # ======================================================
        # IDENTIFICADOR RECEBIDO
        # ======================================================

        identificador_mp = (
            data.get("data", {}).get("id")
            or data.get("id")
        )

        if not identificador_mp:

            logging.warning(
                "Webhook recebido sem identificador: %s",
                data,
            )

            return JsonResponse(
                {
                    "status": "error",
                    "message": (
                        "Identificador do Mercado Pago "
                        "não informado."
                    ),
                },
                status=400,
            )

        identificador_mp = str(identificador_mp)

        # ======================================================
        # LOCALIZA PAGAMENTO LOCAL
        # ======================================================

        if evento_order:

            # No modo de teste:
            #
            # mercado_pago_id = ORDER ID

            pagamento_obj = (
                Pagamento.objects
                .select_related(
                    "contratacao",
                    "contratacao__solicitacao",
                    "contratacao__orcamento",
                    "contratacao__profissional",
                    "cliente",
                )
                .filter(
                    mercado_pago_id=identificador_mp
                )
                .first()
            )

        else:

            # No modo real:
            #
            # mercado_pago_id = PAYMENT ID
            #
            # identificador_transacao também contém
            # o PAYMENT ID.

            pagamento_obj = (
                Pagamento.objects
                .select_related(
                    "contratacao",
                    "contratacao__solicitacao",
                    "contratacao__orcamento",
                    "contratacao__profissional",
                    "cliente",
                )
                .filter(
                    mercado_pago_id=identificador_mp
                )
                .first()
            )

            if pagamento_obj is None:

                pagamento_obj = (
                    Pagamento.objects
                    .select_related(
                        "contratacao",
                        "contratacao__solicitacao",
                        "contratacao__orcamento",
                        "contratacao__profissional",
                        "cliente",
                    )
                    .filter(
                        identificador_transacao=identificador_mp
                    )
                    .first()
                )

        # ======================================================
        # PAGAMENTO NÃO ENCONTRADO
        # ======================================================

        if pagamento_obj is None:

            logging.warning(
                "Webhook recebido para %s %s, "
                "mas nenhum pagamento local foi encontrado.",
                "Order" if evento_order else "Payment",
                identificador_mp,
            )

            return JsonResponse(
                {
                    "status": "ignored",
                    "message": (
                        "Pagamento local não encontrado."
                    ),
                    "event_type": evento_tipo,
                    "mercado_pago_id": identificador_mp,
                },
                status=200,
            )

        # ======================================================
        # OBJETOS RELACIONADOS
        # ======================================================

        contratacao = pagamento_obj.contratacao
        solicitacao = contratacao.solicitacao
        orcamento = contratacao.orcamento
        profissional = contratacao.profissional

        # Variável explicitamente inicializada.
        #
        # Em Order de teste ela continuará None.
        # Em Payment real receberá a ContaGateway.

        conta_gateway = None

        # ======================================================
        # EVENTO ORDER - MODO DE TESTE
        # ======================================================

        if evento_order:

            order_id = identificador_mp

            access_token = getattr(
                settings,
                "MERCADO_PAGO_TEST_ACCESS_TOKEN",
                "",
            )

            if not access_token:

                logging.error(
                    "Access Token de teste do "
                    "Mercado Pago não configurado."
                )

                return JsonResponse(
                    {
                        "status": "error",
                        "message": (
                            "Access Token de teste "
                            "não configurado."
                        ),
                    },
                    status=500,
                )

            mp_url = (
                "https://api.mercadopago.com/v1/orders/"
                f"{order_id}"
            )

            logging.info(
                "Consultando Order de teste %s. "
                "Pagamento local=%s Profissional=%s",
                order_id,
                pagamento_obj.pk,
                profissional.pk,
            )

        # ======================================================
        # EVENTO PAYMENT - MODO REAL
        # ======================================================

        else:

            payment_id_evento = identificador_mp

            conta_gateway = (
                ContaGateway.objects
                .filter(
                    profissional=profissional,
                    gateway=ContaGateway.Gateway.MERCADO_PAGO,
                    ativo=True,
                )
                .first()
            )

            if not conta_gateway:

                logging.error(
                    "Conta Mercado Pago não encontrada. "
                    "Profissional=%s Payment=%s",
                    profissional.pk,
                    payment_id_evento,
                )

                return JsonResponse(
                    {
                        "status": "error",
                        "message": (
                            "Conta Mercado Pago do "
                            "profissional não encontrada."
                        ),
                    },
                    status=500,
                )

            access_token, erro_token = (
                obter_access_token_mercado_pago(conta_gateway)
            )

            if not access_token:

                logging.error(
                    "Falha na credencial OAuth da ContaGateway %s: %s",
                    conta_gateway.pk,
                    erro_token,
                )

                return JsonResponse(
                    {
                        "status": "error",
                        "message": (
                            "Access Token do profissional "
                            "não encontrado."
                        ),
                    },
                    status=500,
                )

            mp_url = (
                "https://api.mercadopago.com/v1/payments/"
                f"{payment_id_evento}"
            )

            logging.info(
                "Consultando Payment real %s. "
                "Pagamento local=%s Profissional=%s "
                "ContaGateway=%s",
                payment_id_evento,
                pagamento_obj.pk,
                profissional.pk,
                conta_gateway.pk,
            )

        # ======================================================
        # CONSULTA MERCADO PAGO
        # ======================================================

        response = requests.get(
            mp_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

        if response.status_code != 200:

            if evento_order:

                logging.error(
                    "Erro ao consultar Order %s. "
                    "Profissional=%s "
                    "HTTP=%s Resposta=%s",
                    identificador_mp,
                    profissional.pk,
                    response.status_code,
                    response.text,
                )

            else:

                logging.error(
                    "Erro ao consultar Payment %s. "
                    "Profissional=%s ContaGateway=%s "
                    "HTTP=%s Resposta=%s",
                    identificador_mp,
                    profissional.pk,
                    conta_gateway.pk,
                    response.status_code,
                    response.text,
                )

            return JsonResponse(
                {
                    "status": "error",
                    "message": (
                        "Não foi possível consultar "
                        "o Mercado Pago."
                    ),
                    "mercado_pago_id": identificador_mp,
                },
                status=502,
            )

        # ======================================================
        # JSON DA CONSULTA
        # ======================================================

        try:
            resposta_mp = response.json()
        except ValueError:

            logging.error(
                "Mercado Pago retornou JSON inválido. "
                "ID=%s Resposta=%s",
                identificador_mp,
                response.text,
            )

            return JsonResponse(
                {
                    "status": "error",
                    "message": (
                        "Resposta inválida do Mercado Pago."
                    ),
                },
                status=502,
            )

        # ======================================================
        # VARIÁVEIS NORMALIZADAS
        # ======================================================

        order_id = None
        payment_id = None

        status_order = None
        status_order_detail = None

        status_pagamento = None
        status_detail = None

        external_reference = None

        payment_method = {}

        # ======================================================
        # INTERPRETA ORDER
        # ======================================================

        if evento_order:

            order_id = str(
                resposta_mp.get("id")
                or identificador_mp
            )

            status_order = resposta_mp.get("status")

            status_order_detail = resposta_mp.get(
                "status_detail"
            )

            external_reference = resposta_mp.get(
                "external_reference"
            )

            pagamentos_mp = (
                resposta_mp
                .get("transactions", {})
                .get("payments", [])
            )

            if pagamentos_mp:

                pagamento_mp = pagamentos_mp[0]

                payment_id = pagamento_mp.get("id")

                if payment_id:
                    payment_id = str(payment_id)

                status_pagamento = pagamento_mp.get(
                    "status"
                )

                status_detail = pagamento_mp.get(
                    "status_detail"
                )

                payment_method = (
                    pagamento_mp.get("payment_method")
                    or {}
                )

            logging.info(
                "Order %s consultada. "
                "Order status=%s/%s "
                "Payment=%s status=%s/%s",
                order_id,
                status_order,
                status_order_detail,
                payment_id,
                status_pagamento,
                status_detail,
            )

        # ======================================================
        # INTERPRETA PAYMENT
        # ======================================================

        else:

            payment_id = str(
                resposta_mp.get("id")
                or identificador_mp
            )

            status_pagamento = resposta_mp.get(
                "status"
            )

            status_detail = resposta_mp.get(
                "status_detail"
            )

            external_reference = resposta_mp.get(
                "external_reference"
            )

            # No /v1/payments os dados PIX ficam em:
            #
            # point_of_interaction.transaction_data

            point_of_interaction = (
                resposta_mp.get(
                    "point_of_interaction"
                )
                or {}
            )

            transaction_data = (
                point_of_interaction.get(
                    "transaction_data"
                )
                or {}
            )

            payment_method = {
                "qr_code": transaction_data.get(
                    "qr_code"
                ),
                "qr_code_base64": (
                    transaction_data.get(
                        "qr_code_base64"
                    )
                ),
                "ticket_url": transaction_data.get(
                    "ticket_url"
                ),
            }

            logging.info(
                "Payment %s consultado. "
                "status=%s/%s "
                "Profissional=%s ContaGateway=%s",
                payment_id,
                status_pagamento,
                status_detail,
                profissional.pk,
                conta_gateway.pk,
            )

        # ======================================================
        # ATUALIZA IDENTIFICADORES
        # ======================================================

        if evento_order:

            pagamento_obj.mercado_pago_id = order_id

            if payment_id:
                pagamento_obj.identificador_transacao = (
                    payment_id
                )

        else:

            pagamento_obj.mercado_pago_id = payment_id

            pagamento_obj.identificador_transacao = (
                payment_id
            )

        # ======================================================
        # STATUS DO MERCADO PAGO
        # ======================================================

        if evento_order:

            pagamento_obj.mercado_pago_status = (
                status_order
                or status_pagamento
            )

            pagamento_obj.mercado_pago_status_detail = (
                status_order_detail
                or status_detail
            )

        else:

            pagamento_obj.mercado_pago_status = (
                status_pagamento
            )

            pagamento_obj.mercado_pago_status_detail = (
                status_detail
            )

        # ======================================================
        # DADOS PIX
        # ======================================================

        if payment_method.get("qr_code"):
            pagamento_obj.qr_code = (
                payment_method.get("qr_code")
            )

        if payment_method.get("qr_code_base64"):
            pagamento_obj.qr_code_base64 = (
                payment_method.get(
                    "qr_code_base64"
                )
            )

        if payment_method.get("ticket_url"):
            pagamento_obj.ticket_url = (
                payment_method.get("ticket_url")
            )

        # ======================================================
        # DETERMINA APROVAÇÃO
        # ======================================================

        pagamento_aprovado = False

        if evento_order:

            # No ambiente de teste, a Order pode chegar a
            # processed/accredited automaticamente. O webhook de
            # Order atualiza os metadados do Mercado Pago, mas não
            # aprova o pagamento local. A aprovação de teste é
            # explícita pela rotina pagamento_teste.
            pagamento_aprovado = False

        else:

            # Payments API:
            #
            # pagamento real aprovado:
            #
            # approved

            pagamento_aprovado = (
                status_pagamento == "approved"
            )

        # ======================================================
        # PAGAMENTO APROVADO
        # ======================================================

        if pagamento_aprovado:

            # Uma notificação atrasada de "approved" não pode
            # reabrir um pagamento/contratação que já foi encerrado.
            if (
                pagamento_obj.status in [
                    Pagamento.Status.ESTORNADO,
                    Pagamento.Status.CANCELADO,
                ]
                or contratacao.status == Contratacao.Status.CANCELADA
                or solicitacao.status == Solicitacao.Status.CANCELADA
            ):
                logging.info(
                    "Webhook approved ignorado para estado final. "
                    "Pagamento=%s status=%s Contratacao=%s Solicitacao=%s",
                    pagamento_obj.pk,
                    pagamento_obj.status,
                    contratacao.status,
                    solicitacao.status,
                )

                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Notificação antiga ignorada.",
                    },
                    status=200,
                )

            contratacao_ja_confirmada = contratacao.status in [
                Contratacao.Status.PAGAMENTO_CONFIRMADO,
                Contratacao.Status.EM_EXECUCAO,
                Contratacao.Status.SERVICO_CONCLUIDO,
                Contratacao.Status.PAGAMENTO_LIBERADO,
            ]

            with transaction.atomic():

                pagamento_obj.status = (
                    Pagamento.Status.APROVADO
                )

                if (
                    hasattr(
                        pagamento_obj,
                        "data_pagamento",
                    )
                    and not pagamento_obj.data_pagamento
                ):
                    pagamento_obj.data_pagamento = (
                        timezone.now()
                    )

                pagamento_obj.save()

                # ----------------------------------------------
                # CONTRATAÇÃO
                # ----------------------------------------------

                if contratacao.status not in [
                    Contratacao.Status.PAGAMENTO_CONFIRMADO,
                    Contratacao.Status.EM_EXECUCAO,
                    Contratacao.Status.SERVICO_CONCLUIDO,
                    Contratacao.Status.PAGAMENTO_LIBERADO,
                ]:

                    contratacao.status = (
                        Contratacao.Status.PAGAMENTO_CONFIRMADO
                    )

                    contratacao.save(
                        update_fields=[
                            "status",
                            "data_atualizacao",
                        ]
                    )

                # ----------------------------------------------
                # SOLICITAÇÃO
                # ----------------------------------------------

                if solicitacao.status not in [
                    Solicitacao.Status.EM_EXECUCAO,
                    Solicitacao.Status.CONCLUIDA,
                    Solicitacao.Status.CANCELADA,
                ]:

                    solicitacao.status = (
                        Solicitacao.Status.EM_EXECUCAO
                    )

                    solicitacao.save(
                        update_fields=[
                            "status",
                            "data_atualizacao",
                        ]
                    )

                # ----------------------------------------------
                # ORÇAMENTO
                # ----------------------------------------------

                if orcamento:

                    if (
                        orcamento.status
                        != Orcamento.Status.ACEITO
                    ):

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
                        status=Orcamento.Status.ENVIADO,
                    ).exclude(
                        pk=orcamento.pk
                    ).update(
                        status=Orcamento.Status.RECUSADO
                    )

            if not contratacao_ja_confirmada:
                _notificar_profissional_orcamento_contratado(contratacao)

            logging.info(
                "Pagamento APROVADO pelo webhook. "
                "Order=%s Payment=%s "
                "Pagamento local=%s "
                "Contratacao=%s Solicitacao=%s",
                order_id,
                payment_id,
                pagamento_obj.pk,
                contratacao.pk,
                solicitacao.pk,
            )

        # ======================================================
        # NÃO APROVADO
        # ======================================================

        else:

            # --------------------------------------------------
            # Escolhe status relevante
            # --------------------------------------------------

            if evento_order:
                status_relevante = (
                    status_order
                    or status_pagamento
                )
            else:
                status_relevante = status_pagamento

            # No modo de teste, notificações de Order servem apenas
            # para atualizar os metadados do Mercado Pago. O estado
            # local é controlado exclusivamente pela rotina de teste.
            if evento_order and getattr(
                settings,
                "MP_PAGAMENTO_TESTE",
                False,
            ):
                pagamento_obj.save()

                logging.info(
                    "Webhook Order de teste recebido sem alterar "
                    "o status local. Order=%s Payment=%s status=%s "
                    "Pagamento local=%s estado=%s",
                    order_id,
                    payment_id,
                    status_relevante,
                    pagamento_obj.pk,
                    pagamento_obj.status,
                )

            # ESTORNADO é um estado final e nunca deve regredir.
            elif pagamento_obj.status == Pagamento.Status.ESTORNADO:
                pagamento_obj.save()

                logging.info(
                    "Webhook ignorado: pagamento %s já está ESTORNADO.",
                    pagamento_obj.pk,
                )

            # Depois de aprovado, eventos antigos pending/processing/
            # rejected/cancelled não podem rebaixar o pagamento.
            # A única transição posterior aceita aqui é refunded.
            elif pagamento_obj.status == Pagamento.Status.APROVADO:
                if status_relevante == "refunded":
                    pagamento_obj.status = Pagamento.Status.ESTORNADO
                    pagamento_obj.save()
                else:
                    pagamento_obj.save()
                    logging.info(
                        "Webhook antigo ignorado para pagamento APROVADO. "
                        "Pagamento=%s status_mp=%s",
                        pagamento_obj.pk,
                        status_relevante,
                    )

            # --------------------------------------------------
            # PROCESSANDO
            # --------------------------------------------------

            elif status_relevante in [
                "processing",
                "in_process",
                "in_mediation",
            ]:
                pagamento_obj.status = Pagamento.Status.PROCESSANDO
                pagamento_obj.save()

            # --------------------------------------------------
            # PENDENTE / AGUARDANDO PIX
            # --------------------------------------------------

            elif status_relevante in [
                "action_required",
                "pending",
                "created",
            ]:
                pagamento_obj.status = Pagamento.Status.PENDENTE
                pagamento_obj.save()

            # --------------------------------------------------
            # RECUSADO / FALHOU
            # --------------------------------------------------

            elif status_relevante in [
                "failed",
                "rejected",
            ]:
                pagamento_obj.status = Pagamento.Status.RECUSADO

                if hasattr(pagamento_obj, "data_pagamento"):
                    pagamento_obj.data_pagamento = None

                pagamento_obj.save()

            # --------------------------------------------------
            # CANCELADO / EXPIRADO
            # --------------------------------------------------

            elif status_relevante in [
                "cancelled",
                "expired",
            ]:
                pagamento_obj.status = Pagamento.Status.CANCELADO
                pagamento_obj.save()

            # --------------------------------------------------
            # ESTORNADO
            # --------------------------------------------------

            elif status_relevante == "refunded":
                pagamento_obj.status = Pagamento.Status.ESTORNADO
                pagamento_obj.save()

            else:
                # Persiste apenas metadados recebidos do Mercado Pago.
                pagamento_obj.save()

            logging.info(
                "Pagamento ainda não aprovado. "
                "Order=%s Payment=%s "
                "status=%s "
                "Pagamento local=%s",
                order_id,
                payment_id,
                status_relevante,
                pagamento_obj.pk,
            )

        # ======================================================
        # RESPOSTA
        # ======================================================

        return JsonResponse(
            {
                "status": "success",
                "event_type": evento_tipo,
                "action": evento_acao,
                "order_id": order_id,
                "payment_id": payment_id,
                "order_status": status_order,
                "order_status_detail": (
                    status_order_detail
                ),
                "mercado_pago_status": (
                    status_pagamento
                ),
                "mercado_pago_status_detail": (
                    status_detail
                ),
                "external_reference": (
                    external_reference
                ),
                "pagamento_id": pagamento_obj.pk,
                "contratacao_id": contratacao.pk,
                "solicitacao_id": solicitacao.pk,
                "local_payment_status": (
                    pagamento_obj.status
                ),
            },
            status=200,
        )

    # ==========================================================
    # JSON INVÁLIDO
    # ==========================================================

    except json.JSONDecodeError:

        logging.error(
            "Webhook Mercado Pago recebeu JSON inválido."
        )

        return JsonResponse(
            {
                "status": "error",
                "message": "JSON inválido.",
            },
            status=400,
        )

    # ==========================================================
    # ERRO DE COMUNICAÇÃO
    # ==========================================================

    except requests.RequestException as e:

        logging.exception(
            "Erro de comunicação com Mercado Pago: %s",
            e,
        )

        return JsonResponse(
            {
                "status": "error",
                "message": (
                    "Erro de comunicação com "
                    "o Mercado Pago."
                ),
            },
            status=502,
        )

    # ==========================================================
    # ERRO GERAL
    # ==========================================================

    except Exception as e:

        logging.exception(
            "Erro no webhook do Mercado Pago."
        )

        return JsonResponse(
            {
                "status": "error",
                "message": str(e),
            },
            status=500,
        )


@profissional_obrigatorio
def meus_servicos_profissional(request, profissional):
    """Lista as contratações pertencentes ao profissional logado."""
    contratacoes = (
        Contratacao.objects.filter(profissional=profissional)
        .select_related(
            "solicitacao",
            "solicitacao__categoria",
            "solicitacao__cliente",
            "solicitacao__cliente__usuario",
            "pagamento",
        )
        .order_by("-data_contratacao")
    )

    return render(
        request,
        "solicitacoes/meus_servicos_profissional.html",
        {"contratacoes": contratacoes},
    )


@profissional_obrigatorio
def detalhe_servico_profissional(request, profissional, pk):
    """Detalhe de uma contratação, exclusivo do profissional contratado."""
    contratacao = get_object_or_404(
        Contratacao.objects.select_related(
            "solicitacao",
            "solicitacao__categoria",
            "solicitacao__cliente",
            "solicitacao__cliente__usuario",
            "orcamento",
            "pagamento",
        ),
        pk=pk,
        profissional=profissional,
    )

    return render(
        request,
        "solicitacoes/detalhe_servico_profissional.html",
        {
            "contratacao": contratacao,
            "solicitacao": contratacao.solicitacao,
            "pagamento": getattr(contratacao, "pagamento", None),
        },
    )



def _notificar_cancelamento_contratacao(
    destinatario,
    contratacao,
    cancelado_por,
    pagamento=None,
):
    """Envia WhatsApp e e-mail à outra parte após o cancelamento."""
    usuario = getattr(destinatario, "usuario", None)

    nome = (
        getattr(usuario, "first_name", "")
        or getattr(usuario, "nome", "")
        or getattr(destinatario, "nome", "")
        or (
            "cliente"
            if cancelado_por == "profissional"
            else "profissional"
        )
    )

    telefone = (
        getattr(usuario, "telefone", None)
        or getattr(destinatario, "telefone", None)
        or getattr(destinatario, "celular", None)
    )

    email = (
        getattr(usuario, "email", None)
        or getattr(destinatario, "email", None)
    )

    valor_formatado = f"R$ {contratacao.valor:.2f}".replace(".", ",")
    titulo_servico = contratacao.solicitacao.titulo

    if cancelado_por == "cliente":
        mensagem = (
            f"Olá, {nome}!\n\n"
            f"O cliente cancelou a Solicitação #{contratacao.solicitacao.pk}, "
            f'referente ao serviço "{titulo_servico}", '
            f"no valor de {valor_formatado}.\n\n"
            "A contratação foi encerrada na plataforma."
        )
    else:
        mensagem = (
            f"Olá, {nome}!\n\n"
            f"O profissional cancelou a Solicitação #{contratacao.solicitacao.pk}, "
            f'referente ao serviço "{titulo_servico}", '
            f"no valor de {valor_formatado}."
        )

        if pagamento and pagamento.status == Pagamento.Status.ESTORNADO:
            mensagem += (
                "\n\nO pagamento foi estornado. "
                "O prazo para o valor ficar disponível depende "
                "do meio de pagamento e da instituição financeira."
            )
        else:
            mensagem += "\n\nA contratação foi encerrada na plataforma."

    assunto = (
        f"Cancelamento da contratação #{contratacao.pk} - "
        "ChamaPro Serviços"
    )

    if telefone:
        try:
            enviar_whatsapp(telefone, mensagem)
        except Exception as exc:
            logger.exception(
                "Erro ao enviar WhatsApp de cancelamento da "
                "contratação %s: %s",
                contratacao.pk,
                exc,
            )

    if email:
        try:
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as exc:
            logger.exception(
                "Erro ao enviar e-mail de cancelamento da "
                "contratação %s: %s",
                contratacao.pk,
                exc,
            )


@profissional_obrigatorio
def cancelar_contratacao_profissional(request, profissional, pk):
    """Permite ao profissional desistir da própria contratação."""
    contratacao = get_object_or_404(
        Contratacao.objects.select_related(
            "solicitacao",
            "orcamento",
            "cliente",
            "cliente__usuario",
            "pagamento",
        ),
        pk=pk,
        profissional=profissional,
    )
    solicitacao = contratacao.solicitacao

    if request.method != "POST":
        return redirect(
            "solicitacoes:detalhe_servico_profissional",
            pk=contratacao.pk,
        )

    if contratacao.status in [
        Contratacao.Status.SERVICO_CONCLUIDO,
        Contratacao.Status.PAGAMENTO_LIBERADO,
        Contratacao.Status.CANCELADA,
    ]:
        messages.error(
            request,
            "Esta contratação não pode mais ser cancelada.",
        )
        return redirect(
            "solicitacoes:detalhe_servico_profissional",
            pk=contratacao.pk,
        )

    try:
        pagamento = contratacao.pagamento
    except Pagamento.DoesNotExist:
        pagamento = None

    if pagamento and pagamento.status == Pagamento.Status.APROVADO:
        sucesso, mensagem = reembolsar_pagamento_mercado_pago(
            pagamento,
            notificar_cliente=False,
        )

        if not sucesso:
            messages.error(
                request,
                "O serviço não foi cancelado porque o reembolso ao cliente "
                f"não pôde ser confirmado: {mensagem}",
            )
            return redirect(
                "solicitacoes:detalhe_servico_profissional",
                pk=contratacao.pk,
            )

    with transaction.atomic():
        if pagamento and pagamento.status != Pagamento.Status.ESTORNADO:
            pagamento.status = Pagamento.Status.CANCELADO
            pagamento.save(update_fields=["status"])

        contratacao.status = Contratacao.Status.CANCELADA
        contratacao.save(
            update_fields=["status", "data_atualizacao"]
        )

        if contratacao.orcamento:
            contratacao.orcamento.status = Orcamento.Status.CANCELADO
            contratacao.orcamento.save(
                update_fields=["status", "data_atualizacao"]
            )

        solicitacao.status = Solicitacao.Status.CANCELADA
        solicitacao.save(
            update_fields=["status", "data_atualizacao"]
        )

    _notificar_cancelamento_contratacao(
        destinatario=contratacao.cliente,
        contratacao=contratacao,
        cancelado_por="profissional",
        pagamento=pagamento,
    )

    if pagamento and pagamento.status == Pagamento.Status.ESTORNADO:
        messages.success(
            request,
            "Serviço cancelado. O reembolso ao cliente foi solicitado "
            "com sucesso e o cliente foi informado.",
        )
    else:
        messages.success(
            request,
            "Serviço cancelado com sucesso. O cliente foi informado.",
        )

    return redirect("solicitacoes:meus_servicos_profissional")


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

                contratacao.status = Contratacao.Status.PAGAMENTO_CONFIRMADO
                contratacao.save(update_fields=["status"])

                solicitacao = contratacao.solicitacao
                solicitacao.status = Solicitacao.Status.EM_EXECUCAO
                solicitacao.save(update_fields=["status"])

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
            "mp_pagamento_teste": (
                    settings.DEBUG
                    and getattr(
                settings,
                "MP_PAGAMENTO_TESTE",
                False
            )
            ),
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


def reembolsar_pagamento_mercado_pago(pagamento, notificar_cliente=True):
    """
    Solicita reembolso total no Mercado Pago.

    TESTE:
        mercado_pago_id = ORDER ID
        POST /v1/orders/{order_id}/refund
        token de teste da aplicação

    REAL / MARKETPLACE:
        identificador_transacao (ou mercado_pago_id) = PAYMENT ID
        POST /v1/payments/{payment_id}/refunds
        token OAuth do profissional
    """

    contratacao = pagamento.contratacao
    profissional = contratacao.profissional
    modo_teste = getattr(settings, "MP_PAGAMENTO_TESTE", False)

    if modo_teste:
        order_id = pagamento.mercado_pago_id

        if not order_id:
            return False, (
                "Order ID do Mercado Pago não encontrado "
                "para este pagamento de teste."
            )

        access_token = getattr(
            settings,
            "MERCADO_PAGO_TEST_ACCESS_TOKEN",
            "",
        )

        if not access_token:
            return False, (
                "Access Token de teste do Mercado Pago "
                "não está configurado."
            )

        url = (
            "https://api.mercadopago.com/v1/orders/"
            f"{order_id}/refund"
        )

    else:
        payment_id = (
            pagamento.identificador_transacao
            or pagamento.mercado_pago_id
        )

        if not payment_id:
            return False, (
                "Payment ID do Mercado Pago não encontrado "
                "para este pagamento."
            )

        conta_gateway = ContaGateway.objects.filter(
            profissional=profissional,
            gateway=ContaGateway.Gateway.MERCADO_PAGO,
            ativo=True,
        ).first()

        if not conta_gateway:
            return False, (
                "A conta Mercado Pago do profissional "
                "não está conectada ao marketplace."
            )

        access_token, erro_token = (
            obter_access_token_mercado_pago(conta_gateway)
        )

        if not access_token:
            return False, (
                erro_token
                or "Não foi possível validar a conexão Mercado Pago."
            )

        url = (
            "https://api.mercadopago.com/v1/payments/"
            f"{payment_id}/refunds"
        )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }

    try:
        response = requests.post(
            url,
            json={},
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as exc:
        logger.exception(
            "Erro de comunicação ao solicitar reembolso "
            "no Mercado Pago: %s",
            exc,
        )
        return False, (
            "Falha de comunicação com o Mercado Pago "
            "ao solicitar o reembolso."
        )

    try:
        resposta = response.json()
    except ValueError:
        resposta = {}

    if response.status_code not in (200, 201):
        mensagem = (
            resposta.get("message")
            or resposta.get("error")
            or response.text
            or "Erro desconhecido ao solicitar o reembolso."
        )

        logger.error(
            "Mercado Pago recusou reembolso. HTTP %s - %s",
            response.status_code,
            response.text,
        )

        return False, str(mensagem)

    pagamento.status = Pagamento.Status.ESTORNADO
    pagamento.mercado_pago_status = "refunded"
    pagamento.save(
        update_fields=[
            "status",
            "mercado_pago_status",
        ]
    )

    if notificar_cliente:
        try:
            cliente = pagamento.cliente
            usuario = getattr(cliente, "usuario", None)
            telefone = (
                getattr(usuario, "telefone", None)
                or getattr(cliente, "telefone", None)
            )

            if telefone:
                nome = getattr(usuario, "first_name", "") or "cliente"
                valor_formatado = f"R$ {pagamento.valor:.2f}"

                mensagem = (
                    f"Olá, {nome}! 📌\n\n"
                    f"Sua contratação *#{contratacao.pk}* foi cancelada "
                    f"e o reembolso no valor de *{valor_formatado}* "
                    f"foi solicitado com sucesso junto ao Mercado Pago."
                )

                enviar_whatsapp(telefone, mensagem)

        except Exception as exc:
            logger.exception(
                "Reembolso realizado, mas houve erro ao enviar "
                "WhatsApp ao cliente: %s",
                exc,
            )

    return True, "Reembolso solicitado com sucesso."


@login_required
@cliente_obrigatorio
def pagamento_teste(request, pk, cliente):
    """
    Simula um pagamento sem movimentar dinheiro.

    Disponível somente quando:
        DEBUG = True
        MP_PAGAMENTO_TESTE = True

    Resultados possíveis:
        aprovado
        pendente
        recusado
    """

    # ==========================================================
    # SEGURANÇA
    # ==========================================================

    if not settings.DEBUG or not getattr(
        settings,
        "MP_PAGAMENTO_TESTE",
        False
    ):
        return JsonResponse(
            {
                "status": "error",
                "message": "Modo de teste de pagamento desativado."
            },
            status=403
        )

    if request.method != "POST":
        return JsonResponse(
            {
                "status": "error",
                "message": "Método não permitido."
            },
            status=405
        )

    # ==========================================================
    # CONTRATAÇÃO
    # ==========================================================

    contratacao = get_object_or_404(
        Contratacao.objects.select_related(
            "solicitacao",
            "orcamento",
            "profissional",
            "cliente",
        ),
        pk=pk,
        cliente=cliente,
    )

    # ==========================================================
    # RESULTADO DO TESTE
    # ==========================================================

    resultado = (
        request.POST.get("resultado")
        or request.POST.get("status")
    )

    resultados_validos = {
        "aprovado",
        "pendente",
        "recusado",
    }

    if resultado not in resultados_validos:
        return JsonResponse(
            {
                "status": "error",
                "message": "Resultado de teste inválido."
            },
            status=400
        )

    # ==========================================================
    # MÉTODO DO PAGAMENTO
    # ==========================================================

    metodo = request.POST.get("metodo_pagamento")

    if metodo not in [
        Pagamento.Metodo.PIX,
        Pagamento.Metodo.CARTAO,
        Pagamento.Metodo.BOLETO,
    ]:
        metodo = Pagamento.Metodo.PIX

    # ==========================================================
    # NÃO PERMITIR ALTERAR UMA CONTRATAÇÃO JÁ CONFIRMADA
    # ==========================================================

    if contratacao.status in [
        Contratacao.Status.PAGAMENTO_CONFIRMADO,
        Contratacao.Status.EM_EXECUCAO,
        Contratacao.Status.SERVICO_CONCLUIDO,
        Contratacao.Status.PAGAMENTO_LIBERADO,
    ]:
        return JsonResponse(
            {
                "status": "error",
                "message": (
                    "Esta contratação já possui o pagamento "
                    "confirmado e não pode ser alterada pelo "
                    "teste de pagamento."
                )
            },
            status=400
        )

    # ==========================================================
    # LOCALIZA / CRIA O PAGAMENTO
    # ==========================================================

    pagamento_obj, created = Pagamento.objects.get_or_create(
        contratacao=contratacao,
        defaults={
            "cliente": cliente,
            "valor": contratacao.valor,
            "metodo": metodo,
            "status": Pagamento.Status.PENDENTE,
        }
    )

    pagamento_obj.cliente = cliente
    pagamento_obj.valor = contratacao.valor
    pagamento_obj.metodo = metodo

    # ==========================================================
    # PAGAMENTO PENDENTE
    # ==========================================================

    if resultado == "pendente":

        pagamento_obj.status = Pagamento.Status.PENDENTE

        pagamento_obj.mercado_pago_status = "pending"

        pagamento_obj.mercado_pago_status_detail = (
            "teste_pendente"
        )

        pagamento_obj.identificador_transacao = (
            f"TESTE-PENDENTE-{pagamento_obj.pk}"
        )

        pagamento_obj.mercado_pago_id = None
        pagamento_obj.data_pagamento = None

        pagamento_obj.save()

        messages.info(
            request,
            "Pagamento de teste colocado como PENDENTE."
        )

        return redirect(
            "solicitacoes:pagamento",
            pk=contratacao.pk
        )

    # ==========================================================
    # PAGAMENTO RECUSADO
    # ==========================================================

    if resultado == "recusado":

        pagamento_obj.status = Pagamento.Status.RECUSADO

        pagamento_obj.mercado_pago_status = "rejected"

        pagamento_obj.mercado_pago_status_detail = (
            "teste_recusado"
        )

        pagamento_obj.identificador_transacao = (
            f"TESTE-RECUSADO-{pagamento_obj.pk}"
        )

        pagamento_obj.mercado_pago_id = None
        pagamento_obj.data_pagamento = None

        pagamento_obj.save()

        messages.error(
            request,
            "Pagamento de teste RECUSADO."
        )

        return redirect(
            "solicitacoes:pagamento",
            pk=contratacao.pk
        )

    # ==========================================================
    # PAGAMENTO APROVADO
    # ==========================================================

    if resultado == "aprovado":

        with transaction.atomic():

            # --------------------------------------------------
            # PAGAMENTO
            # --------------------------------------------------

            pagamento_obj.status = Pagamento.Status.APROVADO

            pagamento_obj.mercado_pago_status = "approved"

            pagamento_obj.mercado_pago_status_detail = (
                "teste_aprovado"
            )

            pagamento_obj.identificador_transacao = (
                f"TESTE-APROVADO-{pagamento_obj.pk}"
            )

            pagamento_obj.mercado_pago_id = None

            pagamento_obj.data_pagamento = timezone.now()

            pagamento_obj.save()

            # --------------------------------------------------
            # CONTRATAÇÃO
            # --------------------------------------------------

            contratacao.status = (
                Contratacao.Status.PAGAMENTO_CONFIRMADO
            )

            contratacao.save(
                update_fields=["status"]
            )

            # --------------------------------------------------
            # SOLICITAÇÃO
            # --------------------------------------------------

            solicitacao = contratacao.solicitacao

            solicitacao.status = (
                Solicitacao.Status.EM_EXECUCAO
            )

            solicitacao.save(
                update_fields=["status"]
            )

            # --------------------------------------------------
            # ORÇAMENTO ACEITO
            # --------------------------------------------------

            orcamento = contratacao.orcamento

            orcamento.status = Orcamento.Status.ACEITO

            orcamento.save(
                update_fields=["status"]
            )

            # --------------------------------------------------
            # OUTROS ORÇAMENTOS RECUSADOS
            # --------------------------------------------------

            Orcamento.objects.filter(
                solicitacao=solicitacao,
                status=Orcamento.Status.ENVIADO,
            ).exclude(
                pk=orcamento.pk
            ).update(
                status=Orcamento.Status.RECUSADO
            )

        _notificar_profissional_orcamento_contratado(contratacao)

        messages.success(
            request,
            "Pagamento de teste APROVADO. Contratação confirmada."
        )

        return redirect(
            "solicitacoes:detalhe",
            pk=solicitacao.pk
        )

    # ==========================================================
    # FALLBACK
    # ==========================================================

    return JsonResponse(
        {
            "status": "error",
            "message": "Resultado não processado."
        },
        status=400
    )


@cliente_obrigatorio
def cancelar_contratacao_cliente(
    request,
    cliente,
    contratacao_id,
):
    """
    Cancela uma contratação do próprio cliente.

    Se houver pagamento aprovado, o reembolso é solicitado primeiro.
    O estado local só é cancelado depois que o Mercado Pago aceitar
    a solicitação de reembolso. Depois disso, o profissional é avisado.
    """
    contratacao = get_object_or_404(
        Contratacao.objects.select_related(
            "solicitacao",
            "profissional",
            "profissional__usuario",
            "pagamento",
        ),
        pk=contratacao_id,
        cliente=cliente,
    )

    solicitacao = contratacao.solicitacao

    if request.method != "POST":
        return redirect(
            "solicitacoes:detalhe",
            pk=solicitacao.pk,
        )

    if contratacao.status in [
        Contratacao.Status.SERVICO_CONCLUIDO,
        Contratacao.Status.PAGAMENTO_LIBERADO,
        Contratacao.Status.CANCELADA,
    ]:
        messages.error(
            request,
            "Esta contratação não pode mais ser cancelada.",
        )
        return redirect(
            "solicitacoes:detalhe",
            pk=solicitacao.pk,
        )

    try:
        pagamento = contratacao.pagamento
    except Pagamento.DoesNotExist:
        pagamento = None

    if pagamento and pagamento.status == Pagamento.Status.APROVADO:
        sucesso, mensagem = reembolsar_pagamento_mercado_pago(
            pagamento,
            notificar_cliente=False,
        )

        if not sucesso:
            messages.error(
                request,
                "A contratação não foi cancelada porque o "
                f"reembolso não pôde ser confirmado: {mensagem}",
            )
            return redirect(
                "solicitacoes:detalhe",
                pk=solicitacao.pk,
            )

        with transaction.atomic():
            contratacao.status = Contratacao.Status.CANCELADA
            contratacao.save(
                update_fields=["status", "data_atualizacao"]
            )

            solicitacao.status = Solicitacao.Status.CANCELADA
            solicitacao.save(
                update_fields=["status", "data_atualizacao"]
            )

        _notificar_cancelamento_contratacao(
            destinatario=contratacao.profissional,
            contratacao=contratacao,
            cancelado_por="cliente",
            pagamento=pagamento,
        )

        messages.success(
            request,
            "Contratação cancelada e reembolso solicitado com sucesso "
            "ao Mercado Pago. O profissional foi informado.",
        )

        return redirect(
            "solicitacoes:detalhe",
            pk=solicitacao.pk,
        )

    with transaction.atomic():
        if pagamento:
            pagamento.status = Pagamento.Status.CANCELADO
            pagamento.save(update_fields=["status"])

        contratacao.status = Contratacao.Status.CANCELADA
        contratacao.save(
            update_fields=["status", "data_atualizacao"]
        )

        solicitacao.status = Solicitacao.Status.CANCELADA
        solicitacao.save(
            update_fields=["status", "data_atualizacao"]
        )

    _notificar_cancelamento_contratacao(
        destinatario=contratacao.profissional,
        contratacao=contratacao,
        cancelado_por="cliente",
        pagamento=pagamento,
    )

    messages.success(
        request,
        "Contratação cancelada com sucesso. O profissional foi informado.",
    )

    return redirect(
        "solicitacoes:detalhe",
        pk=solicitacao.pk,
    )


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


@login_required
def verificar_status_pagamento(request, pk):
    """
    Consulta o status atual do pagamento.

    No modo de teste, sincroniza a Order do Mercado Pago.
    Retorna JSON para a página do PIX consultar automaticamente.
    """

    pagamento = get_object_or_404(
        Pagamento.objects.select_related(
            "contratacao",
            "contratacao__solicitacao",
            "contratacao__orcamento",
        ),
        pk=pk,
        cliente__usuario=request.user,
    )

    contratacao = pagamento.contratacao
    solicitacao = contratacao.solicitacao

    # ----------------------------------------------------------
    # JÁ ESTÁ APROVADO LOCALMENTE
    # ----------------------------------------------------------

    if pagamento.status == Pagamento.Status.APROVADO:

        return JsonResponse({
            "status": "APROVADO",
            "redirect_url": reverse(
                "solicitacoes:detalhe",
                kwargs={"pk": solicitacao.pk},
            ),
        })

    # ----------------------------------------------------------
    # MODO DE TESTE
    # ----------------------------------------------------------
    # Não consultamos a Order para promover o pagamento. A Order
    # sandbox pode se tornar processed/accredited automaticamente.
    # O polling apenas observa o estado LOCAL, que será alterado
    # pela simulação explícita de pagamento.

    modo_teste = getattr(
        settings,
        "MP_PAGAMENTO_TESTE",
        False,
    )

    if modo_teste:
        return JsonResponse({
            "status": pagamento.status,
        })

    # ----------------------------------------------------------
    # RESPOSTA NORMAL
    # ----------------------------------------------------------

    return JsonResponse({
        "status": pagamento.status,
    })


@cliente_obrigatorio
def confirmar_conclusao_servico(request, cliente, pk):
    """
    Permite ao cliente confirmar que o serviço foi concluído.

    A confirmação somente é permitida depois que o profissional
    informar a conclusão do serviço.
    """

    contratacao = get_object_or_404(
        Contratacao.objects.select_related(
            "solicitacao",
            "cliente",
            "profissional",
            "pagamento",
        ),
        pk=pk,
        cliente=cliente,
    )

    solicitacao = contratacao.solicitacao

    if request.method != "POST":
        return redirect(
            "solicitacoes:detalhe",
            pk=solicitacao.pk,
        )

    # ----------------------------------------------------------
    # Confere o pagamento
    # ----------------------------------------------------------

    try:
        pagamento = contratacao.pagamento
    except Pagamento.DoesNotExist:
        messages.error(
            request,
            "Não existe pagamento vinculado a esta contratação.",
        )

        return redirect(
            "solicitacoes:detalhe",
            pk=solicitacao.pk,
        )

    if pagamento.status != Pagamento.Status.APROVADO:
        messages.error(
            request,
            "Não é possível confirmar a conclusão porque "
            "o pagamento não está aprovado.",
        )

        return redirect(
            "solicitacoes:detalhe",
            pk=solicitacao.pk,
        )

    # ----------------------------------------------------------
    # Situações que não permitem nova confirmação
    # ----------------------------------------------------------

    if contratacao.status == Contratacao.Status.PAGAMENTO_LIBERADO:
        messages.info(
            request,
            "A conclusão deste serviço já foi confirmada.",
        )

        return redirect(
            "solicitacoes:detalhe",
            pk=solicitacao.pk,
        )

    if contratacao.status == Contratacao.Status.CANCELADA:
        messages.error(
            request,
            "Uma contratação cancelada não pode ser concluída.",
        )

        return redirect(
            "solicitacoes:detalhe",
            pk=solicitacao.pk,
        )

    # ----------------------------------------------------------
    # O profissional precisa concluir primeiro
    # ----------------------------------------------------------

    if contratacao.status != Contratacao.Status.SERVICO_CONCLUIDO:
        messages.error(
            request,
            "O profissional ainda não informou a conclusão "
            "deste serviço.",
        )

        return redirect(
            "solicitacoes:detalhe",
            pk=solicitacao.pk,
        )

    # ----------------------------------------------------------
    # Confirma definitivamente a conclusão
    # ----------------------------------------------------------

    with transaction.atomic():

        contratacao.status = Contratacao.Status.PAGAMENTO_LIBERADO
        contratacao.save(
            update_fields=[
                "status",
                "data_atualizacao",
            ]
        )

        solicitacao.status = Solicitacao.Status.CONCLUIDA
        solicitacao.save(
            update_fields=[
                "status",
                "data_atualizacao",
            ]
        )

    messages.success(
        request,
        "Conclusão do serviço confirmada com sucesso.",
    )

    return redirect(
        "solicitacoes:detalhe",
        pk=solicitacao.pk,
    )
