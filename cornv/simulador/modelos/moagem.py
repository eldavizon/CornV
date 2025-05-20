import math

def calcular_moagem(massa_milho_kg):
    
    """
    Simula a moagem do milho.

    Args:
        massa_milho_kg (float): massa de milho a moer em kg.
        d1_mm (float): tamanho médio inicial do milho em mm (padrão: 4.22 mm).
        d2_mm (float): tamanho médio final moído em mm (padrão: 0.5 mm).
        eficiencia (float): eficiência da moagem (padrão: 90%).
        k (float): constante de Rittinger (padrão: 1.5 kJ/kg·m)

    Returns:
        dict: energia total (kJ), massa moída (kg), rendimento (%)
    """
    
    try:
        print(f"Massa de milho: {massa_milho_kg}")
        massa_milho_kg = float(massa_milho_kg)

    except (ValueError, TypeError):
        raise ValueError("massa_milho_kg deve ser um número.")
    
    '''      
    # Lei de Rittinger
    
    eficiencia=0.9
    k=1.5
    
    # Converter mm para metros
    d1 = d1_mm / 1000
    d2 = d2_mm / 1000

    # Energia específica
    energia_especifica = k * (1 / d2 - 1 / d1)  # kJ/kg

    # Energia total (kJ)
    energia_total = energia_especifica * massa_milho_kg

    # Massa moída real (com perdas)
    massa_moida = massa_milho_kg * eficiencia'''
    
    d1_mm=4.22 #diametro medio inicial
    d2_mm=0.2  # diametro medio final ( de 80% das particulas)
    wi = 0.0811  # work index do milho
    
    energia_especifica = 10 * wi * ( (1/math.sqrt(d2_mm)) - (1/(math.sqrt(d1_mm))))
    
    # energia total em kWh
    
    energia_total = energia_especifica * massa_milho_kg
    
    # considerando como se toda a massa fosse moída; só estamos medindo a energia.
    massa_moida = massa_milho_kg
    
    
    return {
        "massa_entrada": massa_milho_kg,
        "massa_moida": round(massa_moida, 2),
        "energia_total_kWh": round(energia_total, 2)
    }
