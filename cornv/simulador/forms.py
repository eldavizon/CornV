from django import forms
from .models import CalculoART, ProcessoMoagem

class CalculoARTForm(forms.ModelForm):
    class Meta:
       
        model = CalculoART
        
        fields = ['quantidade_milho']
        

class ProcessoMoagemForm(forms.ModelForm):

    enzima_g = forms.FloatField(required=True, label="Quantidade de enzima (g)")
    concentracao_desejada_g_L = forms.FloatField(required=False, label="Concentração desejada (g/L)")


    class Meta:
        model = ProcessoMoagem
        fields = ['quantidade_milho', 'enzima_g', 'concentracao_desejada_g_L']

        