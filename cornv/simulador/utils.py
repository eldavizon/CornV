# serializar simulacoes
from django.core.serializers.json import DjangoJSONEncoder
import json

# gerar graficos
from plotly.graph_objs import Figure, Scatter, Layout
import json
from plotly.utils import PlotlyJSONEncoder

#processar modelagem
from django.contrib import messages
from .models import ProcessoLiquefacao, CurvaLiquefacao
from .modelos.moagem import calcular_moagem
from .modelos.liquefacao import simular_liquefacao


def serializar_simulacoes(ultimas_simulacoes):
    return json.dumps([
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
                "oligossacarideos": p.liquefacao.massa_oligossacarideos,
                "percentual": p.liquefacao.conversao_amido,
                "enzima": p.liquefacao.enzima_usada,
                "volume_total_L": p.liquefacao.volume_total_L,
                "volume_milho_L": p.liquefacao.volume_milho_L,
                "volume_agua_adicionado_L": p.liquefacao.volume_agua_adicionado_L,
                "grafico": [
                    {
                        "tempo": d.tempo_h,
                        "conc": d.concentracao_amido,
                        "art": d.art,
                        "oligos": d.oligos
                    } for d in p.liquefacao.curva_dados.all()
                ]
            } if hasattr(p, 'liquefacao') else None
        }
        for p in ultimas_simulacoes
    ], cls=DjangoJSONEncoder)



def gerar_grafico_curva(curva_dados, incluir_art=False):
    tempos = [d.tempo_h for d in curva_dados]
    concentracoes = [d.concentracao_amido for d in curva_dados]

    data = [Scatter(
        x=tempos,
        y=concentracoes,
        mode='lines+markers',
        name='Amido (g/L)',
        line=dict(color='orange', width=2),
        fill='tozeroy',
        fillcolor='rgba(255,165,0,0.2)'
    )]

    layout = Layout(
        title='Cinética da Liquefação Enzimática',
        xaxis=dict(title='Tempo (h)'),
        yaxis=dict(title='Concentração de Amido (g/L)'),
        height=450
    )

    if incluir_art:
        arts = [d.art for d in curva_dados]
        oligos = [d.oligos for d in curva_dados]

        data += [
            Scatter(
                x=tempos,
                y=arts,
                mode='lines+markers',
                name='ART (g)',
                line=dict(color='green', width=2),
                yaxis='y2'
            ),
            Scatter(
                x=tempos,
                y=oligos,
                mode='lines+markers',
                name='Oligossacarídeos (g)',
                line=dict(color='blue', width=2, dash='dash'),
                yaxis='y2'
            )
        ]

        layout.yaxis2 = dict(
            title='Produto acumulado (g)',
            overlaying='y',
            side='right'
        )

    fig = Figure(data=data, layout=layout)
    return json.dumps(fig, cls=PlotlyJSONEncoder)



def processar_formulario_processo(request, form):
    if not form.is_valid():
        return None, None, "Formulário inválido."

    instance = form.save(commit=False)
    quantidade = float(form.cleaned_data["quantidade_milho"])

    
    
    resultado = calcular_moagem(quantidade)
    instance.milho_moido = resultado["massa_moida"]
    instance.energia_total = resultado["energia_total_kWh"]
    instance.save()

    enzima_g = form.cleaned_data.get("enzima_g")
    tempo_h = 50
    concentracao_desejada = 200

    resultado_liquefacao = simular_liquefacao(
        massa_milho_kg=instance.milho_moido,
        enzima_g=enzima_g,
        tempo_h=tempo_h,
        concentracao_desejada_g_L=concentracao_desejada
    )

    if resultado_liquefacao.get("erro"):
        return None, None, resultado_liquefacao["erro"]

    liquefacao = ProcessoLiquefacao.objects.create(
        processo=instance,
        amido_convertido=resultado_liquefacao["massa_art_g"] / 1000,
        conversao_amido=resultado_liquefacao["conversao_percentual"],
        tempo_liquefacao=resultado_liquefacao["tempo_h"],
        volume_reacao_L=instance.milho_moido / 1.05,
        conc_amido_inicial=resultado_liquefacao["concentracao_amido_inicial"] / 1000,
        conc_amido_final=resultado_liquefacao["concentracao_amido_final"] / 1000,
        massa_oligossacarideos=resultado_liquefacao["massa_oligossacarideos_g"] / 1000,
        art_gerada=resultado_liquefacao["massa_art_g"] / 1000,
        enzima_usada=enzima_g if enzima_g else resultado_liquefacao["enzima_g"],
        volume_total_L=resultado_liquefacao["volume_total_L"],
        volume_milho_L=resultado_liquefacao["volume_milho_L"],
        volume_agua_adicionado_L=resultado_liquefacao["volume_agua_adicionado_L"],
    )

    for t, s, a, o in zip(resultado_liquefacao["dados_t"],
                          resultado_liquefacao["dados_S"],
                          resultado_liquefacao["dados_ART"],
                          resultado_liquefacao["dados_oligos"]):
        CurvaLiquefacao.objects.create(
            processo_liquefacao=liquefacao,
            tempo_h=t,
            concentracao_amido=s,
            art=a,
            oligos=o,
            produto_gerado=a + o
        )

    return instance, liquefacao, None
