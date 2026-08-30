from django.contrib import admin

from .models import Servico


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

    # Removido 'categoria' do autocomplete
    autocomplete_fields = (
        "profissional",
    )

    ordering = (
        "nome",
    )