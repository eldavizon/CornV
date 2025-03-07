from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import HistoricoPrecoEtanol, HistoricoPrecoMilho




# Create your views here.

@login_required(login_url='user-login', ) # está configurado nas settings > login_url.
def index(request):
    return render(request, 'simulador/index.html')

@csrf_exempt
def calcular_viabilidade(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            materia_prima = data.get("materiaPrima", "Desconhecida")
            preco_etanol = float(data.get("precoEtanol", 0))
            custo_producao = float(data.get("custoProducao", 0))
            eficiencia = float(data.get("eficiencia", 1))  # Evita divisão por zero

            if eficiencia <= 0:
                return JsonResponse({"error": "Eficiência deve ser maior que zero."}, status=400)

            viabilidade = (preco_etanol * custo_producao) / eficiencia

            return JsonResponse({
                "materiaPrima": materia_prima,
                "viabilidade": round(viabilidade, 2)
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método não permitido"}, status=405)


def obter_dados_historico(request):
    try:
        # Obter os dados históricos de etanol e milho
        historico_etanol = HistoricoPrecoEtanol.objects.order_by("data")
        historico_milho = HistoricoPrecoMilho.objects.order_by("data")

        # Preparar os dados para os gráficos
        datas_etanol = [registro.data.strftime("%Y-%m-%d") for registro in historico_etanol]
        precos_etanol = [float(registro.preco_etanol) for registro in historico_etanol]

        datas_milho = [registro.data.strftime("%Y-%m-%d") for registro in historico_milho]
        precos_milho = [float(registro.preco_milho) for registro in historico_milho]

        context = {
            "datas_etanol": datas_etanol,
            "precos_etanol": precos_etanol,
            "datas_milho": datas_milho,
            "precos_milho": precos_milho
        }
        
        # Renderiza a página com os dados no contexto para os gráficos
        return render(request, "simulador/serie_historica.html", context)

    except Exception as e:
        return render(request, "simulador/serie_historica.html", {
            "error": f"Erro ao obter dados: {str(e)}"
        })
    
    
    