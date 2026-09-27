from django.urls import path
from . import views

app_name = "solicitacoes"

urlpatterns = [
    # ==========================================================
    # ÁREAS E AÇÕES DO CLIENTE
    # ==========================================================
    path("", views.lista_solicitacoes, name="lista_solicitacoes"),
    path("nova/", views.nova_solicitacao, name="nova_solicitacao"),
    path("<int:pk>/", views.detalhe_solicitacao, name="detalhe"),
    path("<int:pk>/cancelar/", views.cancelar_solicitacao, name="cancelar_solicitacao"),
    path("<int:pk>/orcamentos/", views.orcamentos_solicitacao, name="orcamentos_solicitacao"),
    path("<int:pk>/aceitar-orcamento/", views.aceitar_orcamento, name="aceitar_orcamento"),
    path("orcamento/<int:pk>/contratar/", views.contratar_orcamento, name="contratar_orcamento"),
    path("contratacao/<int:pk>/pagamento/", views.pagamento, name="pagamento"),
    path("pagamento/<int:pk>/processar/", views.processar_pagamento, name="processar_pagamento"),
    path("pagamento/<int:pk>/status/", views.verificar_status_pagamento, name="verificar_status_pagamento"),
    path("pagamento/<int:pk>/cartao/", views.processar_pagamento_cartao, name="processar_cartao"),
    path("contratacao/<int:pk>/pagamento-teste/", views.pagamento_teste, name="pagamento_teste"),
    path("contratacao/<int:contratacao_id>/cancelar/", views.cancelar_contratacao_cliente, name="cancelar_contratacao"),
    path("contratacao/<int:pk>/confirmar-conclusao/", views.confirmar_conclusao_servico, name="confirmar_conclusao_servico"),

    # ==========================================================
    # ÁREAS E AÇÕES DO PROFISSIONAL
    # ==========================================================
    path("disponiveis/", views.lista_solicitacoes_disponiveis, name="solicitacoes_disponiveis"),
    path("<int:pk>/novo-orcamento/", views.novo_orcamento, name="novo_orcamento"),
    path("meus-orcamentos/", views.meus_orcamentos, name="meus_orcamentos"),
    path("meus-servicos/", views.meus_servicos_profissional, name="meus_servicos_profissional"),
    path("meus-servicos/<int:pk>/", views.detalhe_servico_profissional, name="detalhe_servico_profissional"),
    path("meus-servicos/<int:pk>/cancelar/", views.cancelar_contratacao_profissional, name="cancelar_contratacao_profissional"),
    path("contratacao/<int:pk>/concluir-servico/", views.concluir_servico, name="concluir_servico"),

    # ==========================================================
    # WEBHOOK MERCADO PAGO
    # ==========================================================
    path("webhook/mercadopago/", views.webhook_mercadopago, name="webhook_mercadopago"),
]
