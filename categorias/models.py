from django.db import models


class Categoria(models.Model):
    nome = models.CharField(
        max_length=100, unique=True, verbose_name="Nome da Categoria"
    )
    descricao = models.TextField(
        blank=True, null=True, verbose_name="Descrição"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome