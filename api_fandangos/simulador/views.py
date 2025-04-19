from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import HistoricoPrecoEtanol, HistoricoPrecoMilho, CalculoART, DadosFS
from .forms import CalculoARTForm
from django.contrib import messages




# Create your views here.

@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def index(request):
    return render(request, 'simulador/index.html')

def calcular_rendimento(request):
    
    items = CalculoART.objects.all()
    dados_fs = DadosFS.objects.all()
    #    items = Produto.objects.raw() significaria usar o código SQL bruto ao invés do ORM.
    
    if request.method=="POST":
        form = CalculoARTForm(request.POST)
        
        if form.is_valid():
            form = form.save(commit=False)
            
            # multiplica-se pela quantidade media de amido no milho (63%), pelo fator de conversão pra art (1,11) e pela eficiencia das enzimas (97%),
            #e por 99% (teor de amido hidrolisável)
            
            #constantes
            teor_amido = 0.63
            amido_hidrolisavel = 0.99
            eficiencia_enzima = 0.97
            fator_hidratacao = 1.11
            
            calculo_art = form.quantidade_milho * teor_amido * amido_hidrolisavel * eficiencia_enzima  * fator_hidratacao
            
            form.quantidade_art = round(calculo_art , 4)
            
            
            # multiplica-se pela quantidade de etanol absoluto produzido por g de art (0,6475)
            # e soma-se pela quantidade de AR já contida no milho (2,3%) multiplicada pelo fator de produção (0,6475)
            
            #constantes
            rendimento = 0.9148
            fator_etanol_art = 0.647549868378450666554049298253020
            teor_ar = 0.023
            
            volume_etanol_art = calculo_art * fator_etanol_art * rendimento
            volume_etanol_ar = form.quantidade_milho * teor_ar * fator_etanol_art * rendimento
            total_etanol_abs = volume_etanol_ar + volume_etanol_art
            
            form.volume_etanol = round(total_etanol_abs, 2)
            
            # l/kg = produzido / milho de entrada
            form.proporcao_producao = round((total_etanol_abs / form.quantidade_milho), 4)
            
            # rendimento percentual:
            
            # teoricamente, 1 kg de milho produz 0.4497L de etanol absoluto
            proporcao_teorica = 0.4497
            teorico_produzido = proporcao_teorica * form.quantidade_milho
            
            form.rendimento_percentual = round(((total_etanol_abs / teorico_produzido) * 100), 2)
            
            form.save() 
            quantidade = form.quantidade_milho
            messages.success(request, f'{quantidade}kg de milho foram convertidos para ART e etanol.')
            
            return redirect('calcular-rendimento')
    else:
        form = CalculoARTForm()
    
        
    context= {
        'items': items,
        'form' : form,
    }
    
    return render(request, 'simulador/calc_art.html', context)




def obter_dados_historico(request):
    try:
        historico_etanol = HistoricoPrecoEtanol.objects.order_by("data")
        historico_milho = HistoricoPrecoMilho.objects.order_by("data")

        datas_etanol = [registro.data.strftime("%Y-%m-%d") for registro in historico_etanol]
        precos_etanol = [float(registro.preco_etanol) for registro in historico_etanol]

        datas_milho = [registro.data.strftime("%Y-%m-%d") for registro in historico_milho]
        precos_milho = [float(registro.preco_milho) for registro in historico_milho]

        context = {
            "datas_etanol": json.dumps(datas_etanol),
            "precos_etanol": json.dumps(precos_etanol),
            "datas_milho": json.dumps(datas_milho),
            "precos_milho": json.dumps(precos_milho),
        }
        
        return render(request, "simulador/serie_historica.html", context)

    except Exception as e:
        return render(request, "simulador/serie_historica.html", {
            "error": f"Erro ao obter dados: {str(e)}"
        })