from django.db import models


class CategoriaAjuda(models.Model):

    PUBLICO_CHOICES = [
        ('todos', 'Todos'),
        ('cliente', 'Clientes'),
        ('profissional', 'Profissionais'),
        ('administrador', 'Administradores'),
    ]

    nome = models.CharField(
        max_length=150,
        verbose_name='Nome'
    )

    slug = models.SlugField(
        max_length=170,
        unique=True,
        verbose_name='Slug'
    )

    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição'
    )

    publico = models.CharField(
        max_length=20,
        choices=PUBLICO_CHOICES,
        default='todos',
        verbose_name='Público'
    )

    icone = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Ícone'
    )

    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem'
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = 'Categoria de Ajuda'
        verbose_name_plural = 'Categorias de Ajuda'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class ArtigoAjuda(models.Model):

    categoria = models.ForeignKey(
        CategoriaAjuda,
        on_delete=models.CASCADE,
        related_name='artigos',
        verbose_name='Categoria'
    )

    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
        verbose_name='Slug'
    )

    resumo = models.TextField(
        blank=True,
        null=True,
        verbose_name='Resumo'
    )

    conteudo = models.TextField(
        verbose_name='Conteúdo'
    )

    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem'
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    visualizacoes = models.PositiveIntegerField(
        default=0,
        verbose_name='Visualizações'
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = 'Artigo de Ajuda'
        verbose_name_plural = 'Artigos de Ajuda'
        ordering = ['ordem', 'titulo']

    def __str__(self):
        return self.titulo