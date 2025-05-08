#django
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

#models e forms
from .models import HistoricoPrecoEtanol, HistoricoPrecoMilho, CalculoART, ProcessoMoagem, ProcessoLiquefacao
from .forms import CalculoARTForm, ProcessoMoagemForm


#View de serie historica
from plotly.utils import PlotlyJSONEncoder
import plotly.graph_objects as go

#View de processo
from .modelos.moagem import calcular_moagem
from .modelos.liquefacao import simular_liquefacao  # ajuste o caminho conforme sua estrutura

#bibliotecas adicionais
import json



# Create your views here.

@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def index(request):
    return render(request, 'simulador/index.html')

@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def processo(request):
    dados_moagem = ProcessoMoagem.objects.all()
    dados_liquefacao = ProcessoLiquefacao.objects.all()

    if request.method == "POST":
        form = ProcessoMoagemForm(request.POST)

        if form.is_valid():
            print("🟢 Formulário válido")

            form_instance = form.save(commit=False)

            quantidade = float(form.cleaned_data["quantidade_milho"])
            print(f"🔍 Quantidade de milho informada: {quantidade} kg")

            # Etapa 1: Moagem
            resultado = calcular_moagem(quantidade)

            form_instance.milho_moido = resultado["massa_moida"]
            form_instance.eficiencia = resultado["eficiencia_percentual"]
            form_instance.energia_total_kj = resultado["energia_total_kJ"]

            form_instance.save()

            # Etapa 2: Liquefação com alfa-amilase (baseado na massa moída)
            resultado_liquefacao = simular_liquefacao(form_instance.milho_moido)

            liquefacao = ProcessoLiquefacao.objects.create(
                processo=form_instance,
                amido_convertido=resultado_liquefacao["massa_glicose_g"] / 1000,  # kg
                conversao_amido=resultado_liquefacao["conversao_percentual"],
                tempo_liquefacao=resultado_liquefacao["tempo_h"],
                volume_reacao_L=form_instance.milho_moido / 1.05,  # densidade 1.05 kg/L
                conc_amido_inicial=resultado_liquefacao["concentracao_amido_inicial"] / 1000,  # kg/L
                conc_amido_final=resultado_liquefacao["concentracao_amido_final"] / 1000,      # kg/L
            )

            messages.success(request, f'{quantidade} kg de milho foram moídos e liquefeitos.')
            return redirect('simulador-processo')

        else:
            print("🔴 Formulário de processo inválido")
    else:
        form = ProcessoMoagemForm()

    context = {
        'dados_moagem': dados_moagem,
        'dados_liquefacao': dados_liquefacao,
        'form': form,
    }

    return render(request, 'simulador/processo.html', context)


@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def calcular_rendimento(request):
    
    items = CalculoART.objects.all()
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


@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def obter_dados_historico(request):
    try:
        historico_etanol = HistoricoPrecoEtanol.objects.order_by("data")
        historico_milho = HistoricoPrecoMilho.objects.order_by("data")

        datas_etanol = [registro.data.strftime("%Y-%m-%d") for registro in historico_etanol]
        precos_etanol = [float(registro.preco_etanol) for registro in historico_etanol]

        datas_milho = [registro.data.strftime("%Y-%m-%d") for registro in historico_milho]
        precos_milho = [float(registro.preco_milho) for registro in historico_milho]

        # Gráfico Etanol
        fig_etanol = go.Figure()
        fig_etanol.add_trace(go.Scatter(
            x=datas_etanol,
            y=precos_etanol,
            mode='lines+markers',
            name='Etanol',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 0, 255, 0.2)'
        ))
        fig_etanol.update_layout(
            title='Preço do Etanol (R$/L)',
            xaxis_title='Data',
            yaxis_title='Preço (R$)',
            height=400
        )

        # Gráfico Milho
        fig_milho = go.Figure()
        fig_milho.add_trace(go.Scatter(
            x=datas_milho,
            y=precos_milho,
            mode='lines+markers',
            name='Milho',
            line=dict(color='green', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.2)'
        ))
        fig_milho.update_layout(
            title='Preço do Milho (R$/saca)',
            xaxis_title='Data',
            yaxis_title='Preço (R$)',
            height=400
        )

        context = {
            "grafico_etanol": json.dumps(fig_etanol, cls=PlotlyJSONEncoder),
            "grafico_milho": json.dumps(fig_milho, cls=PlotlyJSONEncoder),
        }

        return render(request, "simulador/serie_historica.html", context)

    except Exception as e:
        return render(request, "simulador/serie_historica.html", {
            "error": f"Erro ao obter dados: {str(e)}"
        })