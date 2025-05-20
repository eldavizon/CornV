from django import forms
from .models import CalculoART, ProcessoMoagem

class CalculoARTForm(forms.ModelForm):
    class Meta:
       
        model = CalculoART
        
        fields = ['quantidade_milho']
        

class ProcessoMoagemForm(forms.ModelForm):
    modo = forms.ChoiceField(
        choices=[
            ('tempo_por_enzima', 'Informar enzima (calcular tempo)'),
            ('enzima_por_tempo', 'Informar tempo (calcular enzima)')
        ],
        widget=forms.RadioSelect,
        label="Modo de simulação"
    )
    enzima_g = forms.FloatField(required=False, label="Quantidade de enzima (g)")
    tempo_h = forms.FloatField(required=False, label="Tempo de reação (h)")

    class Meta:
        model = ProcessoMoagem
        fields = ['quantidade_milho', 'modo', 'enzima_g', 'tempo_h']

        