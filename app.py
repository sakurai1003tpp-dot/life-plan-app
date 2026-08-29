import streamlit as st
import matplotlib.pyplot as plt

# グラフを高解像度（鮮明）に設定
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

# スマホでも見やすいように画面全体を使う設定
st.set_page_config(page_title="Life Plan Simulation", layout="wide")
st.title("📊 Life Plan Simulation")

# ------------------------------------------
# サイドバーに設定パネルを作成
# ------------------------------------------
st.sidebar.header("👨‍👩‍👧‍👦 Family & Work Settings")
current_age_h = st.sidebar.slider("Husband's Age", 20, 60, 29)
current_age_w = st.sidebar.slider("Wife's Age", 20, 60, 30)
retirement_age_h = st.sidebar.slider("Husband's Retirement Age", 50, 75, 65)
retirement_age_w = st.sidebar.slider("Wife's Retirement Age", 50, 75, 55)
pension_start_age_h = st.sidebar.slider("Husband's Pension Start Age", 60, 75, 65)
pension_start_age_w = st.sidebar.slider("Wife's Pension Start Age", 60, 75, 70)

st.sidebar.header("💰 Income Settings")
gross_income_h_start = st.sidebar.number_input("Husband's Income (10k JPY)", 0, 5000, 720, step=10)
gross_income_w = st.sidebar.number_input("Wife's Income (10k JPY)", 0, 5000, 400, step=10)
income_change_rate_w = st.sidebar.slider("Wife's Income Growth Rate (%/year)", 0.0, 5.0, 1.25, step=0.05)

st.sidebar.header("📈 Asset & Investment Settings")
current_cash = st.sidebar.number_input("Current Cash (10k JPY)", 0, 50000, 1000, step=50)
current_investment = st.sidebar.number_input("Current Mutual Funds (10k JPY)", 0, 50000, 1300, step=50)
current_stock = st.sidebar.number_input("Current Stocks (10k JPY)", 0, 50000, 300, step=50)
annual_return_rate = st.sidebar.slider("Mutual Funds Return Rate (%)", 0.0, 10.0, 4.0, step=0.1)

st.sidebar.header("🏠 Housing & Living Expenses")
living_expenses = st.sidebar.number_input("Base Living Expenses (Annual)", 0, 2000, 400, step=10)
regional_house_cost = st.sidebar.number_input("Retirement House Cost", 0, 20000, 5000, step=100)

# ------------------------------------------
# 基本設定（固定値）
# ------------------------------------------
overtime_hours_per_month = 45
overtime_multiplier = 1.25
child_care_reduction_years = 5     
child_care_income_reduction_rate = 0.30  
stock_return_rate = 1.5     
stock_dividend_yield = 2.5  
min_cash_reserve = 500      
max_cash_limit = 1000       
investment_stop_age_h = 60  
retirement_payout_h = 2000  
retirement_payout_w = 500   
migration_housing_expenses = 50 
housing_expenses_base = 180     
annual_travel_cost = 30         
general_medical_cost = 5        
annual_social_cost = 20         
expense_change_rate = 1.5       
housing_increase_on_child = 60  
wedding_cost = 200              
migration_living_expense_ratio = 0.80  
migration_medical_cost_multiplier = 4.0 

car_maintenance_cost = 40      
car_purchase_price = 300       
car_replacement_cycle = 10     
annual_car_depreciation = car_purchase_price / car_replacement_cycle
total_annual_car_cost = car_maintenance_cost + annual_car_depreciation

child_count = 1                
first_birth_age_h = 31         
birth_interval = 3             
maternity_leave_per_child = 3  

child_courses = {1: 'PUBLIC_UNIV_RIKEI', 2: 'PUBLIC_UNIV_PRIVATE', 3: 'ALL_PUBLIC'}
course_labels = {'PUBLIC_UNIV_RIKEI': 'Science/Public', 'PUBLIC_UNIV_PRIVATE': 'Liberal Arts/Private', 'ALL_PUBLIC': 'All Public'}

# --- 出産・育休期間の計算 ---
birth_ages_h, birth_ages_w = [], []
if child_count > 0:
    for n in range(child_count):
        b_h = first_birth_age_h + (n * birth_interval)
        birth_ages_h.append(b_h)
        birth_ages_w.append(current_age_w + (b_h - current_age_h))

maternity_leave_years_w = []
for b_w in birth_ages_w:
    for y in range(maternity_leave_per_child):
        maternity_leave_years_w.append(b_w + y)
maternity_leave_years_w = sorted(list(set(maternity_leave_years_w)))

reduced_income_years_w = []
for b_w in birth_ages_w:
    start_y = b_w + maternity_leave_per_child
    for y in range(child_care_reduction_years):
        reduced_income_years_w.append(start_y + y)
