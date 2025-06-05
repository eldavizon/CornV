def simular_etanol(
    concentracao_oligossacarideos_inicial: float = 120.0,
    concentracao_glicose_inicial: float = 0.0,
    concentracao_biomassa_inicial: float = 0.1,
    tempo_simulacao_h: float = 72,
    passo_temporal_h: float = 0.1,
    Vmax_sacarificacao: float = 2.5,
    Km_sacarificacao: float = 50.0,
    Ki_etanol_sacarificacao: float = 80.0,
    mu_max_fermentacao: float = 0.4,
    Ks_fermentacao: float = 0.5,
    Yxs_fermentacao: float = 0.05,
    Yps_fermentacao: float = 0.45,
    Kp_etanol_fermentacao: float = 95.0
) -> dict:
    """
    Simula o processo combinado de sacarificação e fermentação para produção de etanol,
    agora permitindo uma concentração inicial de glicose (G) para crescimento inicial das leveduras,
    e considerando que os oligossacarídeos (O) são hidrolisados em glicose e imediatamente consumidos.

    Args:
        concentracao_oligossacarideos_inicial: Concentração inicial de oligossacarídeos (g/L).
        concentracao_glicose_inicial: Concentração inicial de glicose já disponível (g/L).
        concentracao_biomassa_inicial: Concentração inicial de biomassa (g/L).
        tempo_simulacao_h: Tempo total de simulação (horas).
        passo_temporal_h: Passo de tempo para integração (horas).
        Vmax_sacarificacao: Vmax da enzima na sacarificação (g/L·h).
        Km_sacarificacao: Km da enzima na sacarificação (g/L).
        Ki_etanol_sacarificacao: Ki de etanol inibindo a sacarificação (g/L).
        mu_max_fermentacao: μ_max da fermentação (1/h).
        Ks_fermentacao: Ks da fermentação (g/L).
        Yxs_fermentacao: rendimento de biomassa por glicose consumida (g_X / g_G).
        Yps_fermentacao: rendimento de etanol por glicose consumida (g_P / g_S).
        Kp_etanol_fermentacao: Kp de etanol inibindo a fermentação (g/L).

    Returns:
        dicionário com resultados:
        {
            "tempo_h": [...],
            "oligossacarideos_g_L": [...],
            "glicose_g_L": [...],
            "biomassa_g_L": [...],
            "etanol_g_L": [...],
            "concentracao_etanol_final": float,
            "conversao_oligossacarideos_percentual": float,
            "conversao_glicose_percentual": float,
            "concentracao_oligossacarideos_inicial": float,
            "concentracao_glicose_inicial": float,
            "concentracao_oligossacarideos_final": float,
            "concentracao_glicose_final": float,
            "concentracao_biomassa_final": float,
            "tempo_simulacao_h": float,
            "parametros_sacarificacao": {...},
            "parametros_fermentacao": {...}
        }
    """
    # 1) Parâmetros agrupados
    params_sacarificacao = {
        'Vmax': Vmax_sacarificacao,
        'Km': Km_sacarificacao,
        'Ki_etanol': Ki_etanol_sacarificacao
    }
    params_fermentacao = {
        'mu_max': mu_max_fermentacao,
        'Ks': Ks_fermentacao,
        'Yxs': Yxs_fermentacao,
        'Yps': Yps_fermentacao,
        'Kp_etanol': Kp_etanol_fermentacao
    }

    # 2) Funções auxiliares (mesma lógica)
    def calcular_sacarificacao(O, E, params):
        Vmax = params['Vmax']
        Km = params['Km']
        Ki_etanol = params['Ki_etanol']
        # Michaelis-Menten com inibição por produto (etanol)
        v_sac = (Vmax * O) / (Km + O) * (1 / (1 + E / Ki_etanol))
        return v_sac

    def calcular_fermentacao(G, X, E, params):
        mu_max = params['mu_max']
        Ks = params['Ks']
        Yxs = params['Yxs']
        Yps = params['Yps']
        Kp_etanol = params['Kp_etanol']
        # Taxa específica de crescimento (Monod + inibição por etanol)
        mu = mu_max * (G / (Ks + G)) * max(0.0, (1.0 - E / Kp_etanol))
        # Consumo de glicose pela levedura (g_G/h·L)
        dG_cons = (mu / Yxs) * X
        # Produção de etanol (g_E/h·L)
        dE_prod = Yps * dG_cons
        return mu, dG_cons, dE_prod

    # 3) Estado inicial
    estado = {
        'O': concentracao_oligossacarideos_inicial,  # oligossacarídeos (g/L)
        'G': concentracao_glicose_inicial,           # glicose inicial (g/L)
        'X': concentracao_biomassa_inicial,          # biomassa (g/L)
        'E': 0.0                                     # etanol (g/L), começa em zero
    }

    # 4) Listas de resultados
    lista_tempo = [0.0]
    lista_oligossacarideos = [estado['O']]
    lista_glicose = [estado['G']]
    lista_biomassa = [estado['X']]
    lista_etanol = [estado['E']]

    # 5) Loop de integração (Euler explícito)
    t = 0.0
    while t < tempo_simulacao_h:
        # 5.1) calcular velocidades no instante t
        v_sac = calcular_sacarificacao(estado['O'], estado['E'], params_sacarificacao)
        mu, dG_cons, dE_prod = calcular_fermentacao(estado['G'], estado['X'], estado['E'], params_fermentacao)

        # 5.2) equações diferenciais
        dO_dt = -v_sac
        dG_dt = v_sac - dG_cons
        dX_dt = mu * estado['X']
        dE_dt = dE_prod

        # 5.3) passo de tempo
        estado['O'] = max(estado['O'] + dO_dt * passo_temporal_h, 0.0)
        estado['G'] = max(estado['G'] + dG_dt * passo_temporal_h, 0.0)
        estado['X'] = max(estado['X'] + dX_dt * passo_temporal_h, 0.0)
        estado['E'] = estado['E'] + dE_dt * passo_temporal_h

        # 5.4) avançar t e armazenar
        t += passo_temporal_h
        lista_tempo.append(t)
        lista_oligossacarideos.append(estado['O'])
        lista_glicose.append(estado['G'])
        lista_biomassa.append(estado['X'])
        lista_etanol.append(estado['E'])

        # 5.5) critério de parada: tanto O quanto G praticamente esgotados
        if estado['O'] <= 1e-3 and estado['G'] <= 1e-3:
            break

    # 6) Cálculo de métricas finais
    # Conversão de oligossacarídeos (%)
    conversao_O_pct = ((concentracao_oligossacarideos_inicial - estado['O']) /
                       concentracao_oligossacarideos_inicial) * 100.0

    # Conversão de glicose (%)
    #   total de glicose disponível = glicose inicial + glicose gerada por O
    glicose_disponivel = concentracao_glicose_inicial + concentracao_oligossacarideos_inicial
    #   glicose final = estado['G']
    conversao_G_pct = ((glicose_disponivel - estado['G']) / glicose_disponivel) * 100.0 if glicose_disponivel > 0 else 0.0

    return {
        "tempo_h": lista_tempo,
        "oligossacarideos_g_L": lista_oligossacarideos,
        "glicose_g_L": lista_glicose,
        "biomassa_g_L": lista_biomassa,
        "etanol_g_L": lista_etanol,
        "concentracao_etanol_final": estado['E'],
        "conversao_oligossacarideos_percentual": conversao_O_pct,
        "conversao_glicose_percentual": conversao_G_pct,
        "concentracao_oligossacarideos_inicial": concentracao_oligossacarideos_inicial,
        "concentracao_glicose_inicial": concentracao_glicose_inicial,
        "concentracao_oligossacarideos_final": estado['O'],
        "concentracao_glicose_final": estado['G'],
        "concentracao_biomassa_final": estado['X'],
        "tempo_simulacao_h": t,
        "parametros_sacarificacao": params_sacarificacao,
        "parametros_fermentacao": params_fermentacao
    }
