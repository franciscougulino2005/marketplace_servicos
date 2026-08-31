from django import forms
from .models import Solicitacao, Orcamento
from categorias.models import Categoria

# Estilo padrão para os inputs com bom contraste
INPUT_STYLE = 'bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 shadow-sm'

class SolicitacaoForm(forms.ModelForm):
    # Declaramos o campo categoria explicitamente para aceitar a busca por texto limpo
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        to_field_name="nome",
        widget=forms.TextInput(attrs={
            'id': 'id_categoria_input',
            'class': INPUT_STYLE,
            'placeholder': 'Digite para buscar a categoria...',
            'autocomplete': 'off'
        }),
        label='Categoria'
    )

    class Meta:
        model = Solicitacao
        fields = [
            'titulo',
            'categoria',
            'descricao',
            'cidade',
            'estado',
            'endereco',
            'numero',
            'bairro',
            'cep',
            'data_desejada',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Ex: Preciso de manutenção no quadro elétrico'}),
            'descricao': forms.Textarea(attrs={'class': INPUT_STYLE, 'rows': 4, 'placeholder': 'Descreva detalhadamente o que precisa...'}),
            'cidade': forms.TextInput(attrs={'class': INPUT_STYLE}),
            'estado': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'UF'}),
            'endereco': forms.TextInput(attrs={'class': INPUT_STYLE}),
            'numero': forms.TextInput(attrs={'class': INPUT_STYLE}),
            'bairro': forms.TextInput(attrs={'class': INPUT_STYLE}),
            'cep': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': '00000-000'}),
            'data_desejada': forms.DateInput(attrs={'type': 'date', 'class': INPUT_STYLE}),
        }

class OrcamentoForm(forms.ModelForm):
    class Meta:
        model = Orcamento
        fields = ['valor', 'descricao', 'prazo_execucao', 'validade']
        widgets = {
            'valor': forms.NumberInput(attrs={'step': '0.01', 'class': INPUT_STYLE}),
            'descricao': forms.Textarea(attrs={'rows': 4, 'class': INPUT_STYLE}),
            'prazo_execucao': forms.NumberInput(attrs={'class': INPUT_STYLE}),
            'validade': forms.NumberInput(attrs={'class': INPUT_STYLE}),
        }