reduced_income_years_w = sorted(list(set(reduced_income_years_w)))

# --- 収入・年金計算関数 ---
def calculate_husband_base_gross_income(age):
    if age < 29 or age >= retirement_age_h: return 0
    elif age <= 41: 
        return 532.72 + (age - 29) * ((887.86 - 532.72) / 12)
    elif age <= 59: 
        return 1000.0 + (age - 42) * ((1400.0 - 1000.0) / 17)
    elif age <= 64: return 1400.0 * 0.70
    return 0

def calculate_husband_gross_income(age):
    base = calculate_husband_base_gross_income(age)
    if base <= 0: return 0
    if age < 42:
        hourly_rate = (base * 10000) / 1920
        annual_overtime_pay = hourly_rate * overtime_multiplier * overtime_hours_per_month * 12
        return base + (annual_overtime_pay / 10000)
    else:
        return base  

def estimate_pension_h():
    return (81.3 + (100 * 0.005481 * 12 * (65 - 22))) * 0.87

def estimate_pension_w():
    actual_leave_years = len(maternity_leave_years_w)
    work_years_w = max(0, (retirement_age_w - 22) - actual_leave_years)
    base_pension = 81.3 + ((gross_income_w / 12) * 0.005481 * 12 * work_years_w)
    return base_pension * 1.42 * 0.87

calculated_pension_h = estimate_pension_h()
calculated_pension_w = estimate_pension_w()

def calculate_net_income(gross):
    if gross <= 0: return 0
    elif gross <= 300: return gross * 0.85
    elif gross <= 600: return gross * 0.80
    elif gross <= 1000: return gross * 0.75
    else: return gross * 0.70

# --- シミュレーション用リスト ---
age_history, total_wealth_history, cash_history, investment_history, stock_history = [], [], [], [], []
net_income_history, total_expense_history, annual_balance_history = [], [], []
child1_history, child2_history, child3_history, total_child_expense_history = [], [], [], []
cash_ratio_history, investment_ratio_history, stock_ratio_history = [], [], []
husband_gross_history, wife_gross_history, pension_gross_history, household_gross_history = [], [], [], []
husband_net_history, wife_net_history, pension_net_history, household_net_history = [], [], [], []

