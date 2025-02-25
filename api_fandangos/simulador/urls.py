from django.urls import path
from . import views # o ponto significa "importar do diretório base do arquivo"

urlpatterns = [
        path('simulador/', views.index, name="simulador-index"),
]
