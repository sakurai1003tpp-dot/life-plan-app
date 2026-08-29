import streamlit as st
import matplotlib.pyplot as plt

# アプリのタイトルを表示
st.title("ライフプラン・シミュレーション")

import matplotlib.pyplot as plt

# グラフを高解像度（鮮明）に設定
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

try:
    import japanize_matplotlib
except ImportError:
    pass

# --- 基本設定 ---

# 【家族の年齢・働き方設定】
current_age_h = 29          # 夫の現在の年齢（歳）
current_age_w = 30          # 妻の現在の年齢（歳）
retirement_age_h = 65       # 夫の退職（リタイア）年齢（歳）
retirement_age_w = 55       # 妻の退職（リタイア）年齢（歳）
pension_start_age_h = 65    # 夫の年金受給開始年齢（歳）
pension_start_age_w = 70    # 妻の年金受給開始年齢（歳）※70歳繰り下げ受給

# 【収入の設定】
gross_income_h_start = 720  # 夫の現在の額面年収（万円）※残業代込み
gross_income_w = 400        # 妻の額面年収（万円）
income_change_rate_w = 1.25 # 妻の年収上昇率（年率・％）

# 【残業の設定（42歳未満は月45時間相当、42歳以降は支給なし）】
overtime_hours_per_month = 45
overtime_multiplier = 1.25

# 【妻の出産・育児に伴う収入減の設定】
child_care_reduction_years = 5     # 育休復職後、時短勤務等で年収が抑制される期間（年/人）
child_care_income_reduction_rate = 0.30  # 育休復職後の年収カット率

# 【現在の資産と運用設定（※投資信託のリターンを4.0%に変更）】
current_cash = 1000         # 現在の現預金残高（万円）
current_investment = 1300   # 現在の投資信託・運用資産残高（万円）
current_stock = 300         # 現在の株式（個別株等）の資産残高（万円）
annual_return_rate = 4.0    # 投資信託の想定運用利回り（年率・％ ※4.0%）
stock_return_rate = 1.5     # 株式の想定株価上昇率（キャピタルゲイン・年率・％）
stock_dividend_yield = 2.5  # 株式の年間配当利回り（インカムゲイン・％）
min_cash_reserve = 500      # 生活防衛資金の下限（万円）
max_cash_limit = 1000       # 現預金の上限（万円）
investment_stop_age_h = 60  # 60歳まで投資購入を継続、60歳で停止

# 【退職金の設定】
retirement_payout_h = 2000  # 夫の退職金支給額（万円）※65歳時
retirement_payout_w = 500   # 妻の退職金支給額（万円）※55歳時

# 【定年時の地方移住・住宅購入の設定】
regional_house_cost = 5000      # 夫65歳時の地方住宅購入費用（万円・現金決済）
migration_housing_expenses = 50 # 移住後の年間住居費（固定資産税・メンテナンス等・万円）

# 【現在の生活費・住居費・イベント費の設定】
living_expenses = 400           # 現在の基本生活費（年間・万円）
housing_expenses_base = 180     # 現在の住居費（年間・万円）
annual_travel_cost = 30         # 毎年計上する旅行費用（年間・万円）
general_medical_cost = 5        # 一般的な医療費（年間・万円）
annual_social_cost = 20         # 毎年計上する交際費（年間・万円）
expense_change_rate = 1.5       # 現役時代の生活費インフレ率（年率・％）
housing_increase_on_child = 60  # 子ども誕生後に増える住居費（年間・万円）

# 【臨時イベント費用の設定】
wedding_cost = 200              # 来年の結婚式費用（万円）

# 【リタイア（移住）後の生活費設定】
migration_living_expense_ratio = 0.80  
migration_medical_cost_multiplier = 4.0 

# 自動車関連費
car_maintenance_cost = 40      
car_purchase_price = 300       
car_replacement_cycle = 10     
annual_car_depreciation = car_purchase_price / car_replacement_cycle
total_annual_car_cost = car_maintenance_cost + annual_car_depreciation

# 【子育て・教育費の設定】
child_count = 1               
first_birth_age_h = 31        
birth_interval = 3            
maternity_leave_per_child = 3 

child_courses = {
    1: 'PUBLIC_UNIV_RIKEI',         
    2: 'PUBLIC_UNIV_PRIVATE', 
    3: 'ALL_PUBLIC'            
}

course_labels = {
    'PUBLIC_UNIV_RIKEI': '国公立・理系',
    'PUBLIC_UNIV_PRIVATE': '私立文系・理系',
    'ALL_PUBLIC': '全公立'
}