# --- ループ処理 ---
for i in range(100 - current_age_h + 1):
    age_h = current_age_h + i
    age_w = current_age_w + i
    
    annual_dividend = 0
    if i > 0:
        current_investment = current_investment * (1 + annual_return_rate / 100)
        current_stock = current_stock * (1 + stock_return_rate / 100)
        annual_dividend = (current_stock * (stock_dividend_yield / 100)) * 0.79685 
    
    net_h = calculate_net_income(calculate_husband_gross_income(age_h)) if age_h < retirement_age_h else 0
    
    if age_w < retirement_age_w:
        if age_w in maternity_leave_years_w:
            current_gross_w = 0
        else:
            base_w = gross_income_w * ((1 + income_change_rate_w / 100) ** i)
            if age_w in reduced_income_years_w: base_w *= (1 - child_care_income_reduction_rate)
            current_gross_w = base_w
        net_w = calculate_net_income(current_gross_w)
    else:
        current_gross_w = 0
        net_w = 0

    extra_retirement_cash = (retirement_payout_w if age_w == retirement_age_w else 0) + (retirement_payout_h if age_h == retirement_age_h else 0)
    current_pension_gross = (calculated_pension_h if age_h >= pension_start_age_h else 0) + (calculated_pension_w if age_w >= pension_start_age_w else 0)
    current_pension_net = current_pension_gross * 0.85 if current_pension_gross > 0 else 0

    total_gross = calculate_husband_gross_income(age_h) + current_gross_w + current_pension_gross
    pure_annual_income = net_h + net_w + current_pension_net + annual_dividend
        
    is_migrated = (age_h >= retirement_age_h and age_w >= retirement_age_h)
    
    if not is_migrated:
        rate_factor_exp = (1 + expense_change_rate / 100) ** i
        current_housing = housing_expenses_base + (housing_increase_on_child if (child_count > 0 and age_h >= first_birth_age_h) else 0)
        annual_expense = (living_expenses + current_housing + annual_travel_cost + general_medical_cost + annual_social_cost) * rate_factor_exp
    else:
        retirement_start_i = retirement_age_h - current_age_h
        base_expense_fixed = ((living_expenses * migration_living_expense_ratio) + migration_housing_expenses + total_annual_car_cost + annual_travel_cost + annual_social_cost) * ((1 + expense_change_rate / 100) ** retirement_start_i)
        annual_expense = (base_expense_fixed * (0.90 if age_h >= 75 else 1.0)) + (general_medical_cost * migration_medical_cost_multiplier)
    
    extra_one_time_expense = wedding_cost if i == 1 else 0
    c1_exp, c2_exp, c3_exp = 0, 0, 0
    if child_count >= 1:
        c1_age = age_h - first_birth_age_h
        if 0 <= c1_age <= 22:
            c1_exp = 60 if c1_age <= 6 else (90 if c1_age <= 12 else (110 if c1_age <= 15 else (100 if c1_age <= 18 else 260)))
    if child_count >= 2:
        c2_age = age_h - (first_birth_age_h + birth_interval)
        if 0 <= c2_age <= 22:
            c2_exp = 60 if c2_age <= 6 else (90 if c2_age <= 12 else (110 if c2_age <= 15 else (100 if c2_age <= 18 else 220)))

    total_child_expense = c1_exp + c2_exp + c3_exp
    pure_total_expense = annual_expense + total_child_expense + extra_one_time_expense
    pure_annual_balance = pure_annual_income - pure_total_expense
    
    current_cash += pure_annual_balance + extra_retirement_cash
    
    if age_h == retirement_age_h:
        current_cash += current_stock
        current_stock = 0
        needed = regional_house_cost - current_cash
        if needed > 0:
            sale = min(needed, current_investment)
            current_investment -= sale
            current_cash += sale
        current_cash -= regional_house_cost

    if current_cash < min_cash_reserve:
        shortfall = min_cash_reserve - current_cash 
        if current_stock >= shortfall:
            current_stock -= shortfall
            current_cash += shortfall 
        else:
            shortfall -= current_stock
            current_cash += current_stock
            current_stock = 0
            if current_investment >= shortfall:
                current_investment -= shortfall
                current_cash += shortfall
            else:
                current_cash += current_investment
                current_investment = 0
    elif age_h < investment_stop_age_h and current_cash > max_cash_limit:
        excess = current_cash - max_cash_limit
        current_cash = max_cash_limit
        current_investment += excess
            
    total_wealth = current_cash + current_investment + current_stock
    c_ratio = (current_cash / total_wealth) * 100 if total_wealth > 0 else 100
    i_ratio = (current_investment / total_wealth) * 100 if total_wealth > 0 else 0
    s_ratio = (current_stock / total_wealth) * 100 if total_wealth > 0 else 0
        
    age_history.append(age_h)
    total_wealth_history.append(total_wealth)
    cash_history.append(current_cash)
    investment_history.append(current_investment)
    stock_history.append(current_stock)
    net_income_history.append(pure_annual_income)
    total_expense_history.append(pure_total_expense)
    annual_balance_history.append(pure_annual_balance)
    child1_history.append(c1_exp)
    child2_history.append(c2_exp)
    child3_history.append(c3_exp)
    total_child_expense_history.append(total_child_expense)
    cash_ratio_history.append(c_ratio)
    investment_ratio_history.append(i_ratio)
    stock_ratio_history.append(s_ratio)
    husband_gross_history.append(calculate_husband_gross_income(age_h))
    wife_gross_history.append(current_gross_w)
    pension_gross_history.append(current_pension_gross)
    household_gross_history.append(total_gross)
    husband_net_history.append(net_h)
    wife_net_history.append(net_w)
    pension_net_history.append(current_pension_net)
    household_net_history.append(pure_annual_income)

# ------------------------------------------
# グラフ描画（全英語化）
# ------------------------------------------
fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)
ax1.plot(age_history, total_wealth_history, label='Total Assets', color='#0F4C81', linewidth=2.5)
ax1.plot(age_history, cash_history, label='Cash (Cap: 10M)', color='#2E7D32', linestyle='--', linewidth=1.8)
ax1.plot(age_history, investment_history, label=f'Mutual Funds ({annual_return_rate}%)', color='#E67E22', linestyle='--', linewidth=1.8)
ax1.plot(age_history, stock_history, label='Stocks', color='#8E44AD', linestyle='--', linewidth=1.8)
ax1.axvline(retirement_age_h, color='red', linestyle=':', label='Retirement / Migration')
ax1.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax1.set_title('1. Lifetime Asset Balance Simulation', fontsize=12, fontweight='bold')
ax1.set_ylabel('Amount (10k JPY)', fontsize=10)
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.legend(loc='upper left')

