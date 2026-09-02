from django.db.models import Sum
from django.utils import timezone
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from solicitacoes.models import Contratacao


@staff_member_required
def relatorio_comissoes(request):
    hoje = timezone.now().date()

    # Pega o mês e o ano separadamente da requisição (GET), ou usa o atual como padrão
    try:
        mes_selecionado = int(request.GET.get('mes', hoje.month))
    except ValueError:
        mes_selecionado = hoje.month

    try:
        ano_selecionado = int(request.GET.get('ano', hoje.year))
    except ValueError:
        ano_selecionado = hoje.year

    # Filtra as contratações com base no mês e ano selecionados
    contratacoes = Contratacao.objects.filter(
        data_contratacao__year=ano_selecionado,
        data_contratacao__month=mes_selecionado,
        status__in=[
            Contratacao.Status.SERVICO_CONCLUIDO,
            Contratacao.Status.PAGAMENTO_LIBERADO,
            Contratacao.Status.PAGAMENTO_CONFIRMADO
        ]
    ).order_by('-data_contratacao')

    # Totais consolidados do período
    totais = contratacoes.aggregate(
        total_bruto=Sum('valor'),
        total_comissao=Sum('valor_comissao'),
        total_profissional=Sum('valor_profissional')
    )

    # Dados para popular os selects no template
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]

    # Gera os últimos 5 anos para seleção
    anos = range(hoje.year, hoje.year - 5, -1)

    context = {
        'contratacoes': contratacoes,
        'totais': totais,
        'meses': meses,
        'anos': anos,
        'mes_selecionado': mes_selecionado,
        'ano_selecionado': ano_selecionado,
    }
    return render(request, 'relatorios_administrativos/comissoes.html', context)


@staff_member_required
def dashboard_administrativo(request):
    return render(request, 'relatorios_administrativos/dashboard.html')