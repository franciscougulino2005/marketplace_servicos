from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Cliente, Profissional, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):

    list_display = (
        "email",
        "first_name",
        "last_name",
        "tipo_usuario",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "tipo_usuario",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

    ordering = (
        "first_name",
        "last_name",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Informações da plataforma",
            {
                "fields": (
                    "tipo_usuario",
                    "telefone",
                    "data_cadastro",
                )
            },
        ),
    )

    readonly_fields = (
        "data_cadastro",
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):

    list_display = (
        "usuario",
        "cpf",
        "cidade",
        "estado",
    )

    search_fields = (
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",
        "cpf",
    )

    list_filter = (
        "estado",
    )


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):

    list_display = (
        "nome_profissional",
        "usuario",
        "cidade",
        "estado",
        "aprovado",
        "ativo",
    )

    list_filter = (
        "aprovado",
        "ativo",
        "estado",
    )

    search_fields = (
        "nome_profissional",
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",
        "cpf",
    )

    actions = [
        "aprovar_profissionais",
    ]

    @admin.action(description="Aprovar profissionais selecionados")
    def aprovar_profissionais(self, request, queryset):

        from django.utils import timezone

        queryset.update(
            aprovado=True,
            data_aprovacao=timezone.now(),
        )