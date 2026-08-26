from django.contrib import admin

from .models import (
    Contratacao,
    Orcamento,
    Solicitacao,
    SolicitacaoFoto,
)


class SolicitacaoFotoInline(admin.TabularInline):

    model = SolicitacaoFoto
    extra = 0


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
    )

    search_fields = (
        "titulo",
        "descricao",
        "cidade",
        "cliente__usuario__first_name",
        "cliente__usuario__last_name",
        "cliente__usuario__email",
    )

    autocomplete_fields = (
        "cliente",
        "categoria",
    )

    readonly_fields = (
        "data_criacao",
        "data_atualizacao",
    )

    inlines = [
        SolicitacaoFotoInline,
    ]

    ordering = (
        "-data_criacao",
    )


@admin.register(SolicitacaoFoto)
class SolicitacaoFotoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "solicitacao",
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
        "status",
        "data_criacao",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "solicitacao__titulo",
        "profissional__nome_profissional",
    )

    autocomplete_fields = (
        "solicitacao",
        "profissional",
    )

    readonly_fields = (
        "data_criacao",
        "data_atualizacao",
    )

    ordering = (
        "-data_criacao",
    )


@admin.register(Contratacao)
class ContratacaoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "solicitacao",
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
        "percentual_comissao",
    )

    search_fields = (
        "solicitacao__titulo",
        "cliente__usuario__first_name",
        "cliente__usuario__last_name",
        "cliente__usuario__email",
        "profissional__nome_profissional",
    )

    autocomplete_fields = (
        "solicitacao",
        "orcamento",
        "cliente",
        "profissional",
    )

    readonly_fields = (
        "data_contratacao",
        "data_atualizacao",
    )

    ordering = (
        "-data_contratacao",
    )