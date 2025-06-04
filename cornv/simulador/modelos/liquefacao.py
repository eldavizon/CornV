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

def simular_liquefacao(
    massa_milho_kg: float,
    enzima_g: float,
    tempo_h: float,
    fator_amido_milho: float = 0.63,
    densidade_medio_L: float = 1.05,
    concentracao_desejada_g_L: Optional[float] = None,
    T_operacao: float = 85,
    pH_operacao: float = 6.0,
) -> dict:
    massa_amido_kg = massa_milho_kg * fator_amido_milho
    massa_amido_g = massa_amido_kg * 1000

    if concentracao_desejada_g_L:
        volume_L = massa_amido_g / concentracao_desejada_g_L
    else:
        volume_L = massa_milho_kg / densidade_medio_L

    volume_milho_L = massa_milho_kg / densidade_medio_L
    volume_agua_adicionado_L = max(volume_L - volume_milho_L, 0)

    conc_inicial_g_L = massa_amido_g / volume_L

    dt = 0.01
    t = 0
    S = conc_inicial_g_L

    lista_t = [t]
    lista_S = [S]
    lista_P = [0]  # Produto acumulado

    # Listas para massa de ART e oligossacarídeos
    lista_ART = [0]
    lista_oligos = [0]

    epsilon = 1e-6
    Vmax_ajustado = atividade_aparente(Vmax_std * enzima_g, T_operacao, pH_operacao)

    Ki = 50
    fator_estequiometrico_amido_para_ART = 1.11
    fracao_fermentescivel = 0.30

    while t < tempo_h:
        P = (conc_inicial_g_L - S)
        dSdt = - (Vmax_ajustado * S) / (Km + S + (S * P) / Ki)
        S += dSdt * dt
        S = max(S, 0)
        t += dt

        produto_g = (conc_inicial_g_L - S) * volume_L

        # Calcular massa ART e oligossacarídeos no instante t
        massa_art_g_t = produto_g * fracao_fermentescivel * fator_estequiometrico_amido_para_ART
        massa_oligo_g_t = produto_g * (1 - fracao_fermentescivel)

        # Armazenar nos arrays
        lista_t.append(t)
        lista_S.append(S)
        lista_P.append(produto_g)
        lista_ART.append(massa_art_g_t)
        lista_oligos.append(massa_oligo_g_t)

        if S <= epsilon:
            S = 0
            break

    S_final = lista_S[-1]
    P_final = lista_P[-1]
    massa_art_g = lista_ART[-1]
    massa_oligossacarideos_g = lista_oligos[-1]

    conversao_percentual = (P_final / massa_amido_g) * 100

    return {
        "dados_t": lista_t,
        "dados_S": lista_S,
        "dados_P": lista_P,
        "dados_ART": lista_ART,  # <- listas para gráficos
        "dados_oligos": lista_oligos,
        "tempo_h": t,
        "massa_art_g": massa_art_g,
        "massa_oligossacarideos_g": massa_oligossacarideos_g,
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