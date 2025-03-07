from django.db import models

# Create your models here.

class HistoricoPrecoEtanol(models.Model):
    data = models.DateField(unique=True, help_text="Data da cotação do etanol", null=False)
    preco_etanol = models.FloatField(help_text="Preço do etanol por litro (R$)", null=False)

    def __str__(self):
        return f"{self.data} - Etanol: R$ {self.preco_etanol}"

class HistoricoPrecoMilho(models.Model):
    data = models.DateField(unique=True, help_text="Data da cotação do milho", null=False)
    preco_milho = models.FloatField(help_text="Preço do milho por saca de 60kg (R$)", null=False)

    def __str__(self):
        return f"{self.data} - Milho: R$ {self.preco_milho}"


