from django import forms
from .models import Produto, Retirada

class ProdutoForm(forms.ModelForm):
    class Meta:
       
        model = Produto
        
        fields = ['nome', 'classificacao', 'quantidade']
        
class RetiradaForm(forms.ModelForm):
    class Meta:
        
        model = Retirada
        
        fields = ['produto', 'quantidade_retirada']
        