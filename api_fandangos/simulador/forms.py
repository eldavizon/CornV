from django import forms
from .models import CalculoART, ProcessoMoagem

class CalculoARTForm(forms.ModelForm):
    class Meta:
       
        model = CalculoART
        
        fields = ['quantidade_milho']
        
class ProcessoMoagemForm(forms.ModelForm):
    class Meta:
       
        model = ProcessoMoagem
        
        fields = ['quantidade_milho']
        