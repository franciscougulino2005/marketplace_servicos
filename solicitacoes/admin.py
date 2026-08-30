from django.contrib import admin

from .models import (
    Solicitacao,
    SolicitacaoFoto,
    Orcamento,
    Contratacao,
    Pagamento,
    ContaGateway,
)


@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "titulo",
        "cliente",
        "categoria",
        "cidade",
        "estado",
        "status",
        "data_criacao",
    )

    list_filter = (
        "status",
        "categoria",
        "estado",
        "data_criacao",
    )

    search_fields = (
        "titulo",
        "descricao",
        "cliente__usuario__first_name",
        "cliente__usuario__last_name",
        "cliente__usuario__email",
    )

    readonly_fields = (
        "data_criacao",
        "data_atualizacao",
    )


@admin.register(SolicitacaoFoto)
class SolicitacaoFotoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "solicitacao",
        "data_cadastro",
    )

    list_filter = (
        "data_cadastro",
    )

    search_fields = (
        "solicitacao__titulo",
    )

    readonly_fields = (
        "data_cadastro",
    )


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "solicitacao",
        "profissional",
        "valor",
        "prazo_execucao",
        "validade",
        "status",
        "data_criacao",
    )

    list_filter = (
        "status",
        "data_criacao",
    )

    search_fields = (
        "solicitacao__titulo",
        "profissional__nome_profissional",
        "profissional__usuario__email",
    )

    readonly_fields = (
        "data_criacao",
        "data_atualizacao",
    )


@admin.register(Contratacao)
class ContratacaoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "solicitacao",
        "orcamento",
        "cliente",
        "profissional",
        "valor",
        "percentual_comissao",
        "valor_comissao",
        "valor_profissional",
        "status",
        "data_contratacao",
    )

    list_filter = (
        "status",
        "data_contratacao",
    )

    search_fields = (
        "solicitacao__titulo",
        "orcamento__solicitacao__titulo",
        "cliente__usuario__first_name",
        "cliente__usuario__last_name",
        "cliente__usuario__email",
        "profissional__nome_profissional",
        "profissional__usuario__email",
    )

    readonly_fields = (
        "data_contratacao",
        "data_atualizacao",
    )


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "contratacao",
        "cliente",
        "valor",
        "metodo",
        "status",
        "identificador_transacao",
        "data_criacao",
        "data_pagamento",
    )

    list_filter = (
        "status",
        "metodo",
        "data_criacao",
        "data_pagamento",
    )

    search_fields = (
        "contratacao__solicitacao__titulo",
        "cliente__usuario__first_name",
        "cliente__usuario__last_name",
        "cliente__usuario__email",
        "identificador_transacao",
    )

    readonly_fields = (
        "data_criacao",
        "data_atualizacao",
        "data_pagamento",
    )


@admin.register(ContaGateway)
class ContaGatewayAdmin(admin.ModelAdmin):

    list_display = (
        "profissional",
        "gateway",
        "ativo",
        "token_expires_at",
        "data_conexao",
        "data_atualizacao",
    )

    list_filter = (
        "gateway",
        "ativo",
        "data_conexao",
    )

    search_fields = (
        "profissional__nome_profissional",
        "profissional__usuario__first_name",
        "profissional__usuario__last_name",
        "profissional__usuario__email",
    )

    readonly_fields = (
        "data_conexao",
        "data_atualizacao",
    )

    exclude = (
        "access_token",
        "refresh_token",
    )