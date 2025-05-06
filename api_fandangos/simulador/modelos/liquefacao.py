from scipy.integrate import solve_ivp
import numpy as np

Vmax = 300.0  # g/L/h
Km   = 100.0  # g/L
rend_amido = 0.62  # fração de amido no milho moído
densidade_reacao = 1.05  # kg/L - densidade do meio reação

def cinetica_liquefacao(t, S, Vmax, Km):
    """EDO para liquefação do amido."""
    dSdt = - (Vmax * S[0]) / (Km + S[0])
    return [dSdt]

def simular_liquefacao(massa_milho_moido_kg, tempo_reacao_h=2.0):
    """
    Simula a liquefação enzimática do milho moído com alfa-amilase.

    Parâmetros:
        massa_milho_moido_kg: float - massa de milho moído (kg)
        tempo_reacao_h: float - tempo de reação (h)

    Retorna:
        dict com resultados da simulação
    """
    massa_amido_g = massa_milho_moido_kg * 1000 * rend_amido
    volume_L = massa_milho_moido_kg * 3.0  # 3 L de água por kg
    S0 = massa_amido_g / volume_L

    t_span = (0, tempo_reacao_h)
    t_eval = np.linspace(0, tempo_reacao_h, 100)
    sol = solve_ivp(cinetica_liquefacao, t_span, [S0], args=(Vmax, Km), t_eval=t_eval)

    S_final = sol.y[0][-1]
    conversao = (S0 - S_final) / S0
    glicose_gerada_g = (S0 - S_final) * volume_L

    return {
        "tempo_h": tempo_reacao_h,
        "concentracao_amido_inicial": S0,
        "concentracao_amido_final": S_final,
        "conversao_percentual": conversao * 100,
        "massa_glicose_g": glicose_gerada_g,
        "dados_t": sol.t.tolist(),
        "dados_S": sol.y[0].tolist()
    }
