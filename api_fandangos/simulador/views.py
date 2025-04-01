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
            volume_etanol = float(data.get("volumeEtanol", 0) or 0)
            custo_producao = float(data.get("custoProducao", 0) or 0)
            massa_MP = float(data.get("massaMP", 0) or 0)
            eficiencia = float(data.get("eficiencia", 1) or 1)  # Evita divisão por zero


            print(f'''data: {data}\n materia prima: {materia_prima} ;volume etanol: {volume_etanol} \n 
                  custo: {custo_producao} massa: {massa_MP} e eficiencia: {eficiencia}
                  
                  ''')

            if custo_producao <= 0 or volume_etanol <= 0:
                return JsonResponse({"error": "Custo de produção e volume de etanol devem ser maiores que zero."}, status=400)


            viabilidade = ((massa_MP * 0.63 * eficiencia) / (custo_producao * volume_etanol))*100

            return JsonResponse({
                "materiaPrima": materia_prima,
                "viabilidade": round(viabilidade, 2)
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método não permitido"}, status=405)


def obter_dados_historico(request):
    try:
        # Obter os dados históricos de etanol e milho ordenados por data
        historico_etanol = HistoricoPrecoEtanol.objects.order_by("data")
        historico_milho = HistoricoPrecoMilho.objects.order_by("data")

        # Preparar os dados para os gráficos
        datas_etanol = [registro.data.strftime("%Y-%m-%d") for registro in historico_etanol]
        precos_etanol = [float(registro.preco_etanol) for registro in historico_etanol]

        datas_milho = [registro.data.strftime("%Y-%m-%d") for registro in historico_milho]
        precos_milho = [float(registro.preco_milho) for registro in historico_milho]

        context = {
            "datas_etanol_json": json.dumps(datas_etanol),
            "precos_etanol_json": json.dumps(precos_etanol),
            "datas_milho_json": json.dumps(datas_milho),
            "precos_milho_json": json.dumps(precos_milho)
        }
        
        return render(request, "simulador/serie_historica.html", context)

    except Exception as e:
        return render(request, "simulador/serie_historica.html", {
            "error": f"Erro ao obter dados: {str(e)}"
        })
    
    
    