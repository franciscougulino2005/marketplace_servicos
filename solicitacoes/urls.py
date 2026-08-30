from django.urls import path
from . import views

app_name = "solicitacoes"

urlpatterns = [
    # Áreas e Ações do Cliente
    path("", views.lista_solicitacoes, name="lista_solicitacoes"),
    path("nova/", views.nova_solicitacao, name="nova_solicitacao"),
    path("<int:pk>/", views.detalhe_solicitacao, name="detalhe"),
    path("<int:pk>/cancelar/", views.cancelar_solicitacao, name="cancelar_solicitacao"),
    path("<int:pk>/orcamentos/", views.orcamentos_solicitacao, name="orcamentos_solicitacao"),
    path("<int:pk>/aceitar-orcamento/", views.aceitar_orcamento, name="aceitar_orcamento"),
    path("orcamento/<int:pk>/contratar/", views.contratar_orcamento, name="contratar_orcamento"),
    path("contratacao/<int:pk>/pagamento/", views.pagamento, name="pagamento"),
    path("pagamento/<int:pk>/processar/", views.processar_pagamento, name="processar_pagamento"),

    # Áreas e Ações do Profissional
    # path("disponiveis/", views.lista_solicitacoes_disponiveis, name="disponiveis"),
    path("disponiveis/", views.lista_solicitacoes_disponiveis, name="solicitacoes_disponiveis"),
    path("<int:pk>/novo-orcamento/", views.novo_orcamento, name="novo_orcamento"),
    path("meus-orcamentos/", views.meus_orcamentos, name="meus_orcamentos"),
    path("meus-servicos/", views.meus_servicos_profissional, name="meus_servicos_profissional"),

    # Integrador Mercado Pago (Webhook)
    path("webhook/mercadopago/", views.webhook_mercadopago, name="webhook_mercadopago"),
]