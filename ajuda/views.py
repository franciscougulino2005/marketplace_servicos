from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.db.models import F
from django.utils.http import url_has_allowed_host_and_scheme

from .models import CategoriaAjuda, ArtigoAjuda


def central_ajuda(request):

    categorias = (
        CategoriaAjuda.objects
        .filter(ativo=True)
        .order_by('ordem', 'nome')
    )

    artigos_recentes = (
        ArtigoAjuda.objects
        .filter(
            ativo=True,
            categoria__ativo=True
        )
        .select_related('categoria')
        .order_by('-criado_em')[:6]
    )

    context = {
        'categorias': categorias,
        'artigos_recentes': artigos_recentes,
    }

    return render(
        request,
        'ajuda/index.html',
        context
    )


def categoria_ajuda(request, slug):

    categoria = get_object_or_404(
        CategoriaAjuda,
        slug=slug,
        ativo=True
    )

    artigos = (
        categoria.artigos
        .filter(ativo=True)
        .order_by('ordem', 'titulo')
    )

    context = {
        'categoria': categoria,
        'artigos': artigos,
    }

    return render(
        request,
        'ajuda/categoria.html',
        context
    )


def artigo_ajuda(request, slug):

    artigo = get_object_or_404(
        ArtigoAjuda.objects.select_related('categoria'),
        slug=slug,
        ativo=True,
        categoria__ativo=True
    )

    ArtigoAjuda.objects.filter(
        pk=artigo.pk
    ).update(
        visualizacoes=F('visualizacoes') + 1
    )

    artigo.refresh_from_db()

    artigos_relacionados = (
        ArtigoAjuda.objects
        .filter(
            categoria=artigo.categoria,
            ativo=True
        )
        .exclude(pk=artigo.pk)
        .order_by('ordem', 'titulo')[:5]
    )

    # =========================================================
    # URL PARA RETORNAR À PÁGINA DE ORIGEM
    # =========================================================

    next_url = request.GET.get('next', '').strip()

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        voltar_url = next_url
    else:
        voltar_url = ''

    context = {
        'artigo': artigo,
        'artigos_relacionados': artigos_relacionados,
        'voltar_url': voltar_url,
    }

    return render(
        request,
        'ajuda/artigo.html',
        context
    )


def pesquisar_ajuda(request):

    termo = request.GET.get(
        'q',
        ''
    ).strip()

    artigos = ArtigoAjuda.objects.none()

    if termo:

        artigos = (
            ArtigoAjuda.objects
            .filter(
                Q(titulo__icontains=termo) |
                Q(resumo__icontains=termo) |
                Q(conteudo__icontains=termo),
                ativo=True,
                categoria__ativo=True
            )
            .select_related('categoria')
            .order_by('titulo')
        )

    context = {
        'termo': termo,
        'artigos': artigos,
    }

    return render(
        request,
        'ajuda/pesquisa.html',
        context
    )
