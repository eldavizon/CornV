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
    enzima_g: Optional[float] = None,
    tempo_h: Optional[float] = None,
    modo: Literal["tempo_por_enzima", "enzima_por_tempo"] = "tempo_por_enzima",
    fator_amido_milho: float = 0.6,          # Fração de amido no milho (60%)
    densidade_medio_L: float = 1.05,          # Densidade média da mistura (kg/L)
    concentracao_desejada_g_L: Optional[float] = None,  # Concentração alvo de amido
    T_operacao: float = 85,                   # Temperatura real de operação
    pH_operacao: float = 6.0,                 # pH real de operação
) -> dict:
    """Simula o processo de hidrólise enzimática do amido do milho"""
    
    # Validação de entradas conforme modo selecionado
    if modo == "tempo_por_enzima" and enzima_g is None:
        return {"erro": "Informe a quantidade de enzima."}
    if modo == "enzima_por_tempo" and tempo_h is None:
        return {"erro": "Informe o tempo de reação."}

    # Cálculo da massa de amido presente no milho
    massa_amido_kg = massa_milho_kg * fator_amido_milho
    massa_amido_g = massa_amido_kg * 1000  # Conversão para gramas

    # Cálculo do volume total do reator
    if concentracao_desejada_g_L:
        volume_L = massa_amido_g / concentracao_desejada_g_L  # Volume para atingir concentração desejada
    else:
        volume_L = massa_milho_kg / densidade_medio_L  # Volume baseado apenas na massa de milho

    # Cálculo de volumes adicionais
    volume_milho_L = massa_milho_kg / densidade_medio_L
    volume_agua_adicionado_L = max(volume_L - volume_milho_L, 0)  # Água necessária para ajuste

    # Concentração inicial de substrato (amido)
    conc_inicial_g_L = massa_amido_g / volume_L

    # Parâmetros para simulação numérica
    dt = 0.01  # Passo temporal (0.01 h = 36 segundos)
    S = conc_inicial_g_L  # Concentração inicial de substrato
    t = 0  # Tempo inicial
    tempo_max = tempo_h if modo == "enzima_por_tempo" else 8  # Tempo máximo de simulação (8h padrão)

    # Listas para armazenar resultados
    lista_t = [t]
    lista_S = [S]

    epsilon = 1e-6  # Valor mínimo considerado para concentração

    # Modo 1: Encontrar quantidade de enzima necessária para um tempo específico
    if modo == "enzima_por_tempo":
        enzima_g = 0.1  # Começa com 0.1g e incrementa
        encontrado = False
        
        # Loop para encontrar a dose mínima de enzima que atinge 90% de conversão
        while enzima_g <= 100:
            Vmax_ajustado = atividade_aparente(Vmax_std * enzima_g, T_operacao, pH_operacao)
            
            # Simulação temporária para testar conversão
            S_temp = conc_inicial_g_L
            t_temp = 0
            while t_temp < tempo_h:
                # Modelo de Michaelis-Menten (equação diferencial)
                dSdt = - (Vmax_ajustado * S_temp) / (Km + S_temp)
                S_temp += dSdt * dt  # Método de Euler explícito
                S_temp = max(S_temp, 0)
                t_temp += dt
                if S_temp <= epsilon:
                    S_temp = 0
                    break
            
            # Verifica se atingiu pelo menos 90% de conversão
            conversao = (conc_inicial_g_L - S_temp) / conc_inicial_g_L
            if conversao >= 0.9:
                encontrado = True
                break
            enzima_g += 0.1  # Incrementa dose de enzima

        # Trata casos onde não foi encontrada solução
        if not encontrado:
            enzima_g = None
        else:
            # Refaz a simulação com a enzima encontrada para armazenar os dados
            S = conc_inicial_g_L
            t = 0
            lista_t = [t]
            lista_S = [S]
            while t < tempo_h:
                dSdt = - (Vmax_ajustado * S) / (Km + S)
                S += dSdt * dt
                S = max(S, 0)
                t += dt
                lista_t.append(t)
                lista_S.append(S)
                if S <= epsilon:
                    S = 0
                    break

    # Modo 2: Simular processo com dose fixa de enzima até tempo máximo
    elif modo == "tempo_por_enzima":
        Vmax_ajustado = atividade_aparente(Vmax_std * enzima_g, T_operacao, pH_operacao)
        while t < tempo_max:
            dSdt = - (Vmax_ajustado * S) / (Km + S)
            S += dSdt * dt
            S = max(S, 0)
            t += dt
            lista_t.append(t)
            lista_S.append(S)
            if S <= epsilon:
                S = 0
                break

    # Cálculos finais de resultados
    S_final = lista_S[-1]
    massa_glicose_g = (conc_inicial_g_L - S_final) * volume_L  # Massa produzida
    conversao_percentual = (massa_glicose_g / massa_amido_g) * 100  # % de conversão

    # Retorna dicionário com todos os resultados
    return {
        "dados_t": lista_t,  # Lista de tempos simulados
        "dados_S": lista_S,  # Lista de concentrações de substrato
        "tempo_h": t,       # Tempo total de simulação
        "massa_glicose_g": massa_glicose_g,
        "conversao_percentual": conversao_percentual,
        "enzima_g": enzima_g,  # Quantidade de enzima usada/encontrada
        "concentracao_amido_inicial": conc_inicial_g_L,
        "concentracao_amido_final": S_final,
        "volume_total_L": volume_L,
        "volume_milho_L": volume_milho_L,
        "volume_agua_adicionado_L": volume_agua_adicionado_L,
    }