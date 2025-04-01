from django.urls import path
from .views import index, calcular_viabilidade, obter_dados_historico # o ponto significa "importar do diretório base do arquivo"

urlpatterns = [
        path('', index, name="simulador-index"),
        path("calcular-viabilidade/", calcular_viabilidade, name="calcular_viabilidade"),
        path('dados-historicos/', obter_dados_historico, name='obter_dados_historico'),

]

