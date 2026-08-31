from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Categoria
from .forms import CategoriaForm

def e_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(e_admin)
def lista_categorias(request):
    categorias = Categoria.objects.all().order_by('nome')
    # Alterado de 'categorias/lista.html' para 'categorias/lista_categorias.html'
    return render(request, 'categorias/lista_categorias.html', {'categorias': categorias})

@login_required
@user_passes_test(e_admin)
def criar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria criada com sucesso!')
            return redirect('categorias:lista')
    else:
        form = CategoriaForm()
    return render(request, 'categorias/form.html', {'form': form, 'titulo': 'Nova Categoria'})

@login_required
@user_passes_test(e_admin)
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria atualizada com sucesso!')
            return redirect('categorias:lista')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'categorias/form.html', {'form': form, 'titulo': 'Editar Categoria'})

@login_required
@user_passes_test(e_admin)
def alternar_status_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    categoria.ativo = not categoria.ativo
    categoria.save()
    status_str = "ativada" if categoria.ativo else "desativada"
    messages.info(request, f'Categoria "{categoria.nome}" {status_str} com sucesso.')
    return redirect('categorias:lista')