# --- 出産・育休・復職減収期間の計算 ---
birth_ages_h = []
birth_ages_w = []
if child_count > 0:
    for n in range(child_count):
        b_h = first_birth_age_h + (n * birth_interval)
        birth_ages_h.append(b_h)
        birth_ages_w.append(current_age_w + (b_h - current_age_h))

maternity_leave_years_w = []
for idx, b_w in enumerate(birth_ages_w):
    for y in range(maternity_leave_per_child):
        maternity_leave_years_w.append(b_w + y)
maternity_leave_years_w = sorted(list(set(maternity_leave_years_w)))

reduced_income_years_w = []
for b_w in birth_ages_w:
    start_y = b_w + maternity_leave_per_child
    for y in range(child_care_reduction_years):
        reduced_income_years_w.append(start_y + y)
reduced_income_years_w = sorted(list(set(reduced_income_years_w)))

# --- 収入・年金計算関数（滑らかな昇給カーブ設計） ---
def calculate_husband_base_gross_income(age):
    if age < 29 or age >= retirement_age_h: return 0
    elif age <= 41: 
        base_at_29 = 532.72
        base_at_41 = 887.86  
        return base_at_29 + (age - 29) * ((base_at_41 - base_at_29) / 12)
    elif age <= 59: 
        base_at_42 = 1000.0
        peak_base_59 = 1400.0
        return base_at_42 + (age - 42) * ((peak_base_59 - base_at_42) / 17)
    elif age <= 64: return 1400.0 * 0.70
    return 0

def calculate_husband_gross_income(age):
    base = calculate_husband_base_gross_income(age)
    if base <= 0:
        return 0
    if age < 42:
        annual_standard_hours = 1920
        hourly_rate = (base * 10000) / annual_standard_hours
        annual_overtime_pay = hourly_rate * overtime_multiplier * overtime_hours_per_month * 12
        return base + (annual_overtime_pay / 10000)
    else:
        return base  

def estimate_pension_h():
    work_years_h = 65 - 22 
    average_monthly_gross_h = 100
    kousei_pension_h = average_monthly_gross_h * 0.005481 * 12 * work_years_h
    kiso_pension_h = 81.3
    return (kiso_pension_h + kousei_pension_h) * 0.87

def estimate_pension_w():
    actual_leave_years = len(maternity_leave_years_w)
    work_years_w = max(0, (retirement_age_w - 22) - actual_leave_years)
    average_monthly_gross_w = gross_income_w / 12
    kousei_pension_w = average_monthly_gross_w * 0.005481 * 12 * work_years_w
    kiso_pension_w = 81.3
    base_pension = kiso_pension_w + kousei_pension_w
    deferral_rate = 1.42 
    return base_pension * deferral_rate * 0.87

calculated_pension_h = estimate_pension_h()
calculated_pension_w = estimate_pension_w()

def calculate_net_income(gross):
    if gross <= 0: return 0
    elif gross <= 300: return gross * 0.85
    elif gross <= 600: return gross * 0.80
    elif gross <= 1000: return gross * 0.75
    else: return gross * 0.70

# --- シミュレーション履歴用リスト ---
age_history = []
total_wealth_history = []
cash_history = []
investment_history = []
stock_history = []
net_income_history = []
total_expense_history = []
annual_balance_history = [] 

child1_history = []
child2_history = []
child3_history = []
total_child_expense_history = []

cash_ratio_history = []
investment_ratio_history = []
stock_ratio_history = []

husband_gross_history = []
wife_gross_history = []
pension_gross_history = []    # 【修正追加】年金(額面)リスト
household_gross_history = []

husband_net_history = []
wife_net_history = []
pension_net_history = []      # 【修正追加】年金(手取り)リスト
household_net_history = []

