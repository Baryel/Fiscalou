import streamlit as st
import pandas as pd
from fiscal_logic import inverse_salary_from_net_after_tax, calculate_company_results

st.set_page_config(page_title="Simulateur Fiscal SASU", layout="wide")

st.title("🇫🇷 Simulateur Fiscal SASU")
st.markdown("Optimisez votre rémunération entre salaire et dividendes.")

# --- Sidebar Inputs ---
st.sidebar.header("Paramètres")

monthly_revenue = st.sidebar.number_input("Chiffre d'Affaires Mensuel (HT)", min_value=0.0, value=10000.0, step=500.0)
monthly_expenses = st.sidebar.number_input("Charges Mensuelles (hors salaire)", min_value=0.0, value=500.0, step=100.0)
target_net_after_ir = st.sidebar.number_input("Salaire Net Après IR Souhaité (Mensuel)", min_value=0.0, value=1700.0, step=100.0)
fiscal_parts = st.sidebar.number_input("Nombre de parts fiscales", min_value=1.0, value=1.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("🚗 Véhicule de Société")
car_enabled = st.sidebar.checkbox("Activer Véhicule", value=False)

if car_enabled:
    col_car_1, col_car_2 = st.sidebar.columns(2)
    car_monthly_lease = col_car_1.number_input("Loyer Mensuel", value=500.0, step=50.0)
    car_duration = col_car_2.number_input("Durée (Mois)", value=36, step=12)
    car_initial_contribution = st.sidebar.number_input("Apport Initial (1er loyer majoré)", value=0.0, step=500.0)
    
    simulation_mode = st.sidebar.radio(
        "Mode de calcul", 
        ["Lissé (Moyenne)", "Année 1 (Paiement Apport)"], 
        help="Lissé : Étale l'apport sur la durée.\nAnnée 1 : Déduit l'apport total maintenant."
    )
    
    if simulation_mode == "Lissé (Moyenne)":
        car_monthly_cost = car_monthly_lease + (car_initial_contribution / car_duration)
        annual_car_cost = car_monthly_cost * 12
        st.sidebar.caption(f"👉 Coût annuel : **{annual_car_cost:,.0f} €** (Moyenne)")
    else:
        # Année 1 : On compte 12 loyers + l'apport (ou 11 + apport, mais restons simples : c'est du cash out)
        # Souvent l'apport EST le 1er loyer. Donc on paierait Apport + 11 loyers.
        # Simplification : Flux annuel = Apport + (11 * Loyer)
        annual_car_cost = car_initial_contribution + (car_monthly_lease * 11)
        # Mais pour recalculer le "monthly" equivalent pour l'affichage, on divise par 12
        car_monthly_cost = annual_car_cost / 12
        st.sidebar.caption(f"👉 Coût année 1 : **{annual_car_cost:,.0f} €** (Cash)")
    
    car_annual_non_deductible = st.sidebar.number_input("Part non déductible (Amort. excédentaire annuel)", value=0.0, step=100.0)
    car_monthly_aen = st.sidebar.number_input("Avantage en Nature Mensuel", value=200.0, step=10.0)
else:
    car_monthly_cost = 0.0
    annual_car_cost = 0.0
    car_annual_non_deductible = 0.0
    car_monthly_aen = 0.0

# --- Calculations ---

# 1. Salary Reverse Calculation
salary_details = inverse_salary_from_net_after_tax(target_net_after_ir, fiscal_parts, car_monthly_aen)

# 2. Company Annual Calculation
annual_revenue = monthly_revenue * 12
annual_expenses = monthly_expenses * 12
# annual_car_cost is already calculated above based on mode

company_results = calculate_company_results(
    annual_revenue, 
    annual_expenses, 
    salary_details["annual_salary_cash_out"], 
    annual_car_cost, 
    car_annual_non_deductible
)

# 3. Finals
total_annual_personal = (salary_details["monthly_net_cash_after_ir"] * 12) + company_results["dividends_net"]
monthly_average = total_annual_personal / 12

# --- Display ---

st.divider()

# 🏆 HEADLINE RESULT
st.subheader("💰 Rémunération Mensuelle Moyenne (Net)")
col_main, col_chart = st.columns([1, 2])

with col_main:
    st.metric(
        label="Total Mensuel (Salaire + Dividendes/12)",
        value=f"{monthly_average:,.0f} €",
        delta=f"{monthly_average - target_net_after_ir:,.0f} € via Dividendes"
    )
    if car_enabled:
        st.caption("Inclut Salaire Net Cash + Dividendes. (Hors Avantage Nature)")
    st.caption("Ce montant inclut votre salaire net mensuel et le lissage mensuel de vos dividendes annuels nets.")

with col_chart:
    # Bar chart composition
    chart_df = pd.DataFrame({
        "Source": ["Salaire Net", "Dividendes (Lissés)"],
        "Montant": [salary_details['monthly_net_cash_after_ir'], company_results['dividends_net'] / 12]
    })
    st.bar_chart(chart_df.set_index("Source"), horizontal=True, height=200)

st.divider()

# 📂 DETAILED TABS
tab_synthese, tab_salaire, tab_entreprise = st.tabs(["📊 Synthèse & Dividendes", "👤 Détail Salaire", "🏢 Détail Entreprise"])

with tab_synthese:
    st.markdown("#### Dividendes de fin d'année")
    c1, c2, c3 = st.columns(3)
    c1.metric("Bénéfice (Avant IS)", f"{company_results['result_before_is_accounting']:,.0f} €")
    c2.metric("IS (Impôt Société)", f"{company_results['is_tax']:,.0f} €")
    c3.metric("Dividendes Nets (Poche)", f"{company_results['dividends_net']:,.0f} €")
    
    st.info(f"En vous versant **{target_net_after_ir:,.0f} €** de salaire net/mois, il reste **{company_results['dividends_net']:,.0f} €** de dividendes nets en fin d'année.")

with tab_salaire:
    st.markdown("#### Simulation Fiche de Paie (Mensuel)")
    
    sal_col1, sal_col2 = st.columns(2)
    with sal_col1:
        st.write(" **Votre Poche**")
        st.success(f"**Net Après Impôt : {salary_details['monthly_net_cash_after_ir']:,.2f} €**")
        st.write(f"Net Avant Impôt (Cash) : {salary_details['monthly_net_cash_before_ir']:,.2f} €")
        st.write(f"Impôt Revenu (Est.) : {salary_details['monthly_ir']:,.2f} €")
        if car_enabled:
            st.info(f"Avantage Nature (Non Cash) : {salary_details['monthly_aen']:,.2f} €")

    with sal_col2:
        st.write(" **Coût pour l'Entreprise**")
        st.error(f"**Sortie Cash Salaire : {salary_details['monthly_employer_cost_total'] - salary_details['monthly_aen']:,.2f} €**")
        st.write(f"Salaire Brut : {salary_details['annual_gross']/12:,.2f} €")
        st.write(f"Total Chargé (Base) : {salary_details['monthly_employer_cost_total']:,.2f} €")
        st.caption("Charges patronales estimées à ~45%")

with tab_entreprise:
    st.markdown("#### Compte de Résultat Simplifié (Annuel)")
    
    # Use container for cleaner look
    with st.container():
        row1 = st.columns([3, 1])
        row1[0].write("➕ Chiffre d'Affaires")
        row1[1].write(f"**{annual_revenue:,.0f} €**")
        
        row2 = st.columns([3, 1])
        row2[0].write("➖ Charges Externes")
        row2[1].write(f"- {annual_expenses:,.0f} €")
        
        row3 = st.columns([3, 1])
        row3[0].write("➖ Masse Salariale (Cash Only)")
        row3[1].write(f"- {salary_details['annual_salary_cash_out']:,.0f} €")
        
        if car_enabled:
            row_car = st.columns([3, 1])
            row_car[0].write("➖ Véhicule (Coût lissé)")
            row_car[1].write(f"- {annual_car_cost:,.0f} €")
            
        st.divider()
        
        row4 = st.columns([3, 1])
        row4[0].write("🟰 Résultat Comptable")
        row4[1].write(f"**{company_results['result_before_is_accounting']:,.0f} €**")
        
        if car_enabled and car_annual_non_deductible > 0:
            row_fiscal = st.columns([3, 1])
            row_fiscal[0].write("ℹ️ _dont Réintégration Fiscale (Non déductible)_")
            row_fiscal[1].write(f"_{(car_annual_non_deductible):,.0f} €_")
        
        row5 = st.columns([3, 1])
        row5[0].write("➖ Impôt Sociétés (IS)")
        row5[1].write(f"**- {company_results['is_tax']:,.0f} €**")
        
        st.divider()
        
        row6 = st.columns([3, 1])
        row6[0].write("💰 Bénéfice Net (Dividendes Bruts)")
        row6[1].write(f"**{company_results['result_after_is']:,.0f} €**")
