import datetime
import holidays
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from simulador.models import HistoricoPrecoEtanol
from utils.etanol_scrapper import coletar_cotacao_etanol
from django.conf import settings

# Inclui feriados nacionais e estaduais (SP)
feriados_br = holidays.Brazil(prov='SP', state='SP')

#feriados municipais de Piracicaba
feriados_piracicaba = [
    datetime.date(2025, 8, 1),   # Aniversário de Piracicaba
    # Adicione outros feriados municipais aqui
]

# Combina tudo em um único set de feriados
feriados_completos = feriados_br
for feriado in feriados_piracicaba:
    feriados_completos[feriado] = "Feriado municipal"

def obter_ultimo_dia_util(hoje):
    #Retorna o último dia útil antes de hoje, considerando sábados, domingos e feriados.
    dia_util = hoje
    while dia_util.weekday() >= 5 or dia_util in feriados_completos:
        dia_util -= datetime.timedelta(days=1)
    print(f"[DEBUG] Último dia útil determinado: {dia_util}")
    return dia_util

class AtualizaCotacaoEtanolMiddleware(MiddlewareMixin):
    def process_request(self, request):
   
        if not getattr(settings, "ATUALIZAR_COTACAO_ETANOL", True):
            print("[Middleware] Atualização de cotação de etanol desativada via settings.")
            return
        
        hoje = datetime.date.today()

        if cache.get("cotacao_etanol_atualizada"):
            print("[Middleware] Cotação de etanol já foi atualizada hoje (cache ativado).")
            return

        data_alvo = obter_ultimo_dia_util(hoje)

        if HistoricoPrecoEtanol.objects.filter(data=data_alvo).exists():
            print(f"[Middleware] Cotação de etanol para {data_alvo} já existe no banco.")
            cache.set("cotacao_etanol_atualizada", True, 60 * 60 * 24)
            return

        print(f"[Middleware] Cotação de etanol {data_alvo} não encontrada. Realizando scraping...")
        dados = coletar_cotacao_etanol()
        print(f"[Middleware] Dados retornados do scraping: {dados}")

        if dados and dados.get("data") == data_alvo:
            HistoricoPrecoEtanol.objects.create(
                data=dados["data"],
                preco_etanol=dados["valor"]
            )
            print(f"[Middleware] Cotação de etanol inserida no banco: {dados}")
            cache.set("cotacao_etanol_atualizada", True, 60 * 60 * 24)
        else:
            print(f"[Middleware] Dados inválidos ou não correspondem a {data_alvo} para etanol. Nenhuma inserção realizada.")
