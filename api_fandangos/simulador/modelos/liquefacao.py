import numpy as np
from scipy.integrate import solve_ivp, odeint
from scipy.optimize import minimize_scalar
from typing import Literal, Optional

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
def simular_liquefacao(
    massa_milho_kg: float,
    enzima_g: Optional[float] = None,
    tempo_h: Optional[float] = None,
    modo: Literal["tempo_por_enzima", "enzima_por_tempo"] = "tempo_por_enzima",
    k_base: float = 0.2,  # constante de taxa base (h⁻¹.g⁻¹)
    fator_amido_milho: float = 0.6,  # fração de amido no milho
    densidade_medio_L: float = 1.05,  # densidade aproximada da mistura (kg/L)
) -> dict:
    """
    Simula a liquefação enzimática, resolvendo uma EDO simples de 1ª ordem.

    Parâmetros:
    - massa_milho_kg: quantidade de milho moído (kg)
    - enzima_g: quantidade de enzima (g)
    - tempo_h: tempo da reação (h)
    - modo: 'tempo_por_enzima' ou 'enzima_por_tempo'
    - k_base: constante de reação por grama de enzima
    - fator_amido_milho: fração do milho que é amido
    - densidade_medio_L: densidade da mistura (kg/L)

    Retorno:
    - dicionário com curva de tempo, concentração e métricas da conversão
    """

    if modo == "tempo_por_enzima" and enzima_g is None:
        return {"erro": "Informe a quantidade de enzima."}
    if modo == "enzima_por_tempo" and tempo_h is None:
        return {"erro": "Informe o tempo de reação."}

    # Cálculo da massa de amido presente
    massa_amido_kg = massa_milho_kg * fator_amido_milho
    massa_amido_g = massa_amido_kg * 1000
    volume_L = massa_milho_kg / densidade_medio_L
    conc_inicial_g_L = massa_amido_g / volume_L

    def modelo(S, t, k):
        return -k * S

    if modo == "tempo_por_enzima":
        k = k_base * enzima_g
        t = np.linspace(0, 8, 1000)  # até 8h
        S = odeint(modelo, conc_inicial_g_L, t, args=(k,)).flatten()
        S_final = S[-1]
        massa_glicose_g = (conc_inicial_g_L - S_final) * volume_L
        tempo_atingido = t[-1]
    elif modo == "enzima_por_tempo":
        def erro_enxima(enzima_teste):
            if enzima_teste <= 0:
                return np.inf
            k = k_base * enzima_teste
            S = odeint(modelo, conc_inicial_g_L, [0, tempo_h], args=(k,)).flatten()
            S_final = S[-1]
            massa_glicose = (conc_inicial_g_L - S_final) * volume_L
            return -massa_glicose  # queremos maximizar glicose → minimizar -glicose

        opt = minimize_scalar(erro_enxima, bounds=(0.1, 100), method='bounded')
        enzima_g = opt.x
        k = k_base * enzima_g
        t = np.linspace(0, tempo_h, 1000)
        S = odeint(modelo, conc_inicial_g_L, t, args=(k,)).flatten()
        S_final = S[-1]
        massa_glicose_g = (conc_inicial_g_L - S_final) * volume_L
        tempo_atingido = tempo_h

    conversao_percentual = (massa_glicose_g / massa_amido_g) * 100

    return {
        "dados_t": list(t),
        "dados_S": list(S),
        "tempo_h": tempo_atingido,
        "massa_glicose_g": massa_glicose_g,
        "conversao_percentual": conversao_percentual,
        "enzima_g": enzima_g,
        "concentracao_amido_inicial": conc_inicial_g_L,
        "concentracao_amido_final": S_final,
    }
