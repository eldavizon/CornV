from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Produto, Retirada
from .forms import ProdutoForm, RetiradaForm
from django.contrib.auth.models import User
from django.contrib import messages
from simulador.models import HistoricoPrecoEtanol, HistoricoPrecoMilho
from django.db.models import Avg
from django.db.models.functions import TruncMonth
import json


# Create your views here.

@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def index(request):
    
    # Filtrar os registros a cada 6 meses, utilizando o mês truncado
    historico_etanol = (
        HistoricoPrecoEtanol.objects
        .annotate(mes=TruncMonth('data'))  # Trunca a data para o primeiro dia do mês
        .filter(mes__month__in=[1, 4, 7, 10])  # Filtra apenas os meses de janeiro e julho (a cada 6 meses)
        .values('mes')
        .annotate(preco_medio=Avg('preco_etanol'))  # Média do preço de etanol por período de 6 meses
        .order_by('mes')
    )

    historico_milho = (
        HistoricoPrecoMilho.objects
        .annotate(mes=TruncMonth('data'))
        .filter(mes__month__in=[1, 4, 7, 10])  # Filtra apenas os meses de janeiro e julho (a cada 6 meses)
        .values('mes')
        .annotate(preco_medio=Avg('preco_milho'))
        .order_by('mes')
    )

    # Preparar os dados para os gráficos
    datas_etanol = [registro['mes'].strftime("%Y-%m-%d") for registro in historico_etanol]
    precos_etanol = [float(registro['preco_medio']) for registro in historico_etanol]

    datas_milho = [registro['mes'].strftime("%Y-%m-%d") for registro in historico_milho]
    precos_milho = [float(registro['preco_medio']) for registro in historico_milho]
        
    
    if request.method == "POST":
        form = RetiradaForm(request.POST)
        
        if form.is_valid():
            
            instance = form.save(commit=False) # Não se salva o formulario imediatamente para que seja possivel adicionar o usuario
            instance.staff = request.user   # Adiciona-se o usuário às informações do formulario aqui
            instance.save()     #Agora sim, pode-se salvar.
            
            return redirect('estatisticas-index')
        
    else:
        form = RetiradaForm()
        
    
    context = {
        "datas_etanol": json.dumps(datas_etanol),
        "precos_etanol": json.dumps(precos_etanol),
        "datas_milho": json.dumps(datas_milho),
        "precos_milho": json.dumps(precos_milho),
    }
    
    return render(request, 'estatisticas/index.html', context)



@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def staff(request):
    
    workers = User.objects.all()
    
    retiradas = Retirada.objects.all()
    
    produtos = Produto.objects.all()

    
    #Soma as quantidades de produtos, usuarios e retiradas para exibir
    workers_count = workers.count()
    produtos_count = produtos.count()
    retiradas_count = retiradas.count()
    
    context = {
        'workers' : workers,
        'workers_count' : workers_count,
        'produtos_count' : produtos_count,
        'retiradas_count' :  retiradas_count,
    }
    
    return render(request, 'estatisticas/staff.html', context)



@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def staff_detail(request, pk):
    
    workers = User.objects.get(id = pk)
    
    context = {
                'workers' : workers
    }

    return render(request, 'estatisticas/staff_detail.html', context)

@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def produtos(request):
    
    items = Produto.objects.all()
    #    items = Produto.objects.raw() significaria usar o código SQL bruto ao invés do ORM.
    
    workers = User.objects.all()
    
    retiradas = Retirada.objects.all()
        
    #Soma as quantidades de produtos, usuarios e retiradas para exibir
    workers_count = workers.count()
    produtos_count = items.count()
    retiradas_count = retiradas.count()

    if request.method=="POST":
        form = ProdutoForm(request.POST)
        
        if form.is_valid():
            form.save()
            
            nome_produto = form.cleaned_data.get('nome')
            messages.success(request, f'O produto {nome_produto} foi registrado.')
            
            return redirect('estatisticas-produtos')
    else:
        form = ProdutoForm()
    
        
    context= {
        'items': items,
        'form' : form,
        'workers_count' : workers_count,
        'produtos_count' : produtos_count,
        'retiradas_count' :  retiradas_count,
    }
    
    return render(request, 'estatisticas/produtos.html', context)



@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def produtos_delete(request, pk):
    
    item = Produto.objects.get(id = pk)
    
    if request.method=="POST":
        item.delete()
        return redirect('estatisticas-produtos')
    
    return render(request, 'estatisticas/produtos_delete.html')



@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def produtos_update(request, pk):
    
    item = Produto.objects.get(id = pk)
        
    if request.method=="POST":
        form = ProdutoForm(request.POST, instance = item)
        
        if form.is_valid():
            form.save()
            return redirect('estatisticas-produtos')        
    else:
        form = ProdutoForm(instance = item)
        
    context = {
        'form': form, 
    }
    
    return render(request, 'estatisticas/produtos_update.html', context)



@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def retirada(request):
    
    retiradas = Retirada.objects.all()
    produtos = Produto.objects.all()
    workers = User.objects.all()
    
        
    #Soma as quantidades de produtos, usuarios e retiradas para exibir
    workers_count = workers.count()
    produtos_count = produtos.count()
    retiradas_count = retiradas.count()
    
    context = {
        'retiradas' : retiradas,
        'workers_count' : workers_count,
        'produtos_count' : produtos_count,
        'retiradas_count' :  retiradas_count,
    }
    
    return render(request, 'estatisticas/retirada.html', context)
