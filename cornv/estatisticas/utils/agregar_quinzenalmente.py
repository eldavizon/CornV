from datetime import date, timedelta
import holidays
from collections import defaultdict
import calendar


# Importar feriados do estado de São Paulo
feriados = holidays.Brazil(prov="SP")

def proximo_dia_util(d):
    while d.weekday() >= 5 or d in feriados:  # 5 = sábado, 6 = domingo
        d += timedelta(days=1)
    return d

def gerar_intervalos_quinzenais(inicio, fim):
    data_atual = inicio
    intervalos = []
    
    while data_atual <= fim:
        inicio_periodo = proximo_dia_util(data_atual)

        if data_atual.day < 16:
            fim_periodo = date(data_atual.year, data_atual.month, 15)
        else:
            ultimo_dia = calendar.monthrange(data_atual.year, data_atual.month)[1]
            fim_periodo = date(data_atual.year, data_atual.month, ultimo_dia)

        fim_periodo = proximo_dia_util(fim_periodo)

        if inicio_periodo > fim:
            break

        intervalos.append((inicio_periodo, fim_periodo))

        # Avança para próxima quinzena
        if data_atual.day < 16:
            data_atual = date(data_atual.year, data_atual.month, 16)
        else:
            if data_atual.month == 12:
                data_atual = date(data_atual.year + 1, 1, 1)
            else:
                data_atual = date(data_atual.year, data_atual.month + 1, 1)

    return intervalos

# Função para agrupar por intervalo
def agrupar_por_intervalo(dados, campo_preco):
    
    grupos = defaultdict(list)
    
    # Datas de início e fim calculadas para 2 anos atrás.
    data_fim = date.today()
    data_inicio = date(data_fim.year - 2, data_fim.month, data_fim.day)

    # Gera os intervalos quinzenais com dias úteis
    intervalos = gerar_intervalos_quinzenais(data_inicio, data_fim)
    
    for registro in dados:
        for inicio, fim in intervalos:
            if inicio <= registro.data <= fim:
                grupos[inicio].append(getattr(registro, campo_preco))
                break
    return [
        {"quinzena": inicio, "preco_medio": sum(valores) / len(valores)}
        for inicio, valores in grupos.items() if valores
    ]