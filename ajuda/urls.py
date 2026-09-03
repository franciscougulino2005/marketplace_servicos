from django.urls import path

from . import views


app_name = 'ajuda'


urlpatterns = [

    path(
        '',
        views.central_ajuda,
        name='index'
    ),

    path(
        'pesquisar/',
        views.pesquisar_ajuda,
        name='pesquisar'
    ),

    path(
        'categoria/<slug:slug>/',
        views.categoria_ajuda,
        name='categoria'
    ),

    path(
        'artigo/<slug:slug>/',
        views.artigo_ajuda,
        name='artigo'
    ),

]
