from django.urls import path

from .views import (
    cancelar_solicitacao,
    contratar_orcamento,
    detalhe_solicitacao,
    lista_solicitacoes,
    lista_solicitacoes_disponiveis,
    meus_orcamentos,
    nova_solicitacao,
    novo_orcamento,
    orcamentos_solicitacao,
    pagamento,
    processar_pagamento,
)


app_name = "solicitacoes"


urlpatterns = [

    path(
        "",
        lista_solicitacoes,
        name="lista",
    ),

    path(
        "nova/",
        nova_solicitacao,
        name="nova",
    ),

    path(
        "<int:pk>/",
        detalhe_solicitacao,
        name="detalhe",
    ),

    path(
        "<int:pk>/cancelar/",
        cancelar_solicitacao,
        name="cancelar",
    ),

    path(
        "disponiveis/",
        lista_solicitacoes_disponiveis,
        name="disponiveis",
    ),

    path(
        "orcamentos/",
        meus_orcamentos,
        name="meus_orcamentos",
    ),

    path(
        "<int:pk>/orcamento/",
        novo_orcamento,
        name="novo_orcamento",
    ),

    path(
        "<int:pk>/orcamentos/",
        orcamentos_solicitacao,
        name="orcamentos_solicitacao",
    ),

    path(
        "orcamentos/<int:pk>/contratar/",
        contratar_orcamento,
        name="contratar_orcamento",
    ),

    path(
        "contratacoes/<int:pk>/pagamento/",
        pagamento,
        name="pagamento",
    ),

    path(
        "pagamentos/<int:pk>/processar/",
        processar_pagamento,
        name="processar_pagamento",
    ),

]