# --- シミュレーション・ループ ---
for i in range(100 - current_age_h + 1):
    age_h = current_age_h + i
    age_w = current_age_w + i
    
    annual_dividend = 0
    if i > 0:
        current_investment = current_investment * (1 + annual_return_rate / 100)
        current_stock = current_stock * (1 + stock_return_rate / 100)
        annual_dividend = (current_stock * (stock_dividend_yield / 100)) * 0.79685 
    
    if age_h < retirement_age_h:
        current_gross_h = calculate_husband_gross_income(age_h)
        net_h = calculate_net_income(current_gross_h)
    else:
        current_gross_h = 0
        net_h = 0

    if age_w < retirement_age_w:
        if age_w in maternity_leave_years_w:
            current_gross_w = 0
        else:
            base_w = gross_income_w * ((1 + income_change_rate_w / 100) ** i)
            if age_w in reduced_income_years_w:
                base_w = base_w * (1 - child_care_income_reduction_rate)
            current_gross_w = base_w
        net_w = calculate_net_income(current_gross_w)
    else:
        current_gross_w = 0
        net_w = 0

    extra_retirement_cash = 0
    if age_w == retirement_age_w:
        extra_retirement_cash += retirement_payout_w
    if age_h == retirement_age_h:
        extra_retirement_cash += retirement_payout_h

    # 【修正】年金（額面・手取り）の計算を分離してリストへ保存できるように変更
    current_pension_gross = 0
    if age_h >= pension_start_age_h:
        current_pension_gross += calculated_pension_h
    if age_w >= pension_start_age_w:
        current_pension_gross += calculated_pension_w
        
    current_pension_net = current_pension_gross * 0.85 if current_pension_gross > 0 else 0

    total_gross = current_gross_h + current_gross_w + current_pension_gross
    pure_annual_income = net_h + net_w + current_pension_net + annual_dividend
        
    is_migrated = (age_h >= retirement_age_h and age_w >= retirement_age_h)
    
    if not is_migrated:
        rate_factor_exp = (1 + expense_change_rate / 100) ** i
        current_housing = housing_expenses_base
        if child_count > 0 and age_h >= first_birth_age_h:
            current_housing += housing_increase_on_child
        base_annual_expense = living_expenses + current_housing + annual_travel_cost + general_medical_cost + annual_social_cost
        annual_expense = base_annual_expense * rate_factor_exp
    else:
        retirement_start_i = retirement_age_h - current_age_h
        rate_factor_exp_at_retirement = (1 + expense_change_rate / 100) ** retirement_start_i
        
        base_living_at_retirement = (living_expenses * migration_living_expense_ratio) + migration_housing_expenses + total_annual_car_cost + annual_travel_cost + annual_social_cost
        base_expense_fixed = base_living_at_retirement * rate_factor_exp_at_retirement
        
        aging_reduction = 0.90 if age_h >= 75 else 1.0
        current_medical = general_medical_cost * migration_medical_cost_multiplier
        annual_expense = (base_expense_fixed * aging_reduction) + current_medical
    
    extra_one_time_expense = 0
    if i == 1:
        extra_one_time_expense += wedding_cost
    
    c1_exp, c2_exp, c3_exp = 0, 0, 0
    if child_count >= 1:
        c1_age = age_h - first_birth_age_h
        if 0 <= c1_age <= 22:
            if c1_age <= 6:   c1_exp = 60
            elif c1_age <= 12:  c1_exp = 90
            elif c1_age <= 15:  c1_exp = 110
            elif c1_age <= 18:  c1_exp = 100
            elif c1_age <= 22:  c1_exp = 260
    if child_count >= 2:
        c2_age = age_h - (first_birth_age_h + birth_interval)
        if 0 <= c2_age <= 22:
            if c2_age <= 6:   c2_exp = 60
            elif c2_age <= 12:  c2_exp = 90
            elif c2_age <= 15:  c2_exp = 110
            elif c2_age <= 18:  c2_exp = 100
            elif c2_age <= 22:  c2_exp = 220
    if child_count >= 3:
        c3_age = age_h - (first_birth_age_h + birth_interval * 2)
        if 0 <= c3_age <= 22:
            if c3_age <= 6:   c3_exp = 60
            elif c3_age <= 12:  c3_exp = 90
            elif c3_age <= 15:  c3_exp = 110
            elif c3_age <= 18:  c3_exp = 100
            elif c3_age <= 22:  c3_exp = 180

    total_child_expense = c1_exp + c2_exp + c3_exp
    pure_total_expense = annual_expense + total_child_expense + extra_one_time_expense
    pure_annual_balance = pure_annual_income - pure_total_expense
    
    cash_delta = pure_annual_balance + extra_retirement_cash
    current_cash += cash_delta
    
    # 【安全対策＆売却順序の厳密化：定年移住時の住宅購入】
    if age_h == retirement_age_h:
        total_available_liquidity = current_cash + current_stock + current_investment
        if total_available_liquidity < regional_house_cost + min_cash_reserve:
            print(f"【警告】夫 {age_h}歳時点：地方住宅購入（{regional_house_cost}万円）と生活防衛資金確保のためにお金が不足しています（資金ショート・破綻リスク）！")
        
        sale_from_stock = current_stock
        current_stock = 0
        current_cash += sale_from_stock
        
        needed_for_house = regional_house_cost - current_cash
        if needed_for_house > 0:
            sale_from_inv = min(needed_for_house, current_investment)
            current_investment -= sale_from_inv
            current_cash += sale_from_inv
            
        current_cash -= regional_house_cost

    # 【通常時の資金不足時：株式を優先して売却するロジック】
    effective_max_cash = max_cash_limit
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
    elif age_h < investment_stop_age_h and current_cash > effective_max_cash:
        excess = current_cash - effective_max_cash
        current_cash = effective_max_cash
        current_investment += excess
            
    total_wealth = current_cash + current_investment + current_stock
    if total_wealth > 0:
        c_ratio = (current_cash / total_wealth) * 100
        i_ratio = (current_investment / total_wealth) * 100
        s_ratio = (current_stock / total_wealth) * 100
    else:
        c_ratio, i_ratio, s_ratio = 100, 0, 0
        
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

    husband_gross_history.append(current_gross_h)
    wife_gross_history.append(current_gross_w)
    
    # 【修正追加】年金(額面)と世帯合計を履歴に追加
    pension_gross_history.append(current_pension_gross)
    household_gross_history.append(total_gross)

    husband_net_history.append(net_h)
    wife_net_history.append(net_w)
    
    # 【修正追加】年金(手取り)と世帯合計を履歴に追加
    pension_net_history.append(current_pension_net)
    household_net_history.append(pure_annual_income)

