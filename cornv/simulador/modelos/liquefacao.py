# Importações de bibliotecas
import numpy as np  # Apesar de importado, não está sendo utilizado no código atual
from typing import Literal, Optional

# Constantes do modelo industrial
Vmax_std = 10080.0     # Velocidade máxima da enzima (Liquozyme) em g/L/h
Km = 50.0              # Constante de Michaelis-Menten (afinidade substrato-enzima) em g/L
T_opt = 85             # Temperatura ótima de operação em °C
pH_opt = 6.0           # pH ótimo de operação

# Função para calcular o fator de correção da temperatura
def fator_temperatura(T):
    """Calcula o fator de redução da atividade enzimática devido ao desvio da temperatura ideal"""
    return max(0, 1 - 0.02 * abs(T - T_opt))  # Redução de 2% por °C de desvio

# Função para calcular o fator de correção do pH
def fator_pH(pH):
    """Calcula o fator de redução da atividade enzimática devido ao desvio do pH ideal"""
    # Mantém 100% de atividade entre 5.8 e 6.2
    return 1.0 if 5.8 <= pH <= 6.2 else max(0, 1 - 0.2 * abs(pH - pH_opt))  # Redução de 20% por unidade de pH fora da faixa

# Função para calcular a atividade enzimática ajustada
def atividade_aparente(Vmax, T, pH):
    """Calcula a velocidade máxima ajustada considerando temperatura e pH"""
    return Vmax * fator_temperatura(T) * fator_pH(pH)

# Função principal de simulação do processo de liquefação
def simular_liquefacao(
    massa_milho_kg: float,
    enzima_g: float,
    tempo_h: float,
    fator_amido_milho: float = 0.6,
    densidade_medio_L: float = 1.05,
    concentracao_desejada_g_L: Optional[float] = None,
    T_operacao: float = 85,
    pH_operacao: float = 6.0,
) -> dict:
    """Simula o processo de hidrólise enzimática do amido do milho com tempo fixo."""

    # Massa de amido
    massa_amido_kg = massa_milho_kg * fator_amido_milho
    massa_amido_g = massa_amido_kg * 1000

    # Volume do reator
    if concentracao_desejada_g_L:
        volume_L = massa_amido_g / concentracao_desejada_g_L
    else:
        volume_L = massa_milho_kg / densidade_medio_L

    volume_milho_L = massa_milho_kg / densidade_medio_L
    volume_agua_adicionado_L = max(volume_L - volume_milho_L, 0)

    conc_inicial_g_L = massa_amido_g / volume_L

    # Simulação numérica
    dt = 0.01
    t = 0
    S = conc_inicial_g_L
    lista_t = [t]
    lista_S = [S]
    lista_P = [0]  # Produto inicial

    epsilon = 1e-6
    Vmax_ajustado = atividade_aparente(Vmax_std * enzima_g, T_operacao, pH_operacao)

    while t < tempo_h:
        dSdt = - (Vmax_ajustado * S) / (Km + S)
        S += dSdt * dt
        S = max(S, 0)
        t += dt
        lista_t.append(t)
        lista_S.append(S)

        # Produto acumulado = diferença em relação à concentração inicial
        produto_g = (conc_inicial_g_L - S) * volume_L
        lista_P.append(produto_g)

        if S <= epsilon:
            S = 0
            break

    S_final = lista_S[-1]
    P_final = lista_P[-1]

    massa_glicose_g = P_final  # P_final já está em gramas
    conversao_percentual = (massa_glicose_g / massa_amido_g) * 100

    return {
        "dados_t": lista_t,
        "dados_S": lista_S,
        "dados_P": lista_P,
        "tempo_h": t,
        "massa_glicose_g": massa_glicose_g,
        "conversao_percentual": conversao_percentual,
        "enzima_g": enzima_g,
        "concentracao_amido_inicial": conc_inicial_g_L,
        "concentracao_amido_final": S_final,
        "concentracao_produto_final": P_final,
        "volume_total_L": volume_L,
        "volume_milho_L": volume_milho_L,
        "volume_agua_adicionado_L": volume_agua_adicionado_L,
    }
#fim