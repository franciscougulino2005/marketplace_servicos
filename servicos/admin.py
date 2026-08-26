from django.contrib import admin

from .models import Categoria, Servico


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):

    list_display = (
        "nome",
        "ativo",
        "data_cadastro",
        "data_atualizacao",
    )

    list_filter = (
        "ativo",
    )

    search_fields = (
        "nome",
        "descricao",
    )

    ordering = (
        "nome",
    )


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):

    list_display = (
        "nome",
        "categoria",
        "profissional",
        "preco_referencia",
        "ativo",
        "data_cadastro",
    )

    list_filter = (
        "categoria",
        "ativo",
    )

    search_fields = (
        "nome",
        "descricao",
        "profissional__nome_profissional",
    )

    autocomplete_fields = (
        "profissional",
        "categoria",
    )

    ordering = (
        "nome",
    )