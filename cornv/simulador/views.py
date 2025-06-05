from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import HistoricoPrecoEtanol, HistoricoPrecoMilho, CalculoART
from .forms import CalculoARTForm, ProcessoMoagemForm
from django.contrib import messages

#View de serie historica
from plotly.utils import PlotlyJSONEncoder
from plotly.graph_objs import Scatter, Layout, Figure
import plotly.graph_objects as go

#View de processo
  # ajuste o caminho conforme sua estrutura
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder

from .models import ProcessoMoagem, ProcessoLiquefacao, CurvaLiquefacao


from .utils import serializar_simulacoes,gerar_grafico_curva,processar_formulario_processo

from .models import ProcessoSacarificacaoFermentacao, CurvaSacFerm
from .modelos.sacferm import simular_etanol
from .utils import gerar_grafico_sacferm

# Create your views here.

@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def index(request):
    return render(request, 'simulador/index.html')


# está configurado nas settings > login_url.
@login_required(login_url='user-login')
def processo(request):
    dados_moagem = ProcessoMoagem.objects.all().order_by("-data")
    dados_liquefacao = ProcessoLiquefacao.objects.all()
    ultimas_simulacoes = ProcessoMoagem.objects.filter(liquefacao__isnull=False).order_by("-data")[:10]
    simulacoes_json = serializar_simulacoes(ultimas_simulacoes)

    grafico_liquefacao_json = None
    simulacao_selecionada = None

    simulacao_id = request.GET.get("simulacao_id")
    if simulacao_id:
        simulacao_selecionada = get_object_or_404(ProcessoMoagem, pk=simulacao_id)
        if simulacao_selecionada.liquefacao:
            curva_dados = simulacao_selecionada.liquefacao.curva_dados.all()
            grafico_liquefacao_json = gerar_grafico_curva(curva_dados)

    if request.method == "POST":
        form = ProcessoMoagemForm(request.POST)
        processo_instancia, liquefacao_instancia, erro = processar_formulario_processo(request, form)

        if erro:
            messages.error(request, f"Erro: {erro}")
            return redirect('simulador-processo')

        # —————— PARTE NOVA: usar valores de liquefação como entrada para sac/ferm ——————

        # 1) obter massa de oligossacarídeos (kg), art gerada (kg) e volume total (L)
        massa_oligos_kg = liquefacao_instancia.massa_oligossacarideos or 0.0
        art_gerada_kg = liquefacao_instancia.art_gerada or 0.0
        volume_L = liquefacao_instancia.volume_total_L or 1.0  # evitar divisão por zero

        # 2) converter para concentração em g/L
        #    (1 kg = 1000 g)
        conc_oligos_inicial = (massa_oligos_kg * 1000.0) / volume_L
        conc_glicose_inicial = (art_gerada_kg * 1000.0) / volume_L

        # 3) CHAMADA da função simular_etanol
        resultado = simular_etanol(
            concentracao_oligossacarideos_inicial=conc_oligos_inicial,
            concentracao_glicose_inicial=conc_glicose_inicial,
            concentracao_biomassa_inicial=0.1,   # mantém valor padrão; se quiser parametrizar, adicione no form
            tempo_simulacao_h=72,
            passo_temporal_h=0.1,
            Vmax_sacarificacao=2.5,
            Km_sacarificacao=50.0,
            Ki_etanol_sacarificacao=80.0,
            mu_max_fermentacao=0.4,
            Ks_fermentacao=0.5,
            Yxs_fermentacao=0.05,
            Yps_fermentacao=0.45,
            Kp_etanol_fermentacao=95.0
        )

        # 4) criar instância de ProcessoSacarificacaoFermentacao
        sacferm = ProcessoSacarificacaoFermentacao.objects.create(
            processo_liquefacao=liquefacao_instancia,
            art_inicial=conc_glicose_inicial,
            oligossacarideos_inicial=conc_oligos_inicial,
            etanol_final=resultado["concentracao_etanol_final"],
            biomassa_final=resultado["concentracao_biomassa_final"]
        )

        # 5) gravar curva temporal em CurvaSacFerm
        lista_tempo = resultado["tempo_h"]
        lista_O = resultado["oligossacarideos_g_L"]
        lista_G = resultado["glicose_g_L"]
        lista_X = resultado["biomassa_g_L"]
        lista_E = resultado["etanol_g_L"]

        curva_objs = []
        for t, O, G, X, E in zip(lista_tempo, lista_O, lista_G, lista_X, lista_E):
            curva_objs.append(
                CurvaSacFerm(
                    processo_sacferm=sacferm,
                    conc_art=G,
                    conc_oligos=O,
                    conc_etanol=E,
                    conc_biomassa=X,
                    tempo_h=t
                )
            )
        CurvaSacFerm.objects.bulk_create(curva_objs)

        # 6) refazer gráfico incluindo ART (atualizado) e exibir sac/ferm
        grafico_sacferm_json = gerar_grafico_sacferm(sacferm.curva_dados.all())

        messages.success(
            request, 
            f'{processo_instancia.quantidade_milho} kg de milho foram moídos, '
            'liquefeitos e agora simulados sacarificação/fermentação.'
        )
        return redirect(f"{request.path}?simulacao_id={processo_instancia.id}")

    else:
        form = ProcessoMoagemForm()

    context = {
        'dados_moagem': dados_moagem,
        'dados_liquefacao': dados_liquefacao,
        'form': form,
        'grafico_liquefacao': grafico_liquefacao_json,
        'ultimas_simulacoes': ultimas_simulacoes,
        'simulacao_selecionada': simulacao_selecionada,
        'simulacoes_json': simulacoes_json,
    }

    return render(request, 'simulador/processo.html', context)



