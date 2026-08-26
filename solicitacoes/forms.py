from django import forms

from servicos.models import Categoria

from .models import (
    Orcamento,
    Solicitacao,
)


class SolicitacaoForm(forms.ModelForm):

    class Meta:
        model = Solicitacao

        fields = [
            "categoria",
            "titulo",
            "descricao",
            "cidade",
            "estado",
            "endereco",
            "numero",
            "bairro",
            "cep",
            "data_desejada",
        ]

        labels = {
            "categoria": "Categoria do serviço",
            "titulo": "O que você precisa?",
            "descricao": "Descreva o serviço",
            "cidade": "Cidade",
            "estado": "Estado",
            "endereco": "Endereço",
            "numero": "Número",
            "bairro": "Bairro",
            "cep": "CEP",
            "data_desejada": "Data desejada",
        }

        widgets = {

            "categoria": forms.Select(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 bg-white "
                        "px-4 py-2.5"
                    ),
                }
            ),

            "titulo": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "placeholder": (
                        "Ex.: Preciso pintar minha casa"
                    ),
                }
            ),

            "descricao": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "rows": 6,
                    "placeholder": (
                        "Explique o que precisa ser feito, "
                        "dimensões, quantidade, detalhes etc."
                    ),
                }
            ),

            "cidade": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "placeholder": "João Pessoa",
                }
            ),

            "estado": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5 uppercase"
                    ),
                    "placeholder": "PB",
                    "maxlength": "2",
                }
            ),

            "endereco": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                }
            ),

            "numero": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                }
            ),

            "bairro": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                }
            ),

            "cep": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "placeholder": "00000-000",
                }
            ),

            "data_desejada": forms.DateInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["categoria"].queryset = (
            Categoria.objects
            .filter(ativo=True)
            .order_by("nome")
        )

    def clean_estado(self):

        estado = self.cleaned_data["estado"]

        return estado.upper().strip()

    def clean(self):

        cleaned_data = super().clean()

        cidade = cleaned_data.get("cidade")
        estado = cleaned_data.get("estado")

        if cidade:
            cleaned_data["cidade"] = cidade.strip()

        if estado:
            cleaned_data["estado"] = estado.upper().strip()

        return cleaned_data


class OrcamentoForm(forms.ModelForm):

    class Meta:
        model = Orcamento

        fields = [
            "valor",
            "descricao",
            "prazo_execucao",
            "validade",
        ]

        labels = {
            "valor": "Valor do orçamento",
            "descricao": "Descrição",
            "prazo_execucao": "Prazo de execução",
            "validade": "Validade do orçamento",
        }

        widgets = {

            "valor": forms.NumberInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0,00",
                }
            ),

            "descricao": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "rows": 6,
                    "placeholder": (
                        "Explique o que está incluído no orçamento..."
                    ),
                }
            ),

            "prazo_execucao": forms.NumberInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "min": "1",
                    "placeholder": "Ex.: 3",
                }
            ),

            "validade": forms.NumberInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "min": "1",
                    "placeholder": "Ex.: 7",
                }
            ),
        }

    def clean_valor(self):

        valor = self.cleaned_data["valor"]

        if valor <= 0:

            raise forms.ValidationError(
                "O valor do orçamento deve ser maior que zero."
            )

        return valor