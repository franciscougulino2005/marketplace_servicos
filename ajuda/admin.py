from django.contrib import admin

from .models import CategoriaAjuda, ArtigoAjuda


@admin.register(CategoriaAjuda)
class CategoriaAjudaAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'publico',
        'ordem',
        'ativo',
    )

    list_filter = (
        'publico',
        'ativo',
    )

    search_fields = (
        'nome',
        'descricao',
    )

    prepopulated_fields = {
        'slug': ('nome',)
    }

    ordering = (
        'ordem',
        'nome',
    )


@admin.register(ArtigoAjuda)
class ArtigoAjudaAdmin(admin.ModelAdmin):

    list_display = (
        'titulo',
        'categoria',
        'ordem',
        'ativo',
        'visualizacoes',
    )

    list_filter = (
        'categoria',
        'ativo',
    )

    search_fields = (
        'titulo',
        'resumo',
        'conteudo',
    )

    prepopulated_fields = {
        'slug': ('titulo',)
    }

    ordering = (
        'categoria',
        'ordem',
        'titulo',
    )