import numpy as np
from scipy.integrate import solve_ivp

# Parâmetros globais
Vmax_std = 300.0        # Vmax padrão da alfa-amilase (g/L/h)
Km = 100.0              # Constante de Michaelis-Menten (g/L)
rend_amido = 0.62       # Fração de amido no milho moído
densidade_reacao = 1.05 # kg/L
T_operacao = 85         # Temperatura de operação da liquefação (°C)
pH_operacao = 6.0       # pH ideal para alfa-amilase

# Função que calcula o fator de temperatura baseado na temperatura da operação
def fator_temperatura(T):
    T_opt = 85  # Temperatura ótima da enzima
    if T > T_opt:
        # Se a temperatura for maior que a ótima, a atividade da enzima diminui
        return max(0, 1 - 0.02 * (T - T_opt))
    else:
        # Se a temperatura for menor que a ótima, a atividade também diminui, mas de forma mais suave
        return max(0, 1 - 0.01 * (T_opt - T))

# Função que calcula o fator de pH baseado no pH da operação
def fator_pH(pH):
    if 5.8 <= pH <= 6.2:
        # Se o pH estiver entre 5.8 e 6.2, a enzima está em condições ideais
        return 1.0
    else:
        # Se o pH estiver fora da faixa ideal, a atividade diminui
        return max(0, 1 - 0.2 * abs(pH - 6.0))

# Função que calcula a atividade aparente da enzima considerando temperatura e pH
def atividade_aparente(Vmax, T, pH):
    return Vmax * fator_temperatura(T) * fator_pH(pH)

# Função que descreve a cinética de liquefação do amido baseado na equação de Michaelis-Menten
def cinetica_liquefacao(t, S, Vmax_ajustado, Km):
    # Calcula a taxa de variação da concentração de amido (S) com o tempo (t)
    dSdt = - (Vmax_ajustado * S[0]) / (Km + S[0])
    return [dSdt]

# Função principal que simula o processo de liquefação do amido
def simular_liquefacao(massa_milho_moido_kg, tempo_reacao_h=2.0, T=T_operacao, pH=pH_operacao):
    try:
        # Valida a entrada para garantir que a massa de milho moído seja positiva
        if massa_milho_moido_kg <= 0:
            raise ValueError("A massa de milho moído deve ser positiva.")

        # Calcula a massa de amido no milho moído (em gramas)
        massa_amido_g = massa_milho_moido_kg * 1000 * rend_amido
        # Calcula o volume total de milho moído no reator (em litros)
        volume_L = massa_milho_moido_kg * 3.0
        # Concentração inicial de amido no reator (g/L)
        S0 = massa_amido_g / volume_L

        # Ajusta o Vmax da enzima com base na temperatura e pH
        Vmax_ajustado = atividade_aparente(Vmax_std, T, pH)

        # Define o intervalo de tempo para a simulação
        t_span = (0, tempo_reacao_h)
        # Gera os pontos de avaliação ao longo do tempo
        t_eval = np.linspace(0, tempo_reacao_h, 100)
        # Resolve a equação diferencial usando o método de Runge-Kutta
        sol = solve_ivp(cinetica_liquefacao, t_span, [S0], args=(Vmax_ajustado, Km), t_eval=t_eval)

        # Concentração final de amido após o tempo de reação
        S_final = sol.y[0][-1]
        # Calcula a conversão do amido para glicose (percentual)
        conversao = (S0 - S_final) / S0
        # Calcula a quantidade de glicose gerada (em gramas)
        glicose_gerada_g = (S0 - S_final) * volume_L

        # Retorna os resultados da simulação
        return {
            "tempo_h": tempo_reacao_h,
            "concentracao_amido_inicial": round(S0, 4),
            "concentracao_amido_final": round(S_final, 4),
            "conversao_percentual": round(conversao * 100, 2),
            "massa_glicose_g": round(glicose_gerada_g, 2),
            "dados_t": sol.t.tolist(),
            "dados_S": sol.y[0].tolist()
        }

    except Exception as e:
        # Caso ocorra algum erro durante a simulação, captura a exceção e retorna os dados de erro
        print(f"Erro na simulação da liquefação: {e}")
        return {
            "tempo_h": 0,
            "concentracao_amido_inicial": 0,
            "concentracao_amido_final": 0,
            "conversao_percentual": 0,
            "massa_glicose_g": 0,
            "dados_t": [],
            "dados_S": [],
            "erro": str(e)
        }