# ------------------------------------------
# ウィンドウ1：資産と収支の2段グラフ
# ------------------------------------------
fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

ax1.plot(age_history, total_wealth_history, label='総資産額', color='#0F4C81', linewidth=2.5)
ax1.plot(age_history, cash_history, label='現預金（上限1000万円で固定）', color='#2E7D32', linestyle='--', linewidth=1.8)
ax1.plot(age_history, investment_history, label='投資信託 (利回り4.0%)', color='#E67E22', linestyle='--', linewidth=1.8)
ax1.plot(age_history, stock_history, label='株式 [株価1.5% + 配当2.0%・先に売却]', color='#8E44AD', linestyle='--', linewidth=1.8)

ax1.axvline(retirement_age_h, color='red', linestyle=':', linewidth=1.5, label='夫定年・移住 (65歳)')
ax1.axvspan(retirement_age_h, 100, color='gray', alpha=0.15, label='リタイア期')
ax1.set_title('1. 資産残高の生涯シミュレーション（投信4%・株式優先売却対応版）', fontsize=12, fontweight='bold')
ax1.set_ylabel('金額 (万円)', fontsize=10)
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.legend(loc='upper left', frameon=True)

ax2.plot(age_history, net_income_history, label='世帯手取り収入（配当金込）', color='#2980B9', linewidth=1.8)
ax2.plot(age_history, total_expense_history, label='年間総支出', color='#C0392B', linewidth=1.8)
ax2.plot(age_history, annual_balance_history, label='年間収支（黒字/赤字ライン）', color='#333333', linewidth=1.5, linestyle='-.')

ax2.fill_between(age_history, annual_balance_history, 0, where=[b >= 0 for b in annual_balance_history], color='#27AE60', alpha=0.3, interpolate=True, label='黒字期間')
ax2.fill_between(age_history, annual_balance_history, 0, where=[b < 0 for b in annual_balance_history], color='#E74C3C', alpha=0.3, interpolate=True, label='赤字期間')

ax2.axhline(0, color='gray', linestyle='--', alpha=0.7)
ax2.axvline(retirement_age_h, color='red', linestyle=':', linewidth=1.5, label='夫定年・移住 (65歳)')
ax2.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax2.set_title('2. 年間手取り収入・年間支出・年間収支の推移', fontsize=12, fontweight='bold')
ax2.set_xlabel('夫の年齢 (歳)', fontsize=10)
ax2.set_ylabel('金額 (万円)', fontsize=10)
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.legend(loc='upper left', frameon=True)
plt.tight_layout()

# ------------------------------------------
# ウィンドウ2：年収の推移（額面・手取りに年金を追加）のグラフ
# ------------------------------------------
fig_income, (ax_g, ax_n) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

ax_g.plot(age_history, household_gross_history, label='世帯合計 額面収入（給与＋年金）', color='#2C3E50', linewidth=2.5)
ax_g.plot(age_history, husband_gross_history, label='夫 額面給与収入', color='#2980B9', linestyle='--', linewidth=1.8)
ax_g.plot(age_history, wife_gross_history, label='妻 額面給与収入', color='#E67E22', linestyle='--', linewidth=1.8)
ax_g.plot(age_history, pension_gross_history, label='公立年金受給額（額面合計）', color='#8E44AD', linestyle=':', linewidth=2.0)

