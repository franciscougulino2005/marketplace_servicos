from django import forms
from django.contrib.auth.forms import AuthenticationForm

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
        }


class ProfissionalForm(forms.ModelForm):

    class Meta:
        model = Profissional
        exclude = [
            "usuario",
            "ativo",
            "aprovado",
            "data_aprovacao",
            "data_cadastro",
        ]