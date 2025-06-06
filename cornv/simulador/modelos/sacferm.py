def simular_etanol(
    concentracao_art_inicial: float,
    concentracao_oligossacarideos_inicial: float,
    concentracao_biomassa_inicial: float,
    tempo_simulacao_h: float = 50,
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
    
    def calcular_sacarificacao(O, E):
        return (Vmax_sacarificacao * O) / (Km_sacarificacao + O + 1e-8) * (1 / (1 + E / (Ki_etanol_sacarificacao + 1e-8)))

    def calcular_fermentacao(ART, X, E):
        mu = mu_max_fermentacao * (ART / (Ks_fermentacao + ART)) * max(0, 1 - E / Kp_etanol_fermentacao)
        dART_cons = (mu / Yxs_fermentacao) * X
        dE_prod = Yps_fermentacao * dART_cons
        return mu, dART_cons, dE_prod

    estado = {
        'ART': concentracao_art_inicial,
        'O': concentracao_oligossacarideos_inicial,
        'X': concentracao_biomassa_inicial,
        'E': 0.0,
    }

    lista_tempo = [0]
    lista_art_total = [estado['ART']]
    lista_oligossacarideos = [estado['O']]
    lista_biomassa = [estado['X']]
    lista_etanol = [estado['E']]

    t = 0.0
    while t < tempo_simulacao_h:
        v_sac = calcular_sacarificacao(estado['O'], estado['E'])
        mu, dART_cons, dE_prod = calcular_fermentacao(
            estado['ART'], estado['X'], estado['E']
        )

        dART_dt = v_sac - dART_cons
        dO_dt = -v_sac
        dX_dt = mu * estado['X']
        dE_dt = dE_prod

        estado['ART'] = max(estado['ART'] + dART_dt * passo_temporal_h, 0.0)
        estado['O'] = max(estado['O'] + dO_dt * passo_temporal_h, 0.0)
        estado['X'] = max(estado['X'] + dX_dt * passo_temporal_h, 0.0)
        estado['E'] += dE_dt * passo_temporal_h

        t += passo_temporal_h
        lista_tempo.append(t)
        lista_art_total.append(estado['ART'])
        lista_oligossacarideos.append(estado['O'])
        lista_biomassa.append(estado['X'])
        lista_etanol.append(estado['E'])

        if estado['ART'] <= 1e-3 and estado['O'] <= 1e-3:
            break

    substrato_total_inicial = concentracao_art_inicial + concentracao_oligossacarideos_inicial
    substrato_total_consumido = (concentracao_art_inicial - estado['ART'] +
                                 concentracao_oligossacarideos_inicial - estado['O'])
    conversao_percentual = (substrato_total_consumido / substrato_total_inicial) * 100
    rendimento_etanol = (estado['E'] / substrato_total_inicial) * 100

    return {
        "tempo_h": lista_tempo,
        "glicose_total_g_L": lista_art_total,
        "oligossacarideos_g_L": lista_oligossacarideos,
        "biomassa_g_L": lista_biomassa,
        "etanol_g_L": lista_etanol,
        "concentracao_etanol_final": estado['E'],
        "conversao_percentual": conversao_percentual,
        "rendimento_etanol_percentual": rendimento_etanol,
        "biomassa_final": estado['X'],
        "tempo_processo_h": t
    }
