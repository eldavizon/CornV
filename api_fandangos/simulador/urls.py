from django.urls import path
from .views import index, calcular_rendimento, obter_dados_historico # o ponto significa "importar do diretório base do arquivo"

urlpatterns = [
        path('', index, name="simulador-index"),
        path("calcular-rendimento/", calcular_rendimento, name="calcular-rendimento"),
        path('dados-historicos/', obter_dados_historico, name='obter_dados_historico'),

]

