from django.core.validators import MinValueValidator
from django.db import models


class Solicitacao(models.Model):

    class Status(models.TextChoices):
        ABERTA = "ABERTA", "Aberta"
        RECEBENDO_ORCAMENTOS = (
            "RECEBENDO_ORCAMENTOS",
            "Recebendo orçamentos",
        )
        ORCAMENTO_ACEITO = (
            "ORCAMENTO_ACEITO",
            "Orçamento aceito",
        )
        EM_EXECUCAO = (
            "EM_EXECUCAO",
            "Em execução",
        )
        AGUARDANDO_PAGAMENTO = (
            "AGUARDANDO_PAGAMENTO",
            "Aguardando pagamento",
        )
        CONCLUIDA = "CONCLUIDA", "Concluída"
        CANCELADA = "CANCELADA", "Cancelada"

    cliente = models.ForeignKey(
        "usuarios.Cliente",
        on_delete=models.PROTECT,
        related_name="solicitacoes",
        verbose_name="Cliente",
    )

    categoria = models.ForeignKey(
        "servicos.Categoria",
        on_delete=models.PROTECT,
        related_name="solicitacoes",
        verbose_name="Categoria",
    )

    titulo = models.CharField(
        max_length=200,
        verbose_name="Título",
    )

    descricao = models.TextField(
        verbose_name="Descrição",
    )

    cidade = models.CharField(
        max_length=100,
        verbose_name="Cidade",
    )

    estado = models.CharField(
        max_length=2,
        verbose_name="Estado",
    )

    endereco = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Endereço",
    )

    numero = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Número",
    )

    bairro = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Bairro",
    )

    cep = models.CharField(
        max_length=9,
        blank=True,
        verbose_name="CEP",
    )

    data_desejada = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data desejada",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ABERTA,
        verbose_name="Status",
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de criação",
    )

    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última atualização",
    )

    class Meta:
        verbose_name = "Solicitação"
        verbose_name_plural = "Solicitações"
        ordering = ["-data_criacao"]

    def __str__(self):
        return f"#{self.pk} - {self.titulo}"


class SolicitacaoFoto(models.Model):

    solicitacao = models.ForeignKey(
        Solicitacao,
        on_delete=models.CASCADE,
        related_name="fotos",
        verbose_name="Solicitação",
    )

    imagem = models.ImageField(
        upload_to="solicitacoes/",
        verbose_name="Imagem",
    )

    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de cadastro",
    )

    class Meta:
        verbose_name = "Foto da solicitação"
        verbose_name_plural = "Fotos das solicitações"
        ordering = ["data_cadastro"]

    def __str__(self):
        return f"Foto da solicitação #{self.solicitacao_id}"


class Orcamento(models.Model):

    class Status(models.TextChoices):
        ENVIADO = "ENVIADO", "Enviado"
        ACEITO = "ACEITO", "Aceito"
        RECUSADO = "RECUSADO", "Recusado"
        CANCELADO = "CANCELADO", "Cancelado"
        EXPIRADO = "EXPIRADO", "Expirado"

    solicitacao = models.ForeignKey(
        Solicitacao,
        on_delete=models.CASCADE,
        related_name="orcamentos",
        verbose_name="Solicitação",
    )

    profissional = models.ForeignKey(
        "usuarios.Profissional",
        on_delete=models.PROTECT,
        related_name="orcamentos",
        verbose_name="Profissional",
    )

    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(0)
        ],
        verbose_name="Valor",
    )

    descricao = models.TextField(
        verbose_name="Descrição do orçamento",
    )

    prazo_execucao = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Prazo de execução",
        help_text="Prazo em dias.",
    )

    validade = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Validade",
        help_text="Validade do orçamento em dias.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ENVIADO,
        verbose_name="Status",
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de criação",
    )

    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última atualização",
    )

    class Meta:
        verbose_name = "Orçamento"
        verbose_name_plural = "Orçamentos"
        ordering = ["-data_criacao"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "solicitacao",
                    "profissional",
                ],
                name="unique_orcamento_solicitacao_profissional",
            )
        ]

    def __str__(self):
        return (
            f"Orçamento #{self.pk} - "
            f"{self.profissional.nome_profissional}"
        )


