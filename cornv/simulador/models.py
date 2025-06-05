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
    

# ============================= MODELAGEM DE PROCESSOS =====================================================

class ProcessoMoagem(models.Model):
    quantidade_milho = models.FloatField(null=True)
    milho_moido = models.FloatField(null=True)
    energia_total = models.FloatField(null=True)
    data = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.quantidade_milho} kg - {self.milho_moido} moido - {self.data} - eficiencia: {self.eficiencia}"

class ProcessoLiquefacao(models.Model):
    processo = models.OneToOneField('ProcessoMoagem', on_delete=models.CASCADE, related_name='liquefacao')

    amido_convertido = models.FloatField(null=True, help_text="Amido convertido (kg)")
    conversao_amido = models.FloatField(null=True, help_text="Conversão do amido (%)")
    tempo_liquefacao = models.FloatField(null=True, help_text="Tempo de liquefação (h)")
    volume_reacao_L = models.FloatField(null=True, help_text="Volume da reação (L)")
    conc_amido_inicial = models.FloatField(null=True, help_text="Concentração inicial de amido (kg/L)")
    conc_amido_final = models.FloatField(null=True, help_text="Concentração final de amido (kg/L)")
    massa_oligossacarideos = models.FloatField(null=True, help_text="Oligossacarideos gerados (kg)")
    art_gerada = models.FloatField(null=True, help_text="Glicose fermentescível (ART) gerada (kg)")
    enzima_usada = models.FloatField(null=True, blank=True, help_text="Enzima utilizada ou necessária (g)")
    volume_total_L = models.FloatField(null=True, help_text="Volume total do processo (L)")
    volume_milho_L = models.FloatField(null=True, help_text="Volume estimado do milho puro (L)")
    volume_agua_adicionado_L = models.FloatField(null=True, help_text="Volume de água adicionado (L)")

    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.conversao_amido is not None:
            return f"Liq. de {self.processo.milho_moido} kg de milho moído - {self.conversao_amido:.1f}% convertido"
        return f"Liq. de {self.processo.milho_moido} kg de milho moído - conversão não calculada"

class CurvaLiquefacao(models.Model):
    processo_liquefacao = models.ForeignKey(ProcessoLiquefacao, on_delete=models.CASCADE, related_name='curva_dados')
    tempo_h = models.FloatField(help_text="Tempo (h)")
    concentracao_amido = models.FloatField(help_text="Concentração de amido (g/L)")
    produto_gerado = models.FloatField(null=True, blank=True)  # Novo campo
    art = models.FloatField(null=True, blank=True)
    oligos = models.FloatField(null=True, blank=True)


    class Meta:
        ordering = ['tempo_h']

    def __str__(self):
        return f"{self.tempo_h} h - {self.concentracao_amido:.2f} g/L"



class ProcessoSacarificacaoFermentacao(models.Model):
    processo_liquefacao = models.ForeignKey(
        'ProcessoLiquefacao',
        on_delete=models.CASCADE,
        related_name='sacarificacoes'
    )

    art_inicial = models.FloatField(help_text="Concentração inicial de ART (g/L) vindo da liquefação")
    oligossacarideos_inicial = models.FloatField(help_text="Concentração inicial de oligossacarídeos (g/L) vindo da liquefação")
    etanol_final = models.FloatField(help_text="Concentração final de etanol (g/L)")
    biomassa_final = models.FloatField(help_text="Concentração final de biomassa celular (g/L)")
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sacarificação/Fermentação em {self.data.date()} - Etanol: {self.etanol_final:.1f} g/L"


class CurvaSacFerm(models.Model):
    processo_sacferm = models.ForeignKey(
        ProcessoSacarificacaoFermentacao,
        on_delete=models.CASCADE,
        related_name='curva_dados'
    )
    
    conc_art = models.FloatField(null=True, help_text="Concentração de ART (g/L)")
    conc_oligos = models.FloatField(null=True, blank=True, help_text="Concentração de oligossacarídeos (g/L)")
    conc_etanol = models.FloatField(help_text="Concentração de etanol (g/L)")
    conc_biomassa = models.FloatField(help_text="Concentração de biomassa celular (g/L)")
    
    tempo_h = models.FloatField(help_text="Tempo (h)")


    def __str__(self):
        return f"{self.tempo}h: Etanol {self.etanol:.1f} g/L"



class CalculoART(models.Model):
    quantidade_milho = models.FloatField(null=True)
    quantidade_art = models.FloatField(null=True)
    volume_etanol = models.FloatField(null=True)
    proporcao_producao = models.FloatField(null=True)
    rendimento_percentual = models.FloatField(null=True)
    data = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.quantidade_milho} kg - {self.quantidade_art} ART - {self.data} - quantidade teorica de etanol produzida: {self.volume_etanol}"
    
    
class DadosFS(models.Model):
    milho_moido = models.FloatField(null=True)
    etanol_anidro_prod = models.FloatField(null=True)
    etanol_hidratado_prod = models.FloatField(null=True)
    ddg_produzido = models.FloatField(null=True)
    renda_etanol = models.FloatField(null=True)
    renda_ddg = models.FloatField(null=True)
    renda_energia = models.FloatField(null=True)
    data = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f'''milho: {self.milho_moido} (ton); etanol anidro: {self.etanol_anidro_prod} (m3); etanol hidratado {self.etanol_hidratado_prod};
                    DDG: {self.ddg_produzido} (ton); renda de etanol: {self.renda_etanol}; renda de ddg: {self.renda_ddg}; 
                    renda de energia: {self.renda_energia} - data: {self.data}
                '''