from django.core.validators import MinValueValidator
from django.db import models

from categorias.models import Categoria


class Servico(models.Model):

    profissional = models.ForeignKey(
        "usuarios.Profissional",
        on_delete=models.CASCADE,
        related_name="servicos",
        verbose_name="Profissional",
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="servicos",
        verbose_name="Categoria",
    )

    nome = models.CharField(
        max_length=150,
        verbose_name="Nome do serviço",
    )

    descricao = models.TextField(
        verbose_name="Descrição",
    )

    preco_referencia = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0)
        ],
        verbose_name="Preço de referência",
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )

    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de cadastro",
    )

    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última atualização",
    )

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ["nome"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "profissional",
                    "categoria",
                    "nome",
                ],
                name="unique_servico_profissional",
            )
        ]

    def __str__(self):
        return (
            f"{self.nome} - "
            f"{self.profissional.nome_profissional}"
        )