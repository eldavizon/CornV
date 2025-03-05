from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json



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