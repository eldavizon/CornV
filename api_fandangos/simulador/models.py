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

class CalculoART(models.Model):
    quantidade_milho = models.FloatField(null=True)
    quantidade_art = models.FloatField(null=True)
    volume_etanol = models.FloatField(null=True)
    data = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.quantidade_milho} kg - {self.quantidade_art} ART - {self.data} - quantidade teorica de etanol produzida: {self.volume_etanol}"