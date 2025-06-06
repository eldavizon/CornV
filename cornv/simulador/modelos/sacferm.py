def simular_etanol(
    concentracao_oligossacarideos_inicial: float = 120.0,
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
    Simula o processo combinado de sacarificação e fermentação para produção de etanol
    
    Args:
        concentracao_oligossacarideos_inicial: Concentração inicial de oligossacarídeos (g/L)
        concentracao_biomassa_inicial: Concentração inicial de biomassa (g/L)
        tempo_simulacao_h: Tempo total de simulação (horas)
        passo_temporal_h: Passo de tempo para integração (horas)
        ... (demais parâmetros cinéticos)
    
    Returns:
        Dicionário com resultados da simulação no formato:
        {
            "tempo_h": lista_tempo,
            "oligossacarideos_g_L": lista_oligossacarideos,
            "glicose_g_L": lista_glicose,
            "biomassa_g_L": lista_biomassa,
            "etanol_g_L": lista_etanol,
            "concentracao_etanol_final": valor_etanol_final,
            "conversao_percentual": valor_conversao,
            ... (demais métricas)
        }
    """
    # Parâmetros do processo
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

    # Funções auxiliares (manter as mesmas)
    def calcular_sacarificacao(O, E, params):
        Vmax = params['Vmax']
        Km = params['Km']
        Ki_etanol = params['Ki_etanol']
        v_sac = (Vmax * O) / (Km + O) * (1 / (1 + E/Ki_etanol))
        return v_sac

    def calcular_fermentacao(G, X, E, params):
        mu_max = params['mu_max']
        Ks = params['Ks']
        Yxs = params['Yxs']
        Yps = params['Yps']
        Kp_etanol = params['Kp_etanol']
        
        mu = mu_max * (G / (Ks + G)) * max(0, (1 - E/Kp_etanol))
        dG_cons = (mu / Yxs) * X
        dE_prod = Yps * dG_cons
        return mu, dG_cons, dE_prod

    # Condições iniciais
    estado = {
        'O': concentracao_oligossacarideos_inicial,
        'G': 0.0,
        'X': concentracao_biomassa_inicial,
        'E': 0.0
    }

    # Listas para armazenar resultados
    lista_tempo = [0]
    lista_oligossacarideos = [estado['O']]
    lista_glicose = [estado['G']]
    lista_biomassa = [estado['X']]
    lista_etanol = [estado['E']]

    # Simulação com Euler Explícito
    t = 0
    while t < tempo_simulacao_h:
        # Calcular taxas
        v_sac = calcular_sacarificacao(estado['O'], estado['E'], params_sacarificacao)
        mu, dG_cons, dE_prod = calcular_fermentacao(estado['G'], estado['X'], estado['E'], params_fermentacao)
        
        # Calcular derivadas
        dO_dt = -v_sac
        dG_dt = v_sac - dG_cons
        dX_dt = mu * estado['X']
        dE_dt = dE_prod
        
        # Atualizar estado
        estado['O'] = max(estado['O'] + dO_dt * passo_temporal_h, 0)
        estado['G'] = max(estado['G'] + dG_dt * passo_temporal_h, 0)
        estado['X'] = max(estado['X'] + dX_dt * passo_temporal_h, 0)
        estado['E'] = estado['E'] + dE_dt * passo_temporal_h
        
        # Avançar no tempo e registrar
        t += passo_temporal_h
        lista_tempo.append(t)
        lista_oligossacarideos.append(estado['O'])
        lista_glicose.append(estado['G'])
        lista_biomassa.append(estado['X'])
        lista_etanol.append(estado['E'])
        
        # Critério de parada
        if estado['O'] <= 1e-3 and estado['G'] <= 1e-3:
            break

    # Cálculo de métricas finais
    conversao_percentual = ((concentracao_oligossacarideos_inicial - estado['O']) / 
                          concentracao_oligossacarideos_inicial) * 100

    return {
        "tempo_h": lista_tempo,
        "oligossacarideos_g_L": lista_oligossacarideos,
        "glicose_g_L": lista_glicose,
        "biomassa_g_L": lista_biomassa,
        "etanol_g_L": lista_etanol,
        "concentracao_etanol_final": estado['E'],
        "conversao_percentual": conversao_percentual,
        "concentracao_oligossacarideos_inicial": concentracao_oligossacarideos_inicial,
        "concentracao_oligossacarideos_final": estado['O'],
        "concentracao_biomassa_final": estado['X'],
        "tempo_simulacao_h": t,
        "parametros_sacarificacao": params_sacarificacao,
        "parametros_fermentacao": params_fermentacao
    }