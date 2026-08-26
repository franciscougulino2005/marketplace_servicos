from django import forms

from .models import Servico


class ServicoForm(forms.ModelForm):

    class Meta:
        model = Servico

        fields = [
            "categoria",
            "nome",
            "descricao",
            "preco_referencia",
        ]

        labels = {
            "categoria": "Categoria",
            "nome": "Nome do serviço",
            "descricao": "Descrição",
            "preco_referencia": "Preço de referência",
        }

        widgets = {
            "categoria": forms.Select(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5 "
                        "bg-white"
                    ),
                }
            ),

            "nome": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "placeholder": "Ex.: Instalação de tomadas",
                }
            ),

            "descricao": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "rows": 5,
                    "placeholder": (
                        "Descreva detalhadamente o serviço..."
                    ),
                }
            ),

            "preco_referencia": forms.NumberInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-2.5"
                    ),
                    "placeholder": "0,00",
                    "step": "0.01",
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["categoria"].queryset = (
            self.fields["categoria"]
            .queryset
            .filter(ativo=True)
        )