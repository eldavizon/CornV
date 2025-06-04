from django import forms
from .models import CalculoART, ProcessoMoagem

class CalculoARTForm(forms.ModelForm):
    class Meta:
       
        model = CalculoART
        
        fields = ['quantidade_milho']
        

class ProcessoMoagemForm(forms.ModelForm):

    enzima_g = forms.FloatField(required=True, label="Quantidade de enzima (g)")

    class Meta:
        model = ProcessoMoagem
        fields = ['quantidade_milho', 'enzima_g']

        