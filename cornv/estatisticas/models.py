from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# Uso do loop for para não ter que escrever toda a repetição. O parametro "choices" aceita as tuplas de tuplas.
CLASSIFICACAO = [(item, item) for item in[
    "Ácidos minerais oxidantes",
    "Bases cáusticas",
    "Hidrocarbonetos aromáticos",
    "Orgânicos Halogenados",
    "Metais",
    "Metais tóxicos",
    "Hidrocarbonetos alifáticos saturados",
    "Fenóis e cresóis",
    "Agentes oxidantes fortes",
    "Agentes redutores fortes",
    "Água e soluções aquosas",
    "Substâncias que reagem com água",
    "Químicos tóxicos",
    "Inflamáveis",
    "Outros",
    "Não perigoso",
]
]


class Produto(models.Model):
    nome = models.CharField(max_length=200, null=True)
    classificacao = models.CharField(max_length=200, choices=CLASSIFICACAO , null=True)
    quantidade = models.DecimalField(max_digits=19, decimal_places=4, null=True)
    
    def __str__(self):
        return f'{self.nome}'
    
class Retirada(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=True)
    
    staff = models.ForeignKey(User, models.CASCADE, null=True)
    
    quantidade_retirada = models.DecimalField(max_digits=19, decimal_places=4, null=True)
    
    data = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.produto} retirado por {self.staff.username}'
    
    