ax2.plot(age_history, net_income_history, label='Net Income (incl. Dividends)', color='#2980B9', linewidth=1.8)
ax2.plot(age_history, total_expense_history, label='Total Expenses', color='#C0392B', linewidth=1.8)
ax2.plot(age_history, annual_balance_history, label='Annual Balance', color='#333333', linewidth=1.5, linestyle='-.')
ax2.fill_between(age_history, annual_balance_history, 0, where=[b >= 0 for b in annual_balance_history], color='#27AE60', alpha=0.3, interpolate=True)
ax2.fill_between(age_history, annual_balance_history, 0, where=[b < 0 for b in annual_balance_history], color='#E74C3C', alpha=0.3, interpolate=True)
ax2.axhline(0, color='gray', linestyle='--', alpha=0.7)
ax2.axvline(retirement_age_h, color='red', linestyle=':')
ax2.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax2.set_title('2. Annual Income vs Expenses & Balance', fontsize=12, fontweight='bold')
ax2.set_xlabel("Husband's Age", fontsize=10)
ax2.set_ylabel('Amount (10k JPY)', fontsize=10)
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.legend(loc='upper left')
plt.tight_layout()

fig_income, (ax_g, ax_n) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)
ax_g.plot(age_history, household_gross_history, label='Household Gross Income', color='#2C3E50', linewidth=2.5)
ax_g.plot(age_history, husband_gross_history, label="Husband's Gross Salary", color='#2980B9', linestyle='--', linewidth=1.8)
ax_g.plot(age_history, wife_gross_history, label="Wife's Gross Salary", color='#E67E22', linestyle='--', linewidth=1.8)
ax_g.plot(age_history, pension_gross_history, label='Gross Pension', color='#8E44AD', linestyle=':', linewidth=2.0)
ax_g.axvline(42, color='orange', linestyle=':', label='Husband Overtime Stop')
ax_g.axvline(retirement_age_h, color='red', linestyle=':')
ax_g.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax_g.set_title('3. Gross Income Trend', fontsize=12, fontweight='bold')
ax_g.set_ylabel('Gross Amount (10k JPY)', fontsize=10)
ax_g.grid(True, linestyle='--', alpha=0.5)
ax_g.legend(loc='upper right')

ax_n.plot(age_history, household_net_history, label='Household Net Income', color='#27AE60', linewidth=2.5)
ax_n.plot(age_history, husband_net_history, label="Husband's Net Salary", color='#3498DB', linestyle='--', linewidth=1.8)
ax_n.plot(age_history, wife_net_history, label="Wife's Net Salary", color='#F39C12', linestyle='--', linewidth=1.8)
ax_n.plot(ax_n.get_xticks(), [0]*len(ax_n.get_xticks()), alpha=0) # dummy
ax_n.plot(age_history, pension_net_history, label='Net Pension', color='#9B59B6', linestyle=':', linewidth=2.0)
ax_n.axvline(42, color='orange', linestyle=':')
ax_n.axvline(retirement_age_h, color='red', linestyle=':')
ax_n.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax_n.set_title('4. Net Income Trend', fontsize=12, fontweight='bold')
ax_n.set_xlabel("Husband's Age", fontsize=10)
ax_n.set_ylabel('Net Amount (10k JPY)', fontsize=10)
ax_n.grid(True, linestyle='--', alpha=0.5)
ax_n.legend(loc='upper right')
plt.tight_layout()

fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)
ax3.plot(age_history, child1_history, label='Child 1', color='#3498DB', linewidth=2)
if child_count >= 2: ax3.plot(age_history, child2_history, label='Child 2', color='#9B59B6', linewidth=2)
ax3.plot(age_history, total_child_expense_history, label='Total Child Expenses', color='#E74C3C', linewidth=2.5, linestyle=':')
ax3.axvline(retirement_age_h, color='red', linestyle=':')
ax3.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax3.set_title('5. Child Expenses Trend', fontsize=12, fontweight='bold')
ax3.set_ylabel('Amount (10k JPY)', fontsize=10)
ax3.grid(True, linestyle='--', alpha=0.5)
ax3.legend(loc='upper left')

ax4.stackplot(age_history, cash_ratio_history, investment_ratio_history, stock_ratio_history, 
              labels=['Cash Ratio (%)', 'Mutual Funds Ratio (%)', 'Stocks Ratio (%)'], 
              colors=['#A9DFBF', '#F5CBA7', '#D2B4DE'])
ax4.axvline(retirement_age_h, color='red', linestyle=':')
ax4.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax4.set_title('6. Asset Allocation Ratio', fontsize=12, fontweight='bold')
ax4.set_xlabel("Husband's Age", fontsize=10)
ax4.set_ylabel('Ratio (%)', fontsize=10)
ax4.set_ylim(0, 100)
ax4.grid(True, linestyle='--', alpha=0.5)
ax4.legend(loc='upper left')
plt.tight_layout()

# Streamlit出力
st.pyplot(fig1)
st.pyplot(fig_income)
st.pyplot(fig2)