ax_g.axvline(42, color='orange', linestyle=':', linewidth=1.5, label='夫 残業停止 (42歳)')
ax_g.axvline(55 + (current_age_h - current_age_w), color='purple', linestyle=':', linewidth=1.5, label='妻 定年 (55歳)')
ax_g.axvline(retirement_age_h, color='red', linestyle=':', linewidth=1.5, label='夫 定年 (65歳)')
ax_g.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax_g.set_title('3. 額面収入の生涯推移（夫・妻・年金・世帯合計）', fontsize=12, fontweight='bold')
ax_g.set_ylabel('額面金額 (万円)', fontsize=10)
ax_g.grid(True, linestyle='--', alpha=0.5)
ax_g.legend(loc='upper right', frameon=True)

ax_n.plot(age_history, household_net_history, label='世帯合計 手取り収入（給与＋年金＋配当）', color='#27AE60', linewidth=2.5)
ax_n.plot(age_history, husband_net_history, label='夫 手取り給与', color='#3498DB', linestyle='--', linewidth=1.8)
ax_n.plot(age_history, wife_net_history, label='妻 手取り給与', color='#F39C12', linestyle='--', linewidth=1.8)
ax_n.plot(age_history, pension_net_history, label='公的年金（手取り換算）', color='#9B59B6', linestyle=':', linewidth=2.0)

ax_n.axvline(42, color='orange', linestyle=':', linewidth=1.5, label='夫 残業停止 (42歳)')
ax_n.axvline(55 + (current_age_h - current_age_w), color='purple', linestyle=':', linewidth=1.5, label='妻 定年 (55歳)')
ax_n.axvline(retirement_age_h, color='red', linestyle=':', linewidth=1.5, label='夫 定年 (65歳)')
ax_n.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax_n.set_title('4. 手取り収入の生涯推移（夫・妻・年金・世帯合計）', fontsize=12, fontweight='bold')
ax_n.set_xlabel('夫の年齢 (歳)', fontsize=10)
ax_n.set_ylabel('手取り金額 (万円)', fontsize=10)
ax_n.grid(True, linestyle='--', alpha=0.5)
ax_n.legend(loc='upper right', frameon=True)
plt.tight_layout()

# ------------------------------------------
# ウィンドウ3：子ども費と資産構成の2段グラフ
# ------------------------------------------
fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

ax3.plot(age_history, child1_history, label=f'第1子 ({course_labels[child_courses[1]]})', color='#3498DB', linewidth=2)
if child_count >= 2:
    ax3.plot(age_history, child2_history, label=f'第2子 ({course_labels[child_courses[2]]})', color='#9B59B6', linewidth=2)
if child_count >= 3:
    ax3.plot(age_history, child3_history, label=f'第3子 ({course_labels[child_courses[3]]})', color='#2ECC71', linewidth=2)
ax3.plot(age_history, total_child_expense_history, label='総子ども費用', color='#E74C3C', linewidth=2.5, linestyle=':')
ax3.axvline(retirement_age_h, color='red', linestyle=':', linewidth=1.5)
ax3.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax3.set_title('5. 子ども費用の推移', fontsize=12, fontweight='bold')
ax3.set_ylabel('金額 (万円)', fontsize=10)
ax3.grid(True, linestyle='--', alpha=0.5)
ax3.legend(loc='upper left', frameon=True)

# 資産構成比率（現金・投資信託・株式の積み上げ）
ax4.stackplot(age_history, cash_ratio_history, investment_ratio_history, stock_ratio_history, 
              labels=['現金比率(%)', '投資信託比率(%)', '株式比率(%)'], 
              colors=['#A9DFBF', '#F5CBA7', '#D2B4DE'])
ax4.axvline(retirement_age_h, color='red', linestyle=':', linewidth=1.5)
ax4.axvspan(retirement_age_h, 100, color='gray', alpha=0.15)
ax4.set_title('6. 資産構成比率の推移（現金・投資信託・株式）', fontsize=12, fontweight='bold')
ax4.set_xlabel('夫の年齢 (歳)', fontsize=10)
ax4.set_ylabel('比率 (%)', fontsize=10)
ax4.set_ylim(0, 100)
ax4.grid(True, linestyle='--', alpha=0.5)
ax4.legend(loc='upper left', frameon=True)
plt.tight_layout()

plt.show()

st.pyplot(fig1)
st.pyplot(fig_income)
st.pyplot(fig2)