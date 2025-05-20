from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Produto, Retirada
from .forms import ProdutoForm, RetiradaForm
from django.contrib.auth.models import User
from django.contrib import messages

# imports pra def index (view da página principal de estatísticas)
from simulador.models import HistoricoPrecoEtanol, HistoricoPrecoMilho
from .utils.agregar_quinzenalmente import agrupar_por_intervalo
from datetime import date, timedelta
import json

import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder


# Create your views here.

@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def index(request):
    
   # Datas de início e fim calculadas para 2 anos atrás.
    data_fim = date.today()
    data_inicio = date(data_fim.year - 2, data_fim.month, data_fim.day)

    # Coleta os dados de uma vez
    dados_etanol = HistoricoPrecoEtanol.objects.filter(data__range=(data_inicio, data_fim))
    dados_milho = HistoricoPrecoMilho.objects.filter(data__range=(data_inicio, data_fim))

    historico_etanol = agrupar_por_intervalo(dados_etanol, 'preco_etanol')
    historico_milho = agrupar_por_intervalo(dados_milho, 'preco_milho')

    datas_etanol = [registro['quinzena'].strftime("%Y-%m-%d") for registro in historico_etanol]
    precos_etanol = [float(registro['preco_medio']) for registro in historico_etanol]

    datas_milho = [registro['quinzena'].strftime("%Y-%m-%d") for registro in historico_milho]
    precos_milho = [float(registro['preco_medio']) for registro in historico_milho]


    # Últimas cotações para exibir nos cards da página principal
    ultima_cotacao_milho = HistoricoPrecoMilho.objects.values('data', 'preco_milho').last()
    ultima_cotacao_etanol = HistoricoPrecoEtanol.objects.values('data', 'preco_etanol').last()
    
    # Cria o gráfico do Etanol
    fig_etanol = go.Figure()
    fig_etanol.add_trace(go.Scatter(
        x=datas_etanol,
        y=precos_etanol,
        mode='lines+markers',
        name='Etanol',
        line=dict(color='rgba(75, 192, 192, 1)', width=2),
        fill='tozeroy',
        fillcolor='rgba(75, 192, 192, 0.2)'
    ))
    fig_etanol.update_layout(
        title='Preço do Etanol (R$/L)',
        xaxis_title='Data',
        yaxis_title='Preço (R$)',
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    # Cria o gráfico do Milho
    fig_milho = go.Figure()
    fig_milho.add_trace(go.Scatter(
        x=datas_milho,
        y=precos_milho,
        mode='lines+markers',
        name='Milho',
        line=dict(color='rgba(255, 159, 64, 1)', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 159, 64, 0.2)'
    ))
    fig_milho.update_layout(
        title='Preço do Milho (R$/60kg)',
        xaxis_title='Data',
        yaxis_title='Preço (R$)',
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )


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
        "grafico_etanol": json.dumps(fig_etanol, cls=PlotlyJSONEncoder),
        "grafico_milho": json.dumps(fig_milho, cls=PlotlyJSONEncoder),
        "ultima_cotacao_milho": ultima_cotacao_milho,
        "ultima_cotacao_etanol": ultima_cotacao_etanol,
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
