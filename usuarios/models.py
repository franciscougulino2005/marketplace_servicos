from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class Usuario(AbstractUser):

    class TipoUsuario(models.TextChoices):
        CLIENTE = "CLIENTE", "Cliente"
        PROFISSIONAL = "PROFISSIONAL", "Profissional"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    tipo_usuario = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.CLIENTE,
        verbose_name="Tipo de usuário",
    )

    email = models.EmailField(
        unique=True,
        verbose_name="E-mail",
    )

    telefone = models.CharField(
        max_length=20,
        blank=False,
        null=False
    )

    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de cadastro",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        nome = self.get_full_name()

        if nome:
            return f"{nome} - {self.email}"

        return self.email


class Cliente(models.Model):

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="cliente",
        verbose_name="Usuário",
    )

    cpf = models.CharField(
        max_length=14,
        unique=True,
        verbose_name="CPF",
    )

    data_nascimento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de nascimento",
    )

    cidade = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Cidade",
    )

    estado = models.CharField(
        max_length=2,
        blank=True,
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

    complemento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Complemento",
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

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.email


class Profissional(models.Model):

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="profissional",
        verbose_name="Usuário",
    )

    categorias = models.ManyToManyField(
        "categorias.Categoria",
        related_name="profissionais",
        blank=True,
        verbose_name="Categorias de Atendimento",
    )

    cpf = models.CharField(
        max_length=14,
        unique=True,
        verbose_name="CPF",
    )

    nome_profissional = models.CharField(
        max_length=150,
        verbose_name="Nome profissional",
    )

    foto = models.ImageField(
        upload_to="profissionais/",
        null=True,
        blank=True,
        verbose_name="Foto",
    )

    descricao = models.TextField(
        blank=True,
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

    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )

    aprovado = models.BooleanField(
        default=False,
        verbose_name="Aprovado",
    )

    mercado_pago_user_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        verbose_name="ID do usuário Mercado Pago",
    )

    mercado_pago_connected = models.BooleanField(
        default=False,
        verbose_name="Mercado Pago conectado",
    )

    mercado_pago_connected_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de conexão Mercado Pago",
    )

    data_aprovacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de aprovação",
    )

    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de cadastro",
    )

    class Meta:
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"
        ordering = ["nome_profissional"]

    def __str__(self):
        return self.nome_profissional