class Contratacao(models.Model):

    class Status(models.TextChoices):
        AGUARDANDO_PAGAMENTO = (
            "AGUARDANDO_PAGAMENTO",
            "Aguardando pagamento",
        )
        PAGAMENTO_CONFIRMADO = (
            "PAGAMENTO_CONFIRMADO",
            "Pagamento confirmado",
        )
        EM_EXECUCAO = (
            "EM_EXECUCAO",
            "Em execução",
        )
        SERVICO_CONCLUIDO = (
            "SERVICO_CONCLUIDO",
            "Serviço concluído",
        )
        PAGAMENTO_LIBERADO = (
            "PAGAMENTO_LIBERADO",
            "Pagamento liberado",
        )
        CANCELADA = (
            "CANCELADA",
            "Cancelada",
        )

    solicitacao = models.OneToOneField(
        Solicitacao,
        on_delete=models.PROTECT,
        related_name="contratacao",
        verbose_name="Solicitação",
    )

    orcamento = models.OneToOneField(
        Orcamento,
        on_delete=models.PROTECT,
        related_name="contratacao",
        verbose_name="Orçamento",
    )

    cliente = models.ForeignKey(
        "usuarios.Cliente",
        on_delete=models.PROTECT,
        related_name="contratacoes",
        verbose_name="Cliente",
    )

    profissional = models.ForeignKey(
        "usuarios.Profissional",
        on_delete=models.PROTECT,
        related_name="contratacoes",
        verbose_name="Profissional",
    )

    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(0)
        ],
        verbose_name="Valor contratado",
    )

    percentual_comissao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        validators=[
            MinValueValidator(0)
        ],
        verbose_name="Percentual de comissão",
    )

    valor_comissao = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0)
        ],
        verbose_name="Valor da comissão",
    )

    valor_profissional = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0)
        ],
        verbose_name="Valor do profissional",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.AGUARDANDO_PAGAMENTO,
        verbose_name="Status",
    )

    data_contratacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da contratação",
    )

    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última atualização",
    )

    class Meta:
        verbose_name = "Contratação"
        verbose_name_plural = "Contratações"
        ordering = ["-data_contratacao"]

    def __str__(self):
        return (
            f"Contratação #{self.pk} - "
            f"{self.profissional.nome_profissional} - "
            f"R$ {self.valor:.2f}"
        )


class Pagamento(models.Model):

    class Status(models.TextChoices):
        PENDENTE = (
            "PENDENTE",
            "Pendente",
        )
        PROCESSANDO = (
            "PROCESSANDO",
            "Processando",
        )
        APROVADO = (
            "APROVADO",
            "Aprovado",
        )
        RECUSADO = (
            "RECUSADO",
            "Recusado",
        )
        CANCELADO = (
            "CANCELADO",
            "Cancelado",
        )
        ESTORNADO = (
            "ESTORNADO",
            "Estornado",
        )

    class Metodo(models.TextChoices):
        PIX = (
            "PIX",
            "PIX",
        )
        CARTAO = (
            "CARTAO",
            "Cartão",
        )
        BOLETO = (
            "BOLETO",
            "Boleto",
        )

    contratacao = models.OneToOneField(
        "Contratacao",
        on_delete=models.PROTECT,
        related_name="pagamento",
        verbose_name="Contratação",
    )

    cliente = models.ForeignKey(
        "usuarios.Cliente",
        on_delete=models.PROTECT,
        related_name="pagamentos",
        verbose_name="Cliente",
    )

    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(0)
        ],
        verbose_name="Valor",
    )

    metodo = models.CharField(
        max_length=20,
        choices=Metodo.choices,
        verbose_name="Método de pagamento",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
        verbose_name="Status",
    )

    identificador_transacao = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Identificador da transação",
        help_text="Identificador fornecido pelo gateway de pagamento.",
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de criação",
    )

    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última atualização",
    )

    data_pagamento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data do pagamento",
    )

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-data_criacao"]

    def __str__(self):
        return (
            f"Pagamento #{self.pk} - "
            f"R$ {self.valor:.2f} - "
            f"{self.get_status_display()}"
        )