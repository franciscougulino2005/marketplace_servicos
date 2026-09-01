from django import forms
from django.contrib.auth.forms import AuthenticationForm

from categorias.models import Categoria
from .models import Usuario, Cliente, Profissional


class LoginForm(AuthenticationForm):

    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={
                "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                "placeholder": "seu@email.com",
                "autocomplete": "email",
            }
        ),
    )

    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                "placeholder": "Sua senha",
                "autocomplete": "current-password",
            }
        ),
    )


class CadastroForm(forms.ModelForm):

    password1 = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                "placeholder": "Digite sua senha",
            }
        ),
    )

    password2 = forms.CharField(
        label="Confirme a senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                "placeholder": "Digite a senha novamente",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["telefone"].required = True
        self.fields["telefone"].error_messages = {
            "required": "O preenchimento do telefone é obrigatório."
        }

    class Meta:
        model = Usuario
        fields = [
            "first_name",
            "last_name",
            "email",
            "telefone",
            "tipo_usuario",
        ]

        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "email": "E-mail",
            "telefone": "Telefone",
            "tipo_usuario": "Quero me cadastrar como",
        }

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5"
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5"
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5"
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5"
                }
            ),
            "tipo_usuario": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5"
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()

        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Já existe um usuário cadastrado com este e-mail."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        senha1 = cleaned_data.get("password1")
        senha2 = cleaned_data.get("password2")

        if senha1 and senha2 and senha1 != senha2:
            self.add_error(
                "password2",
                "As senhas não conferem.",
            )

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)

        usuario.username = self.cleaned_data["email"]
        usuario.set_password(self.cleaned_data["password1"])

        if commit:
            usuario.save()

        return usuario


class ClienteForm(forms.ModelForm):

    class Meta:
        model = Cliente
        exclude = ["usuario"]

        widgets = {
            "cpf": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                    "placeholder": "000.000.000-00",
                }
            ),
            "data_nascimento": forms.DateInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                    "type": "date",
                }
            ),
            "cidade": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                }
            ),
            "estado": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                    "placeholder": "UF",
                }
            ),
            "endereco": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                }
            ),
            "numero": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                }
            ),
            "complemento": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                }
            ),
            "bairro": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                }
            ),
            "cep": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                    "placeholder": "00000-000",
                }
            ),
        }


class ProfissionalForm(forms.ModelForm):

    categorias = forms.ModelMultipleChoiceField(
        queryset=Categoria.objects.filter(ativo=True).order_by("nome"),
        widget=forms.SelectMultiple(
            attrs={
                "id": "id_categorias_profissional",
                "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
            }
        ),
        required=False,
        label="Categorias de Atendimento",
    )

    class Meta:
        model = Profissional
        exclude = [
            "usuario",
            "ativo",
            "aprovado",
            "data_aprovacao",
            "data_cadastro",
            "mercado_pago_user_id",
            "mercado_pago_connected",
            "mercado_pago_connected_at",
        ]

        widgets = {
            "cpf": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                    "placeholder": "000.000.000-00",
                }
            ),
            "nome_profissional": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                    "placeholder": "Seu nome público ou da sua empresa",
                }
            ),
            "foto": forms.FileInput(
                attrs={
                    "class": "w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100",
                }
            ),
            "descricao": forms.Textarea(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                    "rows": 4,
                    "placeholder": "Descreva sua experiência, serviços oferecidos e diferenciais...",
                }
            ),
            "cidade": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                }
            ),
            "estado": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5",
                    "placeholder": "UF",
                }
            ),
        }