@login_required(login_url='user-login')
def calcular_rendimento(request):
    # Constantes do cálculo
    teor_amido = 0.63
    amido_hidrolisavel = 0.99
    eficiencia_enzima = 0.97
    fator_hidratacao = 1.11
    rendimento = 0.9148
    fator_etanol_art = 0.647549868378450666554049298253020
    teor_ar = 0.023
    proporcao_teorica = 0.4497

    resultado_manual = None

    if request.method == "POST":
        form = CalculoARTForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            q_milho = form.quantidade_milho

            # Cálculos
            calculo_art = q_milho * teor_amido * amido_hidrolisavel * eficiencia_enzima * fator_hidratacao
            volume_etanol_art = calculo_art * fator_etanol_art * rendimento
            volume_etanol_ar = q_milho * teor_ar * fator_etanol_art * rendimento
            total_etanol_abs = volume_etanol_ar + volume_etanol_art
            teorico_produzido = proporcao_teorica * q_milho

            form.quantidade_art = round(calculo_art, 4)
            form.volume_etanol = round(total_etanol_abs, 2)
            form.proporcao_producao = round((total_etanol_abs / q_milho), 4)
            form.rendimento_percentual = round(((total_etanol_abs / teorico_produzido) * 100), 2)

            form.save()
            resultado_manual = form

            messages.success(request, f'{q_milho}kg de milho foram convertidos para ART e etanol.')
            return redirect('calcular-rendimento')
    else:
        form = CalculoARTForm()

    # Obter os 10 últimos registros de moagem
    ultimos_processos = ProcessoMoagem.objects.order_by('-data')[:10]
    quantidades_ultimas = [p.quantidade_milho for p in ultimos_processos]

    # Para cada quantidade, verifica se existe cálculo correspondente; se não, calcula e salva
    for q_milho in quantidades_ultimas:
        if not CalculoART.objects.filter(quantidade_milho=q_milho).exists():
            calculo_art = q_milho * teor_amido * amido_hidrolisavel * eficiencia_enzima * fator_hidratacao
            volume_etanol_art = calculo_art * fator_etanol_art * rendimento
            volume_etanol_ar = q_milho * teor_ar * fator_etanol_art * rendimento
            total_etanol_abs = volume_etanol_ar + volume_etanol_art
            teorico_produzido = proporcao_teorica * q_milho

            CalculoART.objects.create(
                quantidade_milho=q_milho,
                quantidade_art=round(calculo_art, 4),
                volume_etanol=round(total_etanol_abs, 2),
                proporcao_producao=round((total_etanol_abs / q_milho), 4),
                rendimento_percentual=round(((total_etanol_abs / teorico_produzido) * 100), 2)
            )

    # Obter apenas os registros condizentes com as quantidades moídas
    items_filtrados = CalculoART.objects.filter(quantidade_milho__in=quantidades_ultimas).order_by('-data')

    # Todos os cálculos (usado para a segunda tabela, se quiser no futuro)
    todos_calculos = CalculoART.objects.all().order_by('-data')

    context = {
        'form': form,
        'items': items_filtrados,
        'resultado_manual': resultado_manual,
        'todos_calculos': todos_calculos,  # Se quiser usar em outro local
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
        
        