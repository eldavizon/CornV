from django import forms
from .models import CalculoART

class CalculoARTForm(forms.ModelForm):
    class Meta:
       
        model = CalculoART
        
        fields = ['quantidade_milho']