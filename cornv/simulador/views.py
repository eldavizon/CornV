from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import HistoricoPrecoEtanol, HistoricoPrecoMilho, CalculoART, ProcessoMoagem, ProcessoLiquefacao, CurvaLiquefacao
from .forms import CalculoARTForm, ProcessoMoagemForm
from django.contrib import messages

#View de serie historica
from plotly.utils import PlotlyJSONEncoder
from plotly.graph_objs import Scatter, Layout, Figure
import plotly.graph_objects as go

#View de processo
from .modelos.moagem import calcular_moagem
from .modelos.liquefacao import simular_liquefacao  # ajuste o caminho conforme sua estrutura
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder





# Create your views here.

@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def index(request):
    return render(request, 'simulador/index.html')


# está configurado nas settings > login_url.
@login_required(login_url='user-login')
def processo(request):
    # Recupera todos os processos de moagem ordenados da data mais recente para a mais antiga
    dados_moagem = ProcessoMoagem.objects.all().order_by("-data")
    
    # Recupera todos os dados de liquefação
    dados_liquefacao = ProcessoLiquefacao.objects.all()

    # Pega as últimas 10 simulações que já possuem dados de liquefação associados
    ultimas_simulacoes = ProcessoMoagem.objects.filter(liquefacao__isnull=False).order_by("-data")[:10]

    # Serializa as últimas simulações para enviar ao JavaScript (por exemplo, para exibição em gráficos interativos)
    simulacoes_json = json.dumps([
        {
            "id": p.id,
            "data": p.data.strftime('%Y-%m-%d') if p.data else None,
            "milho": p.quantidade_milho,
            "milho_moido": p.milho_moido,
            "energia": p.energia_total,
            "liquefacao": {
                "amido": p.liquefacao.amido_convertido,
                "conversao_amido": p.liquefacao.conversao_amido,
                "tempo": p.liquefacao.tempo_liquefacao,
                "volume": p.liquefacao.volume_reacao_L,
                "conc_amido": p.liquefacao.conc_amido_final,
                "art": p.liquefacao.art_gerada,
                "percentual": p.liquefacao.conversao_amido,
                "enzima": p.liquefacao.enzima_usada,
                "grafico": [
                    {
                        "tempo": d.tempo_h,
                        "conc": d.concentracao_amido
                    } for d in p.liquefacao.curva_dados.all()
                ]
            } if hasattr(p, 'liquefacao') else None
        }
        for p in ultimas_simulacoes
    ], cls=DjangoJSONEncoder)

    # Inicializa variáveis de controle
    grafico_liquefacao_json = None
    simulacao_selecionada = None

    # ⚠️ Caso o usuário tenha clicado para visualizar uma simulação anterior
    simulacao_id = request.GET.get("simulacao_id")
    if simulacao_id:
        simulacao_selecionada = get_object_or_404(ProcessoMoagem, pk=simulacao_id)

        # Se a simulação tiver dados de liquefação, gera o gráfico Plotly da curva de concentração
        if simulacao_selecionada.liquefacao:
            curva_dados = CurvaLiquefacao.objects.filter(processo_liquefacao=simulacao_selecionada.liquefacao)
            tempos = [d.tempo_h for d in curva_dados]
            concentracoes = [d.concentracao_amido for d in curva_dados]

            fig = Figure(
                data=[Scatter(
                    x=tempos,
                    y=concentracoes,
                    mode='lines+markers',
                    name='Amido (g/L)',
                    line=dict(color='orange', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255,165,0,0.2)'
                )],
                layout=Layout(
                    title='Cinética da Liquefação Enzimática',
                    xaxis=dict(title='Tempo (h)'),
                    yaxis=dict(title='Concentração de Amido (g/L)'),
                    height=400
                )
            )

            # Serializa o gráfico para o front-end
            grafico_liquefacao_json = json.dumps(fig, cls=PlotlyJSONEncoder)

    # Se o formulário foi enviado (POST)
    if request.method == "POST":
        form = ProcessoMoagemForm(request.POST)

        if form.is_valid():
            # Cria instância do formulário sem salvar ainda no banco
            form_instance = form.save(commit=False)

            # Extrai quantidade de milho informada
            quantidade = float(form.cleaned_data["quantidade_milho"])

            # Calcula moagem com base nessa quantidade
            resultado = calcular_moagem(quantidade)

            # Preenche os campos de moagem
            form_instance.milho_moido = resultado["massa_moida"]
            form_instance.energia_total = resultado["energia_total_kWh"]
            form_instance.save()  # Agora salva no banco

            # Extrai dados para simulação de liquefação
            modo = form.cleaned_data.get("modo")
            enzima_g = form.cleaned_data.get("enzima_g")
            tempo_h = form.cleaned_data.get("tempo_h")

            # Chama a função de simulação da liquefação
            resultado_liquefacao = simular_liquefacao(
                massa_milho_kg=form_instance.milho_moido,
                enzima_g=enzima_g,
                tempo_h=tempo_h,
                modo=modo
            )

            # Se houve erro na simulação, exibe mensagem e redireciona
            if resultado_liquefacao.get("erro"):
                messages.error(request, f"Erro na liquefação: {resultado_liquefacao['erro']}")
                return redirect('simulador-processo')

            # Fator de hidratação para estimar volume de reação
            fator_hidratacao = 1.11

            # Cria instância de ProcessoLiquefacao vinculada ao processo de moagem atual
            liquefacao = ProcessoLiquefacao.objects.create(
                processo=form_instance,
                amido_convertido=resultado_liquefacao["massa_glicose_g"] / 1000,
                conversao_amido=resultado_liquefacao["conversao_percentual"],
                tempo_liquefacao=resultado_liquefacao["tempo_h"],
                volume_reacao_L=form_instance.milho_moido / 1.05,
                conc_amido_inicial=resultado_liquefacao["concentracao_amido_inicial"] / 1000,
                conc_amido_final=resultado_liquefacao["concentracao_amido_final"] / 1000,
                art_gerada=resultado_liquefacao["massa_glicose_g"] / 1000,
                enzima_usada=enzima_g if enzima_g else resultado_liquefacao["enzima_g"],
            )

            # Cria a curva de dados ponto a ponto no banco
            for tempo, concentracao in zip(resultado_liquefacao["dados_t"], resultado_liquefacao["dados_S"]):
                CurvaLiquefacao.objects.create(
                    processo_liquefacao=liquefacao,
                    tempo_h=tempo,
                    concentracao_amido=concentracao
                )

            # Gera novamente o gráfico com os dados recém-salvos
            curva_dados = CurvaLiquefacao.objects.filter(processo_liquefacao=liquefacao)
            tempos = [d.tempo_h for d in curva_dados]
            concentracoes = [d.concentracao_amido for d in curva_dados]

            fig = Figure(
                data=[Scatter(
                    x=tempos,
                    y=concentracoes,
                    mode='lines+markers',
                    name='Amido (g/L)',
                    line=dict(color='orange', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255,165,0,0.2)'
                )],
                layout=Layout(
                    title='Cinética da Liquefação Enzimática',
                    xaxis=dict(title='Tempo (h)'),
                    yaxis=dict(title='Concentração de Amido (g/L)'),
                    height=400
                )
            )

            grafico_liquefacao_json = json.dumps(fig, cls=PlotlyJSONEncoder)

            # Mensagem de sucesso para o usuário
            messages.success(request, f'{quantidade} kg de milho foram moídos e liquefeitos.')

            # Redireciona para a mesma página, mas passando o ID da nova simulação via GET
            return redirect(f"{request.path}?simulacao_id={form_instance.id}")
        
        else:
            print("🔴 Formulário de processo inválido")

    else:
        # Se não for POST, apenas inicializa o formulário vazio
        form = ProcessoMoagemForm()
    
    # Dados para enviar ao template HTML
    context = {
        'dados_moagem': dados_moagem,
        'dados_liquefacao': dados_liquefacao,
        'form': form,
        'grafico_liquefacao': grafico_liquefacao_json,
        'ultimas_simulacoes': ultimas_simulacoes,
        'simulacao_selecionada': simulacao_selecionada,
        'simulacoes_json': simulacoes_json,
    }

    # Renderiza a página
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
        
        