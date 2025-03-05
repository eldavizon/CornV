from django.urls import path
from .views import index, calcular_viabilidade # o ponto significa "importar do diretório base do arquivo"

urlpatterns = [
        path('simulador/', index, name="simulador-index"),
        path("simulador/calcular-viabilidade/", calcular_viabilidade, name="calcular_viabilidade"),

]

