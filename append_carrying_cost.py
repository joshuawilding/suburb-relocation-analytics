import pandas as pd

print("Loading Master Dataset...")
df_seda = pd.read_csv('tri_state_master_with_niche.csv')

# Average Effective Property Tax Rates by County (Estimates)
tax_rates = {
    # New Jersey (~2.0% - 2.8% generally)
    'Bergen County': 2.30,
    'Essex County': 2.80,
    'Union County': 2.65,
    'Morris County': 2.20,
    'Hudson County': 2.10,
    'Passaic County': 2.70,
    'Somerset County': 2.35,
    'Middlesex County': 2.25,
    'Monmouth County': 1.95,
    
    # New York (Downstate is heavily taxed, ~2.0% - 2.5%)
    'Nassau County': 2.25,
    'Suffolk County': 2.15,
    'Westchester County': 2.40,
    'Rockland County': 2.50,
    
    # Connecticut (Fairfield Mill Rates average out to ~1.8% - 2.0% effective)
    'Fairfield County': 1.90
}

df_seda['Estimated_Tax_Rate'] = df_seda['County'].map(tax_rates)

# Assume 2.2% if county is missing somehow
df_seda['Estimated_Tax_Rate'] = df_seda['Estimated_Tax_Rate'].fillna(2.20)

# Financial Assumptions
DOWN_PAYMENT_PCT = 0.20
INTEREST_RATE = 0.065
TERM_MONTHS = 360

def calculate_monthly_payment(price, tax_rate):
    if pd.isna(price):
        return pd.NA
        
    loan_amount = price * (1.0 - DOWN_PAYMENT_PCT)
    monthly_interest = INTEREST_RATE / 12.0
    
    # Principal + Interest (Amortization Formula)
    if monthly_interest > 0:
        p_and_i = loan_amount * (monthly_interest * (1 + monthly_interest)**TERM_MONTHS) / ((1 + monthly_interest)**TERM_MONTHS - 1)
    else:
        p_and_i = loan_amount / TERM_MONTHS
        
    # Property Taxes
    annual_taxes = price * (tax_rate / 100.0)
    monthly_taxes = annual_taxes / 12.0
    
    # Homeowners Insurance (Assume flat 0.2% of home value annually, very rough estimate)
    monthly_insurance = (price * 0.002) / 12.0
    
    return round(p_and_i + monthly_taxes + monthly_insurance, 0)

df_seda['True_Monthly_Carrying_Cost'] = df_seda.apply(lambda row: calculate_monthly_payment(row['Current_3BR_Price_Mean'], row['Estimated_Tax_Rate']), axis=1)

df_seda.to_csv('tri_state_master_with_niche.csv', index=False)
print("Carrying Costs Appended!")
