import os
import platform
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ------------------------------------------
# 日本語フォントの設定（文字化け防止）
# ------------------------------------------
system = platform.system()
if system == 'Darwin':
    font_family = 'Hiragino Sans'
elif system == 'Windows':
    font_family = 'Meiryo'
else:
    # Linux環境やStreamlit Cloudでは利用可能なゴシック体を探索・設定
    font_list = [f.name for f in fm.fontManager.ttflist]
    if 'IPAexGothic' in font_list:
        font_family = 'IPAexGothic'
    elif 'IPAGothic' in font_list:
        font_family = 'IPAGothic'
    elif 'Noto Sans CJK JP' in font_list:
        font_family = 'Noto Sans CJK JP'
    elif 'TakaoGothic' in font_list:
        font_family = 'TakaoGothic'
    else:
        font_family = 'DejaVu Sans'

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [font_family, 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# グラフを高解像度・ポップで可愛いデザインにカスタマイズ
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

# パステル＆ポップなカラーパレット
COLOR_PRIMARY = '#FF6B6B'   # コーラルピンク
COLOR_SECONDARY = '#4D96FF'   # スカイブルー
COLOR_ACCENT = '#FFD93D'   # サンイエロー
COLOR_GREEN = '#6BCB77'   # ミントグリーン
COLOR_PURPLE = '#9D4EDD'   # ラベンダー
COLOR_DARK = '#2B2D42'   # チャコールグレー

# 画面設定とカスタムCSS
st.set_page_config(page_title='ライフプランシミュレーション', layout='wide')

st.markdown(
    """
<style>
    .main {
        background-color: #FFFDF9;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 2px solid #FFE3E3;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.08);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #8D99AE;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.5rem;
        color: #2B2D42;
        font-weight: 700;
    }
</style>
""",
    unsafe_allow_html=True,
)

# メインタイトル
st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <h1 style="font-size: 1.4rem; font-weight: 600; color: #2B2D42; letter-spacing: -0.025em; margin-bottom: 4px;">
            🌸 ほっこりライフプランシミュレーション
        </h1>
        <p style="font-size: 0.85rem; color: #8D99AE; font-weight: 400;">
            将来の資産形成・キャッシュフロー・教育費をやさしく可視化します
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown('---')

# ------------------------------------------
# サイドバー設定パネル
# ------------------------------------------
st.sidebar.header('👨‍👩‍👧‍👦 家族・働き方設定')
current_age_h = st.sidebar.slider('夫の現在の年齢（歳）', 20, 60, 29)
current_age_w = st.sidebar.slider('妻の現在の年齢（歳）', 20, 60, 30)
retirement_age_h = st.sidebar.slider('夫の退職年齢（歳）', 50, 75, 65)
retirement_age_w = st.sidebar.slider('妻の退職年齢（歳）', 50, 75, 55)
pension_start_age_h = st.sidebar.slider('夫の年金受給開始年齢（歳）', 60, 75, 65)
pension_start_age_w = st.sidebar.slider('妻の年金受給開始年齢（歳）', 60, 75, 70)

st.sidebar.header('👶 子ども・育休設定')
child_count = st.sidebar.selectbox('子供の人数', [0, 1, 2, 3], index=1)
first_birth_age_h = st.sidebar.slider('第1子誕生時の夫の年齢', 22, 50, 31)
birth_interval = st.sidebar.slider('きょうだいの年齢差（年）', 1, 5, 3)

maternity_leave_per_child = st.sidebar.selectbox(
    '子1人あたりの産休・育休期間（年）', [1, 2, 3], index=1
)

child_courses = {}
course_labels = {
    'ALL_PUBLIC': '大学まで全公立',
    'PUBLIC_UNIV_RIKEI': '高校まで公立・大学は私立理系',
    'PUBLIC_UNIV_BUNKEI': '高校まで公立・大学は私立文系',
}
if child_count >= 1:
    c1_choice = st.sidebar.selectbox(
        '第1子の進路',
        list(course_labels.keys()),
        format_func=lambda x: course_labels[x],
        index=0,
    )
    child_courses[1] = c1_choice
if child_count >= 2:
    c2_choice = st.sidebar.selectbox(
        '第2子の進路',
        list(course_labels.keys()),
        format_func=lambda x: course_labels[x],
        index=1,
    )
    child_courses[2] = c2_choice
if child_count >= 3:
    c3_choice = st.sidebar.selectbox(
        '第3子の進路',
        list(course_labels.keys()),
        format_func=lambda x: course_labels[x],
        index=2,
    )
    child_courses[3] = c3_choice

st.sidebar.header('💰 収入・働き方設定')
gross_income_h_start = st.sidebar.number_input(
    '夫の現在年収 (万円)', 0, 5000, 720, step=10
)
gross_income_w = st.sidebar.number_input(
    '妻の現在年収 (万円)', 0, 5000, 400, step=10
)
income_change_rate_w = st.sidebar.slider(
    '妻の年収上昇率 (%/年)', 0.0, 5.0, 1.25, step=0.05
)
child_care_reduction_years = st.sidebar.selectbox(
    '育児短時間勤務の期間（年）', [1, 2, 3, 4, 5, 6, 7, 8], index=4
)

st.sidebar.header('📈 資産・運用・経済設定')
current_cash = st.sidebar.number_input(
    '現在の現預金 (万円)', 0, 50000, 1000, step=50
)
current_investment = st.sidebar.number_input(
    '現在の投資信託 (万円)', 0, 50000, 1300, step=50
)
current_stock = st.sidebar.number_input(
    '現在の株式 (万円)', 0, 50000, 300, step=50
)
annual_return_rate = st.sidebar.slider(
    '投資信託の想定利回り (%)', 0.0, 15.0, 4.0, step=0.1
)
expense_change_rate = st.sidebar.slider(
    'インフレ率（年間生活費の上昇率 %）', 0.0, 5.0, 1.5, step=0.1
)
max_cash_limit = st.sidebar.number_input(
    '現預金の保有上限 (万円)', 100, 5000, 1000, step=50
)

st.sidebar.header('🏠 住宅・生活費・年間支出設定')
living_expenses_monthly = st.sidebar.number_input(
    '基本生活費 (毎月・万円)', 0, 100, 33, step=1
)
housing_expenses_monthly = st.sidebar.number_input(
    '住居費 (毎月・万円)', 0, 50, 15, step=1
)
annual_travel_cost = st.sidebar.number_input(
    '年間旅行費 (万円)', 0, 200, 30, step=5
)
general_medical_cost = st.sidebar.number_input(
    '年間医療費 (万円)', 0, 50, 5, step=1
)
annual_social_cost = st.sidebar.number_input(
    '年間交際費 (万円)', 0, 100, 20, step=5
)
regional_house_cost = st.sidebar.number_input(
    '定年時 住宅購入費用 (万円)', 0, 20000, 5000, step=100
)

living_expenses = living_expenses_monthly * 12
housing_expenses_base = housing_expenses_monthly * 12

# ------------------------------------------
# 基本設定と計算ロジック
# ------------------------------------------
overtime_hours_per_month = 45
overtime_multiplier = 1.25
child_care_income_reduction_rate = 0.30
stock_return_rate = 1.5
stock_dividend_yield = 2.5
min_cash_reserve = 500
investment_stop_age_h = 60
retirement_payout_h = 2000
retirement_payout_w = 500
migration_housing_expenses = 50
housing_increase_on_child = 60
wedding_cost = 200
migration_living_expense_ratio = 0.80
migration_medical_cost_multiplier = 4.0

car_maintenance_cost = 40
car_purchase_price = 300
car_replacement_cycle = 10
annual_car_depreciation = car_purchase_price / car_replacement_cycle
total_annual_car_cost = car_maintenance_cost + annual_car_depreciation

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


def calculate_husband_base_gross_income(age):
    if age < 29 or age >= retirement_age_h:
        return 0
    elif age <= 41:
        return 532.72 + (age - 29) * ((1100.0 - 532.72) / 12)
    else:
        peak_target_income = 1400.0
        start_income_at_42 = 1100.0
        years_span = max(1, retirement_age_h - 42)
        current_offset = age - 42
        return start_income_at_42 + current_offset * (
            (peak_target_income - start_income_at_42) / years_span
        )


def calculate_husband_gross_income(age):
    base = calculate_husband_base_gross_income(age)
    if base <= 0:
        return 0
    if age < 42:
        hourly_rate = (base * 10000) / 1920
        annual_overtime_pay = (
            hourly_rate * overtime_multiplier * overtime_hours_per_month * 12
        )
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
    if gross <= 0:
        return 0
    elif gross <= 300:
        return gross * 0.85
    elif gross <= 600:
        return gross * 0.80
    elif gross <= 1000:
        return gross * 0.75
    else:
        return gross * 0.70


def get_child_yearly_expense(c_age, course_type):
    if not (0 <= c_age <= 22):
        return 0
    if c_age <= 2:
        return 30
    elif c_age <= 6:
        return 35
    elif c_age <= 12:
        return 34
    elif c_age <= 15:
        return 54
    elif c_age <= 18:
        return 51
    else:
        if course_type == 'ALL_PUBLIC':
            return 120
        elif course_type == 'PUBLIC_UNIV_RIKEI':
            return 205
        elif course_type == 'PUBLIC_UNIV_BUNKEI':
            return 172
        else:
            return 120


def get_child_living_expense_addition(c_age):
    if not (0 <= c_age <= 22):
        return 0
    if c_age <= 3:
        return 15
    elif c_age <= 12:
        return 30
    elif c_age <= 18:
        return 55
    else:
        return 40


# ------------------------------------------
# シミュレーション実行
# ------------------------------------------
age_history, total_wealth_history, cash_history = [], [], []
investment_history, stock_history = [], []
net_income_history, total_expense_history, annual_balance_history = [], [], []
child1_history, child2_history, child3_history, total_child_expense_history = (
    [],
    [],
    [],
    [],
)
cash_ratio_history, investment_ratio_history, stock_ratio_history = [], [], []
husband_gross_history, wife_gross_history = [], []
pension_gross_history, household_gross_history = [], []
husband_net_history, wife_net_history = [], []
pension_net_history, household_net_history = [], []

init_cash_val = current_cash
init_inv_val = current_investment
init_stk_val = current_stock

sim_cash = current_cash
sim_investment = current_investment
sim_stock = current_stock

for i in range(100 - current_age_h + 1):
    age_h = current_age_h + i
    age_w = current_age_w + i

    annual_dividend = 0
    if i > 0:
        sim_investment = sim_investment * (1 + annual_return_rate / 100)
        sim_stock = sim_stock * (1 + stock_return_rate / 100)
        annual_dividend = (sim_stock * (stock_dividend_yield / 100)) * 0.79685

    net_h = (
        calculate_net_income(calculate_husband_gross_income(age_h))
        if age_h < retirement_age_h
        else 0
    )

    if age_w < retirement_age_w:
        if age_w in maternity_leave_years_w:
            current_gross_w = 0
        else:
            base_w = gross_income_w * ((1 + income_change_rate_w / 100) ** i)
            if age_w in reduced_income_years_w:
                base_w *= 1 - child_care_income_reduction_rate
            current_gross_w = base_w
        net_w = calculate_net_income(current_gross_w)
    else:
        current_gross_w = 0
        net_w = 0

    extra_retirement_cash = (
        retirement_payout_w if age_w == retirement_age_w else 0
    ) + (retirement_payout_h if age_h == retirement_age_h else 0)
    current_pension_gross = (
        calculated_pension_h if age_h >= pension_start_age_h else 0
    ) + (calculated_pension_w if age_w >= pension_start_age_w else 0)
    current_pension_net = (
        current_pension_gross * 0.85 if current_pension_gross > 0 else 0
    )

    total_gross = (
        calculate_husband_gross_income(age_h)
        + current_gross_w
        + current_pension_gross
    )
    pure_annual_income = net_h + net_w + current_pension_net + annual_dividend

    is_migrated = age_h >= retirement_age_h and age_w >= retirement_age_h

    if not is_migrated:
        rate_factor_exp = (1 + expense_change_rate / 100) ** i
        current_housing = housing_expenses_base + (
            housing_increase_on_child
            if (child_count > 0 and age_h >= first_birth_age_h)
            else 0
        )

        total_child_living_addition = 0
        if child_count >= 1:
            c1_age = age_h - first_birth_age_h
            total_child_living_addition += get_child_living_expense_addition(c1_age)
        if child_count >= 2:
            c2_age = age_h - (first_birth_age_h + birth_interval)
            total_child_living_addition += get_child_living_expense_addition(c2_age)
        if child_count >= 3:
            c3_age = age_h - (first_birth_age_h + birth_interval * 2)
            total_child_living_addition += get_child_living_expense_addition(c3_age)

        base_living_with_children = living_expenses + total_child_living_addition
        annual_expense = (
            base_living_with_children
            + current_housing
            + annual_travel_cost
            + general_medical_cost
            + annual_social_cost
        ) * rate_factor_exp
    else:
        retirement_start_i = retirement_age_h - current_age_h
        base_expense_fixed = (
            (living_expenses * migration_living_expense_ratio)
            + migration_housing_expenses
            + total_annual_car_cost
            + annual_travel_cost
            + annual_social_cost
        ) * ((1 + expense_change_rate / 100) ** retirement_start_i)
        annual_expense = (base_expense_fixed * (0.90 if age_h >= 75 else 1.0)) + (
            general_medical_cost * migration_medical_cost_multiplier
        )

    extra_one_time_expense = wedding_cost if i == 1 else 0

    c1_exp, c2_exp, c3_exp = 0, 0, 0
    if child_count >= 1:
        c1_age = age_h - first_birth_age_h
        c1_exp = get_child_yearly_expense(c1_age, child_courses[1])
    if child_count >= 2:
        c2_age = age_h - (first_birth_age_h + birth_interval)
        c2_exp = get_child_yearly_expense(c2_age, child_courses[2])
    if child_count >= 3:
        c3_age = age_h - (first_birth_age_h + birth_interval * 2)
        c3_exp = get_child_yearly_expense(c3_age, child_courses[3])

    total_child_expense = c1_exp + c2_exp + c3_exp
    pure_total_expense = (
        annual_expense + total_child_expense + extra_one_time_expense
    )
    pure_annual_balance = pure_annual_income - pure_total_expense

    sim_cash += pure_annual_balance + extra_retirement_cash

    if age_h == retirement_age_h:
        sim_cash += sim_stock
        sim_stock = 0
        needed = regional_house_cost - sim_cash
        if needed > 0:
            sale = min(needed, sim_investment)
            sim_investment -= sale
            sim_cash += sale
        sim_cash -= regional_house_cost

    if sim_cash < min_cash_reserve:
        shortfall = min_cash_reserve - sim_cash
        if sim_stock >= shortfall:
            sim_stock -= shortfall
            sim_cash += shortfall
        else:
            shortfall -= sim_stock
            sim_cash += sim_stock
            sim_stock = 0
            if sim_investment >= shortfall:
                sim_investment -= shortfall
                sim_cash += shortfall
            else:
                sim_cash += sim_investment
                sim_investment = 0
    elif age_h < investment_stop_age_h and sim_cash > max_cash_limit:
        excess = sim_cash - max_cash_limit
        sim_cash = max_cash_limit
        sim_investment += excess

    total_wealth = sim_cash + sim_investment + sim_stock
    c_ratio = (sim_cash / total_wealth) * 100 if total_wealth > 0 else 100
    i_ratio = (sim_investment / total_wealth) * 100 if total_wealth > 0 else 0
    s_ratio = (sim_stock / total_wealth) * 100 if total_wealth > 0 else 0

    age_history.append(age_h)
    total_wealth_history.append(total_wealth)
    cash_history.append(sim_cash)
    investment_history.append(sim_investment)
    stock_history.append(sim_stock)
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
# KPIメトリクスカードの表示
# ------------------------------------------
initial_total_wealth = init_cash_val + init_inv_val + init_stk_val
peak_wealth = max(total_wealth_history)

target_age_80 = current_age_h + (80 - current_age_h)
if target_age_80 in age_history:
    idx_80 = age_history.index(target_age_80)
    wealth_at_80 = total_wealth_history[idx_80]
else:
    wealth_at_80 = total_wealth_history[-1]

if child_count == 0:
    child_info_str = '子供 0人'
else:
    courses_summary = []
    for n in range(1, child_count + 1):
        if n in child_courses:
            courses_summary.append(f'第{n}: {course_labels[child_courses[n]]}')
    child_info_str = f'子供 {child_count}人 (' + ', '.join(courses_summary) + ')'

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        f"""
            <div class="metric-card">
                <div class="metric-title">現在の総資産</div>
                <div class="metric-value">{initial_total_wealth:,.0f} 万円</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    peak_age = age_history[total_wealth_history.index(peak_wealth)]
    st.markdown(
        f"""
            <div class="metric-card">
                <div class="metric-title">資産ピーク時（年齢: {peak_age}歳）</div>
                <div class="metric-value">{peak_wealth:,.0f} 万円</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
            <div class="metric-card">
                <div class="metric-title">80歳時点の残高</div>
                <div class="metric-value">{wealth_at_80:,.0f} 万円</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        f"""
            <div class="metric-card">
                <div class="metric-title">家族・進路設定</div>
                <div class="metric-value" style="font-size: 0.9rem; padding-top: 5px;">{child_info_str}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<br>', unsafe_allow_html=True)

# ------------------------------------------
# タブによる情報の整理
# ------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ['📈 資産・収支シミュレーション', '💰 収入・詳細推移', '👶 子育て費用', '📊 ポートフォリオ']
)

with tab1:
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 11), sharex=True)
    fig1.patch.set_facecolor('#FFFDF9')
    ax1.set_facecolor('#FFFFFF')
    ax2.set_facecolor('#FFFFFF')

    ax1.plot(
        age_history,
        total_wealth_history,
        label='総資産額',
        color=COLOR_PRIMARY,
        linewidth=3.0,
        solid_capstyle='round',
    )
    ax1.plot(
        age_history,
        cash_history,
        label=f'現預金（上限{max_cash_limit}万円）',
        color=COLOR_GREEN,
        linestyle='--',
        linewidth=2.0,
    )
    ax1.plot(
        age_history,
        investment_history,
        label=f'投資信託 (利回り{annual_return_rate}%)',
        color=COLOR_SECONDARY,
        linestyle='--',
        linewidth=2.0,
    )
    ax1.plot(
        age_history,
        stock_history,
        label='株式',
        color=COLOR_PURPLE,
        linestyle='--',
        linewidth=2.0,
    )
    ax1.axvline(
        retirement_age_h,
        color='#FF869E',
        linestyle=':',
        linewidth=2,
        label='夫定年・移住',
    )
    ax1.axvspan(retirement_age_h, 100, color='#F1F2F6', alpha=0.5)
    ax1.set_title(
        '1. 資産残高の生涯シミュレーション',
        fontsize=13,
        fontweight='bold',
        color=COLOR_DARK,
        pad=12,
    )
    ax1.set_ylabel('金額 (万円)', fontsize=11, color=COLOR_DARK)
    ax1.grid(True, linestyle=':', alpha=0.6, color='#E4E5E9')
    ax1.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='none')

    ax2.plot(
        age_history,
        net_income_history,
        label='世帯手取り収入（配当込）',
        color=COLOR_SECONDARY,
        linewidth=2.2,
    )
    ax2.plot(
        age_history,
        total_expense_history,
        label='年間総支出',
        color=COLOR_PRIMARY,
        linewidth=2.2,
    )
    ax2.plot(
        age_history,
        annual_balance_history,
        label='年間収支',
        color=COLOR_DARK,
        linewidth=1.8,
        linestyle='-.',
    )
    ax2.fill_between(
        age_history,
        annual_balance_history,
        0,
        where=[b >= 0 for b in annual_balance_history],
        color=COLOR_GREEN,
        alpha=0.2,
        interpolate=True,
    )
    ax2.fill_between(
        age_history,
        annual_balance_history,
        0,
        where=[b < 0 for b in annual_balance_history],
        color=COLOR_PRIMARY,
        alpha=0.2,
        interpolate=True,
    )
    ax2.axhline(0, color='#A5B1C2', linestyle='--', alpha=0.7)
    ax2.axvline(retirement_age_h, color='#FF869E', linestyle=':', linewidth=2)
    ax2.axvspan(retirement_age_h, 100, color='#F1F2F6', alpha=0.5)
    ax2.set_title(
        '2. 年間手取り収入・支出・収支の推移',
        fontsize=13,
        fontweight='bold',
        color=COLOR_DARK,
        pad=12,
    )
    ax2.set_xlabel('夫の年齢 (歳)', fontsize=11, color=COLOR_DARK)
    ax2.set_ylabel('金額 (万円)', fontsize=11, color=COLOR_DARK)
    ax2.grid(True, linestyle=':', alpha=0.6, color='#E4E5E9')
    ax2.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='none')

    for ax in [ax1, ax2]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#D1D8E0')
        ax.spines['bottom'].set_color('#D1D8E0')

    plt.tight_layout()
    st.pyplot(fig1)

with tab2:
    fig_income, (ax_g, ax_n) = plt.subplots(2, 1, figsize=(10, 11), sharex=True)
    fig_income.patch.set_facecolor('#FFFDF9')
    ax_g.set_facecolor('#FFFFFF')
    ax_n.set_facecolor('#FFFFFF')

    ax_g.plot(
        age_history,
        household_gross_history,
        label='世帯合計 額面収入（給与＋年金）',
        color=COLOR_DARK,
        linewidth=2.5,
    )
    ax_g.plot(
        age_history,
        husband_gross_history,
        label='夫 額面給与収入',
        color=COLOR_SECONDARY,
        linestyle='--',
        linewidth=2.0,
    )
    ax_g.plot(
        age_history,
        wife_gross_history,
        label='妻 額面給与収入',
        color=COLOR_PRIMARY,
        linestyle='--',
        linewidth=2.0,
    )
    ax_g.plot(
        age_history,
        pension_gross_history,
        label='公的年金受給額（額面合計）',
        color=COLOR_PURPLE,
        linestyle=':',
        linewidth=2.2,
    )
    ax_g.axvline(
        retirement_age_h, color='#FF869E', linestyle=':', label='夫定年・移住'
    )
    ax_g.axvspan(retirement_age_h, 100, color='#F1F2F6', alpha=0.5)
    ax_g.set_title(
        '3. 額面収入の生涯推移',
        fontsize=13,
        fontweight='bold',
        color=COLOR_DARK,
        pad=12,
    )
    ax_g.set_ylabel('額面金額 (万円)', fontsize=11, color=COLOR_DARK)
    ax_g.grid(True, linestyle=':', alpha=0.6, color='#E4E5E9')
    ax_g.legend(
        loc='upper right', frameon=True, facecolor='#FFFFFF', edgecolor='none'
    )

    ax_n.plot(
        age_history,
        household_net_history,
        label='世帯合計 手取り収入',
        color=COLOR_GREEN,
        linewidth=2.5,
    )
    ax_n.plot(
        age_history,
        husband_net_history,
        label='夫 手取り給与',
        color=COLOR_SECONDARY,
        linestyle='--',
        linewidth=2.0,
    )
    ax_n.plot(
        age_history,
        wife_net_history,
        label='妻 手取り給与',
        color=COLOR_PRIMARY,
        linestyle='--',
        linewidth=2.0,
    )
    ax_n.plot(
        age_history,
        pension_net_history,
        label='公的年金（手取り換算）',
        color=COLOR_PURPLE,
        linestyle=':',
        linewidth=2.2,
    )
    ax_n.axvline(retirement_age_h, color='#FF869E', linestyle=':')
    ax_n.axvspan(retirement_age_h, 100, color='#F1F2F6', alpha=0.5)
    ax_n.set_title(
        '4. 手取り収入の生涯推移',
        fontsize=13,
        fontweight='bold',
        color=COLOR_DARK,
        pad=12,
    )
    ax_n.set_xlabel('夫の年齢 (歳)', fontsize=11, color=COLOR_DARK)
    ax_n.set_ylabel('手取り金額 (万円)', fontsize=11, color=COLOR_DARK)
    ax_n.grid(True, linestyle=':', alpha=0.6, color='#E4E5E9')
    ax_n.legend(
        loc='upper right', frameon=True, facecolor='#FFFFFF', edgecolor='none'
    )

    for ax in [ax_g, ax_n]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#D1D8E0')
        ax.spines['bottom'].set_color('#D1D8E0')

    plt.tight_layout()
    st.pyplot(fig_income)

with tab3:
    fig_child, ax3 = plt.subplots(figsize=(10, 6))
    fig_child.patch.set_facecolor('#FFFDF9')
    ax3.set_facecolor('#FFFFFF')

    if child_count >= 1:
        ax3.plot(
            age_history,
            child1_history,
            label=f'第1子 ({course_labels[child_courses[1]]})',
            color=COLOR_SECONDARY,
            linewidth=2.2,
        )
    if child_count >= 2:
        ax3.plot(
            age_history,
            child2_history,
            label=f'第2子 ({course_labels[child_courses[2]]})',
            color=COLOR_PURPLE,
            linewidth=2.2,
        )
    if child_count >= 3:
        ax3.plot(
            age_history,
            child3_history,
            label=f'第3子 ({course_labels[child_courses[3]]})',
            color=COLOR_GREEN,
            linewidth=2.2,
        )

    ax3.plot(
        age_history,
        total_child_expense_history,
        label='総子ども費用',
        color=COLOR_PRIMARY,
        linewidth=2.8,
        linestyle=':',
    )
    ax3.axvline(retirement_age_h, color='#FF869E', linestyle=':')
    ax3.axvspan(retirement_age_h, 100, color='#F1F2F6', alpha=0.5)
    ax3.set_title(
        '子育て費用の推移', fontsize=13, fontweight='bold', color=COLOR_DARK, pad=12
    )
    ax3.set_xlabel('夫の年齢 (歳)', fontsize=11, color=COLOR_DARK)
    ax3.set_ylabel('金額 (万円)', fontsize=11, color=COLOR_DARK)
    ax3.grid(True, linestyle=':', alpha=0.6, color='#E4E5E9')
    ax3.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='none')

    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['left'].set_color('#D1D8E0')
    ax3.spines['bottom'].set_color('#D1D8E0')

    plt.tight_layout()
    st.pyplot(fig_child)

with tab4:
    fig_port, ax4 = plt.subplots(figsize=(10, 6))
    fig_port.patch.set_facecolor('#FFFDF9')
    ax4.set_facecolor('#FFFFFF')

    ax4.stackplot(
        age_history,
        cash_ratio_history,
        investment_ratio_history,
        stock_ratio_history,
        labels=['現金比率(%)', '投資信託比率(%)', '株式比率(%)'],
        colors=['#B8F2E6', '#FFAAA6', '#DFCCF1'],
        alpha=0.85,
    )
    ax4.axvline(retirement_age_h, color='#FF869E', linestyle=':')
    ax4.axvspan(retirement_age_h, 100, color='#F1F2F6', alpha=0.5)
    ax4.set_title(
        '資産構成比率の推移', fontsize=13, fontweight='bold', color=COLOR_DARK, pad=12
    )
    ax4.set_xlabel('夫の年齢 (歳)', fontsize=11, color=COLOR_DARK)
    ax4.set_ylabel('比率 (%)', fontsize=11, color=COLOR_DARK)
    ax4.set_ylim(0, 100)
    ax4.grid(True, linestyle=':', alpha=0.6, color='#E4E5E9')
    ax4.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='none')

    ax4.spines['top'].set_visible(False)
    ax4.spines['right'].set_visible(False)
    ax4.spines['left'].set_color('#D1D8E0')
    ax4.spines['bottom'].set_color('#D1D8E0')

    plt.tight_layout()
    st.pyplot(fig_port)

# CSVエクスポート機能
st.markdown('---')
st.subheader('📥 シミュレーションデータのダウンロード')
df_export = pd.DataFrame({
    '夫の年齢': age_history,
    '総資産額(万円)': total_wealth_history,
    '現預金(万円)': cash_history,
    '投資信託(万円)': investment_history,
    '株式(万円)': stock_history,
    '世帯手取り収入(万円)': net_income_history,
    '年間総支出(万円)': total_expense_history,
    '年間収支(万円)': annual_balance_history,
})

csv_data = df_export.to_csv(index=False).encode('utf-8')
st.download_button(
    label='CSV形式で全データをダウンロード',
    data=csv_data,
    file_name='life_plan_simulation.csv',
    mime='text/csv',
)
