import math

def calculate_ir(annual_net_imposable, parts=1):
    """
    Calcule l'impôt sur le revenu (IR) 2024 (sur revenus 2023)
    annual_net_imposable : Revenu net imposable annuel (après déduction frais pro 10% si applicable, mais ici c'est le net perçu avant abattement 10% standard)
    Note: Le barème s'applique au revenu imposable après abattement de 10%.
    """
    
    # Abattement forfaitaire de 10% (min 472€, max 14 171€ pour 2024 par personne)
    # On simplifie ici en prenant 10% pur pour l'instant, borné si besoin mais pour les salaires de dirigeants TNS/SASU c'est classique.
    # Pour une SASU (assimilé salarié), le net imposable est proche du net perçu + CSG/CRDS non déductible.
    # Simplification demandée : on part du "Salaire net avant IR" comme base.
    
    # Abattement 10%
    assiette = annual_net_imposable * 0.9
    
    # Quotient familial
    qf = assiette / parts
    
    # Barème 2024
    brackets = [
        (0, 11294, 0.00),
        (11294, 28797, 0.11),
        (28797, 82341, 0.30),
        (82341, 177106, 0.41),
        (177106, float('inf'), 0.45)
    ]
    
    tax_per_part = 0
    for low, high, rate in brackets:
        if qf > low:
            taxable_in_bracket = min(qf, high) - low
            tax_per_part += taxable_in_bracket * rate
            
    total_tax = math.floor(tax_per_part * parts)
    return total_tax

def inverse_salary_from_net_after_tax(monthly_net_cash_target, parts=1, monthly_benefit_in_kind=0):
    """
    Retrouve le coût entreprise pour garantir un net cash (virement bancaire) cible.
    Variable: monthly_benefit_in_kind (AEN) = Avantage en nature (ex: voiture).
    """
    annual_target_cash = monthly_net_cash_target * 12
    annual_aen = monthly_benefit_in_kind * 12
    
    # On cherche "Annual Net Imposable"
    # Target "Net après impôt" THÉORIQUE = Cash_Volume + AEN_Volume
    target_annual_net_after_tax_total_value = annual_target_cash + annual_aen
    
    # Recherche dichotomique sur le NET IMPOSABLE
    low = target_annual_net_after_tax_total_value
    high = target_annual_net_after_tax_total_value * 3
    
    for _ in range(50):
        mid = (low + high) / 2
        ir = calculate_ir(mid, parts)
        net_after_tax_value = mid - ir # Value available (Cash + Kind)
        
        if abs(net_after_tax_value - target_annual_net_after_tax_total_value) < 1.0:
            break
            
        if net_after_tax_value < target_annual_net_after_tax_total_value:
            low = mid
        else:
            high = mid
            
    annual_net_imposable = (low + high) / 2
    annual_ir = calculate_ir(annual_net_imposable, parts)
    
    # Reconstruction des flux
    # Net Imposable = Net A Payer Cash (approx) + AEN
    annual_net_cash_before_ir = annual_net_imposable - annual_aen
    
    # Brut et Charges (calculés sur le Brut qui INCLUT l'AEN)
    # Net Imposable ~ 78% du Brut
    annual_gross_salary = annual_net_imposable / 0.78
    
    # Charges patronales : 45% sur le Brut
    annual_employer_charges = annual_gross_salary * 0.45
    annual_employer_cost = annual_gross_salary + annual_employer_charges 
    
    # Sortie Cash Entreprise = Coût Total - AEN (car AEN payé par ailleurs)
    annual_cash_out_salary = annual_employer_cost - annual_aen

    return {
        "monthly_net_cash_after_ir": monthly_net_cash_target,
        "monthly_aen": monthly_benefit_in_kind,
        "monthly_ir": annual_ir / 12,
        "monthly_net_cash_before_ir": annual_net_cash_before_ir / 12,
        "annual_gross": annual_gross_salary,
        "annual_employer_cost_total": annual_employer_cost,
        "monthly_employer_cost_total": annual_employer_cost / 12,
        "annual_salary_cash_out": annual_cash_out_salary        
    }

def calculate_company_results(annual_ca, annual_charges, annual_salary_cash_cost, annual_car_cost=0, annual_car_non_deductible=0):
    """
    annual_salary_cash_cost: Le décaissement réel pour les salaires.
    annual_car_cost: Le décaissement réel pour la voiture (Leasing, essence...).
    annual_car_non_deductible: La part de la voiture à réintégrer fiscalement.
    """
    # 1. Résultat Comptable (Cash flow view)
    result_accounting = annual_ca - annual_charges - annual_salary_cash_cost - annual_car_cost
    
    # 2. Résultat Fiscal (Assiette IS)
    # Réintégration des charges non déductibles
    result_fiscal = result_accounting + annual_car_non_deductible
    
    if result_fiscal <= 0:
        is_tax = 0
    else:
        # Calcul IS sur résultat FISCAL
        limit_reduced_rate = 42500
        if result_fiscal <= limit_reduced_rate:
            is_tax = result_fiscal * 0.15
        else:
            is_tax = (limit_reduced_rate * 0.15) + ((result_fiscal - limit_reduced_rate) * 0.25)
            
    # 3. Résultat Net (Distributable)
    result_net_distributable = result_accounting - is_tax
    
    if result_net_distributable < 0:
        result_net_distributable = 0
        dividends_net = 0
    else:
        # Flat tax 30%
        dividends_net = result_net_distributable * (1 - 0.30)
    
    return {
        "result_before_is_accounting": result_accounting,
        "result_before_is_fiscal": result_fiscal,
        "is_tax": is_tax,
        "result_after_is": result_net_distributable,
        "dividends_net": dividends_net
    }
