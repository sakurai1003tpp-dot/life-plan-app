from pathlib import Path
from google import genai
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import time

# ------------------------------------------
# グラフの基本設定（Streamlit Cloudでも日本語を表示）
# ------------------------------------------
JAPANESE_FONT_PATH = Path(__file__).with_name("NotoSansJP-VF.ttf")
if JAPANESE_FONT_PATH.exists():
    font_manager.fontManager.addfont(JAPANESE_FONT_PATH)
    japanese_font = font_manager.FontProperties(fname=JAPANESE_FONT_PATH).get_name()
    plt.rcParams["font.family"] = japanese_font
    plt.rcParams["font.sans-serif"] = [japanese_font]
else:
    st.error(
        "日本語フォントが見つかりません。app.pyと同じフォルダに"
        "「NotoSansJP-VF.ttf」を追加してください。"
    )
    st.stop()

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 300

# パステル＆モダンなカラーパレット
COLOR_PRIMARY = "#FF6B6B"
COLOR_SECONDARY = "#4D96FF"
COLOR_ACCENT = "#FFD93D"
COLOR_GREEN = "#6BCB77"
COLOR_PURPLE = "#9D4EDD"
COLOR_DARK = "#2B2D42"

# 画面設定と洗練されたカスタムCSS
st.set_page_config(
    page_title="ライフプランシミュレーション",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
<style>
    .main { background-color: #F8F9FA; }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }
    .metric-title { font-size: 0.85rem; color: #6B7280; font-weight: 600; margin-bottom: 6px; }
    .metric-value { font-size: 1.5rem; color: #111827; font-weight: 700; }
    .stApp header { background-color: transparent; }
</style>
""",
    unsafe_allow_html=True,
)

# タイトルエリア
st.markdown(
    """
    <div style="padding: 1rem 0; margin-bottom: 1rem;">
        <h1 style="font-size: 1.8rem; font-weight: 700; color: #111827; letter-spacing: -0.025em; margin-bottom: 4px;">
            ライフプランシミュレーション（企業型DC・医療保険個別管理版）
        </h1>
        <p style="font-size: 0.95rem; color: #4B5563; font-weight: 400;">
            将来の資産形成・キャッシュフロー・教育費、企業型DC、そして民間・公的保険の個別管理を可視化します
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------
# サイドバー設定パネル
# ------------------------------------------
st.sidebar.markdown("### ⚙️ シミュレーション設定")
if st.sidebar.button("🔄 全設定を初期値に戻す", use_container_width=True):
    st.session_state.clear()
    st.rerun()

chart_scale = st.sidebar.slider("グラフの表示倍率", 0.5, 1.0, 1.0, step=0.1)

st.sidebar.markdown("---")

with st.sidebar.expander("👨‍👩‍👧‍👦 家族・働き方設定"):
    current_age_h = st.slider("夫の現在の年齢（歳）", 20, 60, 29)
    current_age_w = st.slider("妻の現在の年齢（歳）", 20, 60, 30)
    retirement_age_h = st.slider("夫の退職年齢（歳）", 50, 75, 65)
    retirement_age_w = st.slider("妻の退職年齢（歳）", 50, 75, 55)
    pension_start_age_h = st.slider("夫の年金受給開始年齢（歳）", 60, 75, 65)
    pension_start_age_w = st.slider("妻の年金受給開始年齢（歳）", 60, 75, 70)

with st.sidebar.expander("⚰️ 万が一の備え（配偶者死亡時）"):
    husband_death_age = st.slider("夫の想定死亡年齢", 60, 100, 85)
    death_lump_sum_cost = st.number_input("介護・葬儀等の一次費用 (万円)", 0, 1000, 300, step=10)
    survivor_pension_ratio = st.slider("遺族年金移行時の夫年金の受給割合 (%)", 0, 100, 75) / 100.0

with st.sidebar.expander("💰 収入・退職金設定"):
    gross_income_w = st.number_input("妻の現在年収 (万円)", 0, 5000, 400, step=10)
    income_change_rate_w = st.slider("妻の年収上昇率 (%/年)", 0.0, 5.0, 1.25, step=0.05)
    child_care_reduction_years = st.selectbox("育児短時間勤務の期間（年）", [1, 2, 3, 4, 5, 6, 7, 8], index=4)
    retirement_payout_h = st.number_input("夫の退職金 (万円)", 0, 5000, 2000, step=100)
    retirement_payout_w = st.number_input("妻の退職金 (万円)", 0, 5000, 500, step=100)

with st.sidebar.expander("👶 子ども・育休設定"):
    child_count = st.selectbox("子供の人数", [0, 1, 2, 3], index=1)
    first_birth_age_h = st.slider("第1子誕生時の夫の年齢", 22, 50, 31)
    birth_interval = st.slider("きょうだいの年齢差（年）", 1, 5, 3)
    maternity_leave_per_child = st.selectbox("子1人あたりの産休・育休期間（年）", [1, 2, 3], index=1)
    nursery_cost_0_to_2 = st.number_input("0〜2歳の保育費等（年額・万円）", 0, 200, 30, step=5)

    child_courses = {}
    course_labels = {
        "ALL_PUBLIC": "大学まで全公立",
        "PUBLIC_UNIV_RIKEI": "高校まで公立・大学は私立理系",
        "PUBLIC_UNIV_BUNKEI": "高校まで公立・大学は私立文系",
    }
    for i in range(1, child_count + 1):
        child_courses[i] = st.selectbox(
            f"第{i}子の進路", list(course_labels.keys()), format_func=lambda x: course_labels[x], index=0 if i==1 else 1, key=f"course_{i}"
        )

with st.sidebar.expander("📈 資産・企業型DC・運用設定", expanded=True):
    current_cash = st.number_input("現在の現預金 (万円)", 0, 50000, 1000, step=50)
    current_investment = st.number_input("現在の投資信託 (万円)", 0, 50000, 1300, step=50)
    current_stock = st.number_input("現在の株式 (万円)", 0, 50000, 130, step=10)
    current_ideco = st.number_input("現在の企業型DC資産残高 (万円)", 0, 20000, 78, step=1)
    ideco_monthly_contribution = st.number_input("企業型DC 毎月の掛金 (万円/月)", 0.0, 7.0, 1.0, step=0.5)
    ideco_receive_age = st.slider("企業型DC 受給開始年齢（歳）", 60, 75, 60)
    base_real_return_rate = st.slider("投資信託・企業型DCの想定実質利回り (%)", 0.0, 10.0, 2.8, step=0.1)
    emergency_fund_months = st.slider("緊急資金の目安（生活費の月数）", 0, 24, 6)
    max_cash_limit = st.number_input("現預金の保有上限 (万円)", 100, 5000, 1000, step=50)

with st.sidebar.expander("🏥 医療・民間保険設定", expanded=True):
    annual_insurance_active = st.number_input("現役期の年間民間保険料（医療・がん保険等・万円）", 0, 50, 12, step=1)
    annual_insurance_retired = st.number_input("老後の年間民間保険料（医療・がん保険等・万円）", 0, 50, 8, step=1)
    enable_medical_event = st.checkbox("特定の年齢で大きな病気（入院・手術）を想定する", value=True)
    medical_event_age = st.slider("病気を想定する夫の年齢", 40, 90, 55)
    medical_event_cost = st.number_input("医療・入院時の自己負担臨時費用（万円）", 0, 500, 100, step=10)

with st.sidebar.expander("🏠 支出・インフレ・年金連動設定"):
    expense_change_rate = st.slider("インフレ率（生活費の上昇率 %）", 0.0, 5.0, 1.4, step=0.1)
    pension_indexation_rate = st.slider("年金改定率のインフレ率に対する連動割合 (%)", 0.0, 100.0, 80.0, step=5.0) / 100.0
    living_expenses_monthly = st.number_input("基本生活費 (毎月・万円)", 0, 100, 30, step=1)
    housing_expenses_monthly = st.number_input("住居費 (毎月・万円)", 0, 50, 15, step=1)
    annual_travel_cost = st.number_input("年間旅行費 (万円)", 0, 200, 20, step=5)
    general_medical_cost = st.number_input("年間医療費 (万円)", 0, 50, 5, step=1)
    annual_social_cost = st.number_input("年間交際費 (万円)", 0, 100, 20, step=5)

with st.sidebar.expander("🏦 年金設定"):
    pension_at_65_h = st.number_input("夫の65歳年金見込額（額面・万円）", 0, 1000, 260, step=5)
    pension_at_65_w = st.number_input("妻の65歳年金見込額（額面・万円）", 0, 1000, 165, step=5)

with st.sidebar.expander("🚗 車・老後公的保険設定"):
    car_purchase_price = st.number_input("車の購入価格 (万円)", 0, 1000, 300, step=10)
    car_maintenance_cost = st.number_input("車の年間維持費 (万円)", 0, 100, 40, step=1)
    car_replacement_cycle = st.slider("車の買替サイクル (年)", 5, 20, 10)
    regional_house_cost = st.number_input("定年時 住宅購入費用 (万円)", 0, 20000, 5000, step=100)
    annual_home_maintenance_cost = st.number_input("老後の住宅維持費（年額・万円）", 0, 300, 50, step=5)
    annual_retirement_insurance_cost = st.number_input("老後の公的医療保険料（国保・後期高齢者等・年額・万円）", 0, 300, 60, step=5)
    migration_medical_cost_multiplier = st.slider("老後の医療費倍率", 1.0, 10.0, 4.0, step=0.1)
    next_year_one_time_expense = st.number_input("翌年の臨時支出（万円）", 0, 2000, 200, step=10)

# ------------------------------------------
# 共通計算ロジック
# ------------------------------------------
living_expenses = living_expenses_monthly * 12
housing_expenses_base = housing_expenses_monthly * 12
stock_return_rate = 1.5
stock_dividend_yield = 2.5
investment_stop_age_h = 60
migration_housing_expenses = 50
housing_increase_on_child = 60
migration_living_expense_ratio = 0.80

birth_ages_h, birth_ages_w = [], []
if child_count > 0:
    for n in range(child_count):
        b_h = first_birth_age_h + (n * birth_interval)
        birth_ages_h.append(b_h)
        birth_ages_w.append(current_age_w + (b_h - current_age_h))

maternity_leave_years_w = sorted(list(set([b_w + y for b_w in birth_ages_w for y in range(maternity_leave_per_child)])))
reduced_income_years_w = sorted(list(set([b_w + maternity_leave_per_child + y for b_w in birth_ages_w for y in range(child_care_reduction_years)])))

def calculate_husband_base_gross_income(age):
    if age < 29 or age >= retirement_age_h: return 0
    elif age <= 41:
        base_income_at_41 = 1200.0 / (1 + (1.25 * 45 * 12 / 1920))
        return 532.72 + (age - 29) * ((base_income_at_41 - 532.72) / 12)
    else:
        return 1100.0 + (age - 42) * ((1500.0 - 1100.0) / max(1, retirement_age_h - 1 - 42))

def calculate_husband_gross_income(age):
    base = calculate_husband_base_gross_income(age)
    if base <= 0: return 0
    if age < 42:
        return base + (((base * 10000) / 1920) * 1.25 * 45 * 12 / 10000)
    return base

def adjust_pension(pension_at_65, start_age):
    if start_age >= 65: return pension_at_65 * (1 + (start_age - 65) * 12 * 0.007)
    return pension_at_65 * (1 - (65 - start_age) * 12 * 0.004)

calculated_pension_h = adjust_pension(pension_at_65_h, pension_start_age_h)
calculated_pension_w = adjust_pension(pension_at_65_w, pension_start_age_w)

def calculate_net_income(gross):
    if gross <= 0: return 0
    elif gross <= 300: return gross * 0.85
    elif gross <= 600: return gross * 0.80
    elif gross <= 1000: return gross * 0.75
    else: return gross * 0.70

def get_child_yearly_expense(c_age, course_type):
    if not (0 <= c_age <= 21): return 0
    if c_age <= 2: return nursery_cost_0_to_2
    elif c_age <= 5: return 18.4646
    elif c_age <= 11: return 36.6599
    elif c_age <= 14: return 54.2450
    elif c_age <= 17: return 59.6954
    else:
        if course_type == "ALL_PUBLIC": return 58.30
        elif course_type == "PUBLIC_UNIV_RIKEI": return 153.0451 if c_age == 18 else 129.5694
        elif course_type == "PUBLIC_UNIV_BUNKEI": return 119.4841 if c_age == 18 else 97.0973
        return 58.30

def get_child_living_expense_addition(c_age, course_type=None):
    if not (0 <= c_age <= 21): return 0
    if c_age <= 3: return 15
    elif c_age <= 11: return 30
    elif c_age <= 17: return 55
    else: return 75.34 if course_type == "ALL_PUBLIC" else 63.15

# ------------------------------------------
# シミュレーション実行関数（民間・公聴保険個別管理対応）
# ------------------------------------------
def run_simulation(real_return_rate):
    res = {k: [] for k in ["age", "wealth", "cash", "invest", "stock", "ideco", "net_income", "expense", "balance", 
                         "child1", "child2", "child3", "child_total", "cash_ratio", "invest_ratio", "stock_ratio", "ideco_ratio",
                         "h_gross", "w_gross", "p_gross", "hh_gross", "h_net", "w_net", "p_net", "hh_net"]}
    
    sim_cash = current_cash
    sim_investment = current_investment
    sim_stock = current_stock
    sim_ideco = current_ideco
    asset_depletion_age = None
    
    effective_pension_rate = (expense_change_rate * pension_indexation_rate) / 100.0

    for i in range(100 - current_age_h + 1):
        age_h = current_age_h + i
        age_w = current_age_w + i
        inflation_factor = (1 + expense_change_rate / 100) ** i
        is_husband_dead = age_h > husband_death_age

        current_nominal_return_rate = real_return_rate + expense_change_rate

        annual_ideco_contribution = 0
        if age_h < 60 and not is_husband_dead:
            annual_ideco_contribution = ideco_monthly_contribution * 12

        if i > 0:
            sim_investment *= (1 + current_nominal_return_rate / 100)
            sim_stock *= (1 + stock_return_rate / 100)
            sim_ideco *= (1 + current_nominal_return_rate / 100)
        
        sim_ideco += annual_ideco_contribution
        sim_cash -= annual_ideco_contribution

        if age_h == ideco_receive_age and sim_ideco > 0:
            sim_cash += sim_ideco
            sim_ideco = 0

        annual_dividend = (sim_stock * (stock_dividend_yield / 100)) * 0.79685 if sim_stock > 0 else 0

        gross_h = 0 if is_husband_dead else calculate_husband_gross_income(age_h)
        net_h = calculate_net_income(gross_h) if age_h < retirement_age_h else 0
        
        gross_w = 0
        if age_w < retirement_age_w:
            if age_w not in maternity_leave_years_w:
                base_w = gross_income_w * ((1 + income_change_rate_w / 100) ** i)
                if age_w in reduced_income_years_w: base_w *= (1 - 0.30)
                gross_w = base_w
        net_w = calculate_net_income(gross_w)

        extra_retirement_cash = (retirement_payout_w if age_w == retirement_age_w else 0) + \
                                (retirement_payout_h if age_h == retirement_age_h and not is_husband_dead else 0)
        
        p_gross_h = calculated_pension_h * ((1 + effective_pension_rate) ** i) if age_h >= pension_start_age_h else 0
        if is_husband_dead: p_gross_h *= survivor_pension_ratio
        p_gross_w = calculated_pension_w * ((1 + effective_pension_rate) ** i) if age_w >= pension_start_age_w else 0
        current_pension_gross = p_gross_h + p_gross_w
        current_pension_net = current_pension_gross
        
        pure_annual_income = net_h + net_w + current_pension_net + annual_dividend
        total_gross_income = gross_h + gross_w + current_pension_gross + annual_dividend

        annual_car_cost_inflated = (car_maintenance_cost + (car_purchase_price / car_replacement_cycle)) * inflation_factor
        
        # 民間保険料の計算（現役期と老後でそれぞれの民間保険料を切り替え・インフレ反映）
        current_private_insurance_cost = (annual_insurance_active if age_h < retirement_age_h else annual_insurance_retired) * inflation_factor

        if age_h < retirement_age_h or age_w < retirement_age_w:
            current_housing = housing_expenses_base + (housing_increase_on_child if (child_count > 0 and age_h >= first_birth_age_h) else 0)
            total_child_living = sum([get_child_living_expense_addition(age_h - first_birth_age_h - n*birth_interval, child_courses.get(n+1)) 
                                    for n in range(child_count)])
            annual_expense = (living_expenses + total_child_living + current_housing + annual_travel_cost + general_medical_cost + annual_social_cost + annual_car_cost_inflated + current_private_insurance_cost) * inflation_factor
        else:
            base_expense = (living_expenses * migration_living_expense_ratio) + migration_housing_expenses + annual_car_cost_inflated + annual_travel_cost + annual_social_cost + current_private_insurance_cost
            # 老後は公的医療保険料（annual_retirement_insurance_cost）も個別に追加して計算
            annual_expense = (base_expense * (0.90 if age_h >= 75 else 1.0) + general_medical_cost * migration_medical_cost_multiplier + annual_home_maintenance_cost + annual_retirement_insurance_cost) * inflation_factor

        if is_husband_dead:
            annual_expense *= 0.70

        extra_one_time = next_year_one_time_expense if i == 1 else 0
        if age_h == husband_death_age:
            extra_one_time += death_lump_sum_cost * inflation_factor
        
        if enable_medical_event and age_h == medical_event_age and not is_husband_dead:
            extra_one_time += medical_event_cost * inflation_factor

        c_exp = [get_child_yearly_expense(age_h - first_birth_age_h - n*birth_interval, child_courses.get(n+1)) * inflation_factor for n in range(child_count)]
        c_exp += [0] * (3 - len(c_exp))
        
        pure_total_expense = annual_expense + sum(c_exp) + extra_one_time
        pure_annual_balance = pure_annual_income - pure_total_expense

        sim_cash += pure_annual_balance + extra_retirement_cash
        
        min_cash_reserve = pure_total_expense * (emergency_fund_months / 12)

        if age_h == retirement_age_h and not is_husband_dead:
            sim_cash += sim_stock
            sim_stock = 0
            needed = (regional_house_cost * inflation_factor) - sim_cash
            if needed > 0:
                sale = min(needed, sim_investment)
                sim_investment -= sale
                sim_cash += sale
            sim_cash -= (regional_house_cost * inflation_factor)

        if sim_cash < min_cash_reserve:
            shortfall = min_cash_reserve - sim_cash
            if sim_stock >= shortfall:
                sim_stock -= shortfall; sim_cash += shortfall
            else:
                shortfall -= sim_stock; sim_cash += sim_stock; sim_stock = 0
                if sim_investment >= shortfall:
                    sim_investment -= shortfall; sim_cash += shortfall
                else:
                    sim_cash += sim_investment; sim_investment = 0
        elif age_h < investment_stop_age_h and sim_cash > max_cash_limit:
            excess = sim_cash - max_cash_limit
            sim_cash = max_cash_limit; sim_investment += excess

        total_wealth = sim_cash + sim_investment + sim_stock + sim_ideco
        if total_wealth < 0 and asset_depletion_age is None:
            asset_depletion_age = age_h

        res["age"].append(age_h)
        res["wealth"].append(total_wealth)
        res["cash"].append(sim_cash)
        res["invest"].append(sim_investment)
        res["stock"].append(sim_stock)
        res["ideco"].append(sim_ideco)
        res["net_income"].append(pure_annual_income)
        res["expense"].append(pure_total_expense)
        res["balance"].append(pure_annual_balance)
        res["child1"].append(c_exp[0])
        res["child2"].append(c_exp[1])
        res["child3"].append(c_exp[2])
        res["child_total"].append(sum(c_exp))
        res["cash_ratio"].append((sim_cash/total_wealth)*100 if total_wealth>0 else 100)
        res["invest_ratio"].append((sim_investment/total_wealth)*100 if total_wealth>0 else 0)
        res["stock_ratio"].append((sim_stock/total_wealth)*100 if total_wealth>0 else 0)
        res["ideco_ratio"].append((sim_ideco/total_wealth)*100 if total_wealth>0 else 0)
        res["h_gross"].append(gross_h)
        res["w_gross"].append(gross_w)
        res["p_gross"].append(current_pension_gross)
        res["hh_gross"].append(total_gross_income)
        res["h_net"].append(net_h)
        res["w_net"].append(net_w)
        res["p_net"].append(current_pension_net)
        res["hh_net"].append(pure_annual_income)

    res["depletion_age"] = asset_depletion_age
    return res

base_res = run_simulation(base_real_return_rate)

# ------------------------------------------
# メトリクスカードとアラート
# ------------------------------------------
initial_wealth = current_cash + current_investment + current_stock + current_ideco
peak_wealth = max(base_res["wealth"])
idx_80 = base_res["age"].index(current_age_h + (80 - current_age_h)) if (current_age_h + (80 - current_age_h)) in base_res["age"] else -1
wealth_at_80 = base_res["wealth"][idx_80]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">現在の総資産（企業型DC込）</div><div class="metric-value">{initial_wealth:,.0f} 万円</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">資産ピーク時（{base_res["age"][base_res["wealth"].index(peak_wealth)]}歳）</div><div class="metric-value">{peak_wealth:,.0f} 万円</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">80歳時点の残高</div><div class="metric-value">{wealth_at_80:,.0f} 万円</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">子供の人数</div><div class="metric-value">{child_count} 人</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if base_res["depletion_age"] is not None:
    dep_age = base_res["depletion_age"]
    shortfall_total = -base_res["wealth"][-1]
    years_short = 100 - dep_age + 1
    annual_short = shortfall_total / years_short if years_short > 0 else 0
    st.error(
        f"⚠️ **{dep_age}歳で総資産がマイナスになる見込みです。**\n\n"
        f"100歳時点での累計不足額は約 **{shortfall_total:,.0f}万円** となります。\n"
        f"これを補うためには、{dep_age}歳以降、**年間約 {annual_short:,.0f}万円（月額約 {annual_short/12:,.0f}万円）** の収支改善が必要です。"
    )
else:
    st.success("✅ 100歳まで総資産はマイナスにならない見込みです。順調な資産形成計画です！")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------
# タブの作成
# ------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📈 資産・収支シミュレーション", "💰 収入・詳細推移", "👶 子育て費用", "📊 ポートフォリオ", "📉 資産運用シミュレーション", "🤖 Gemini AI 家計診断"]
)

with tab1:
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(10 * chart_scale, 11 * chart_scale), sharex=True)
    fig1.patch.set_facecolor("#F8F9FA")
    
    current_nominal_display = base_real_return_rate + expense_change_rate
    ax1.plot(base_res["age"], base_res["wealth"], label="総資産", color=COLOR_PRIMARY, linewidth=3.0)
    ax1.plot(base_res["age"], base_res["cash"], label="現預金", color=COLOR_GREEN, linestyle="--", linewidth=2.0)
    ax1.plot(base_res["age"], base_res["invest"], label=f"投資信託（実質{base_real_return_rate}%）", color=COLOR_SECONDARY, linestyle="--", linewidth=2.0)
    ax1.plot(base_res["age"], base_res["stock"], label=f"個別株式（固定 {stock_return_rate}%）", color=COLOR_PURPLE, linestyle=":", linewidth=2.0)
    ax1.plot(base_res["age"], base_res["ideco"], label=f"企業型DC資産（{ideco_monthly_contribution}万円/月）", color=COLOR_ACCENT, linestyle="-.", linewidth=2.0)
    
    ax1.axvline(retirement_age_h, color="#FF869E", linestyle=":", label="夫の退職")
    ax1.axvline(husband_death_age, color="#2B2D42", linestyle=":", label="夫の想定死亡")
    ax1.set_title("生涯資産シミュレーション（民間・公的保険個別管理版）", fontsize=13, fontweight="bold", color=COLOR_DARK, pad=12)
    ax1.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor="none")
    ax1.grid(True, linestyle=":", alpha=0.6)
    
    ax2.plot(base_res["age"], base_res["hh_net"], label="手取り収入", color=COLOR_SECONDARY, linewidth=2.2)
    ax2.plot(base_res["age"], base_res["expense"], label="総支出", color=COLOR_PRIMARY, linewidth=2.2)
    ax2.plot(base_res["age"], base_res["balance"], label="年間収支", color=COLOR_DARK, linewidth=1.8, linestyle="-.")
    ax2.fill_between(base_res["age"], base_res["balance"], 0, where=[b >= 0 for b in base_res["balance"]], color=COLOR_GREEN, alpha=0.2)
    ax2.fill_between(base_res["age"], base_res["balance"], 0, where=[b < 0 for b in base_res["balance"]], color=COLOR_PRIMARY, alpha=0.2)
    ax2.axvline(retirement_age_h, color="#FF869E", linestyle=":")
    ax2.axvline(husband_death_age, color="#2B2D42", linestyle=":")
    ax2.set_title("年間収入・支出・収支", fontsize=13, fontweight="bold", color=COLOR_DARK, pad=12)
    ax2.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor="none")
    ax2.grid(True, linestyle=":", alpha=0.6)
    
    for ax in [ax1, ax2]:
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.set_facecolor("#FFFFFF")
    plt.tight_layout()
    st.pyplot(fig1)

with tab2:
    fig2, ax_n = plt.subplots(figsize=(10 * chart_scale, 6 * chart_scale))
    fig2.patch.set_facecolor("#F8F9FA")
    ax_n.set_facecolor("#FFFFFF")
    ax_n.plot(base_res["age"], base_res["hh_gross"], label="世帯額面収入", color=COLOR_PRIMARY, linewidth=2.5)
    ax_n.plot(base_res["age"], base_res["hh_net"], label="世帯手取り収入", color=COLOR_GREEN, linewidth=2.5, linestyle="--")
    ax_n.plot(base_res["age"], base_res["h_net"], label="夫手取り", color=COLOR_SECONDARY, linestyle=":")
    ax_n.plot(base_res["age"], base_res["w_net"], label="妻手取り", color=COLOR_ACCENT, linestyle=":")
    ax_n.plot(base_res["age"], base_res["p_net"], label="年金（額面＝手取り）", color=COLOR_PURPLE, linestyle="-.")
    ax_n.axvline(husband_death_age, color="#2B2D42", linestyle=":", label="夫の想定死亡")
    ax_n.set_title("収入（額面・手取り）の推移", fontsize=13, fontweight="bold", color=COLOR_DARK)
    ax_n.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", edgecolor="none")
    ax_n.grid(True, linestyle=":", alpha=0.6)
    ax_n.spines["top"].set_visible(False); ax_n.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig2)

with tab3:
    fig3, ax3 = plt.subplots(figsize=(10 * chart_scale, 6 * chart_scale))
    fig3.patch.set_facecolor("#F8F9FA")
    ax3.set_facecolor("#FFFFFF")
    colors = [COLOR_SECONDARY, COLOR_PURPLE, COLOR_GREEN]
    for i in range(child_count):
        ax3.plot(base_res["age"], base_res[f"child{i+1}"], label=f"第{i+1}子の費用", color=colors[i])
    ax3.plot(base_res["age"], base_res["child_total"], label="子ども費用合計", color=COLOR_PRIMARY, linewidth=2.8, linestyle=":")
    ax3.set_title("子どもの教育費", fontsize=13, fontweight="bold", color=COLOR_DARK)
    ax3.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor="none")
    ax3.grid(True, linestyle=":", alpha=0.6)
    ax3.spines["top"].set_visible(False); ax3.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig3)

with tab4:
    fig4, ax4 = plt.subplots(figsize=(10 * chart_scale, 6 * chart_scale))
    fig4.patch.set_facecolor("#F8F9FA")
    ax4.set_facecolor("#FFFFFF")
    ax4.stackplot(base_res["age"], base_res["cash_ratio"], base_res["invest_ratio"], base_res["stock_ratio"], base_res["ideco_ratio"], 
                  labels=["現預金", "投資信託", "株式", "企業型DC"], colors=["#B8F2E6", "#FFAAA6", "#DFCCF1", "#FFD93D"], alpha=0.85)
    ax4.set_title("資産配分比率の推移（企業型DC含む）", fontsize=13, fontweight="bold", color=COLOR_DARK)
    ax4.set_ylim(0, 100)
    ax4.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor="none")
    ax4.spines["top"].set_visible(False); ax4.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig4)

with tab5:
    st.markdown("### 📊 運用利回りのシナリオ別比較")
    st.write(f"インフレ率（{expense_change_rate}%）に対する実質利回りのシナリオ（標準：{base_real_return_rate}%、保守的：{max(0, base_real_return_rate-1.5):.1f}%、積極的：{base_real_return_rate+1.5:.1f}%）で総資産の推移を比較します。")
    
    res_weak = run_simulation(max(0, base_real_return_rate - 1.5))
    res_strong = run_simulation(base_real_return_rate + 1.5)
    
    fig5, ax5 = plt.subplots(figsize=(10 * chart_scale, 6 * chart_scale))
    fig5.patch.set_facecolor("#F8F9FA")
    ax5.set_facecolor("#FFFFFF")
    ax5.plot(base_res["age"], base_res["wealth"], label=f"標準実質利回り ({base_real_return_rate}%)", color=COLOR_PRIMARY, linewidth=3.0)
    ax5.plot(res_weak["age"], res_weak["wealth"], label=f"保守的実質利回り ({max(0, base_real_return_rate-1.5):.1f}%)", color=COLOR_SECONDARY, linewidth=2.0, linestyle="--")
    ax5.plot(res_strong["age"], res_strong["wealth"], label=f"積極的実質利回り ({base_real_return_rate+1.5:.1f}%)", color=COLOR_GREEN, linewidth=2.0, linestyle="--")
    
    ax5.axvline(retirement_age_h, color="#FF869E", linestyle=":", label="夫の退職")
    ax5.set_title("利回りシナリオ別の総資産推移", fontsize=13, fontweight="bold", color=COLOR_DARK)
    ax5.set_xlabel("夫の年齢（歳）")
    ax5.set_ylabel("総資産（万円）")
    ax5.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor="none")
    ax5.grid(True, linestyle=":", alpha=0.6)
    ax5.spines["top"].set_visible(False)
    ax5.spines["right"].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig5)

with tab6:
    st.markdown("### 🤖 Gemini AIによる家計診断")
    st.write("現在のパラメータとシミュレーション結果（企業型DC、民間保険・公的保険・医療費イベントなど）をAIに送信し、プロのファイナンシャルプランナーの視点から改善アドバイスを受け取ります。")
    
    if st.button("🚀 AIに家計診断を依頼する", type="primary", use_container_width=True):
        with st.spinner("Geminiが家計の診断とアドバイスを生成中...（混雑時は自動で再試行します）"):
            try:
                client = genai.Client(api_key="AQ.Ab8RN6K-KKtdj7nYhxG2JU8LaGNvHuu2_1UkoxVNHXDfQ8F6QQ")
                
                medical_info_str = f"あり（{medical_event_age}歳時に臨時費用 {medical_event_cost}万円）" if enable_medical_event else "なし"
                summary_text = f"""
【シミュレーション条件・パラメータ】
- 夫の年齢: {current_age_h}歳（退職: {retirement_age_h}歳）
- 妻の年齢: {current_age_w}歳（退職: {retirement_age_w}歳）
- 子供の人数: {child_count}人
- 現在の資産: 現預金 {current_cash}万円 / 投資信託 {current_investment}万円 / 株式 {current_stock}万円 / 企業型DC {current_ideco}万円 (合計: {initial_wealth}万円)
- 企業型DC積立: 毎月 {ideco_monthly_contribution}万円（受給開始: {ideco_receive_age}歳）
- 定年時住宅購入費用: {regional_house_cost}万円
- 保険設定: 現役期民間保険料 {annual_insurance_active}万円 / 老後民間保険料 {annual_insurance_retired}万円 / 老後公的医療保険料 {annual_retirement_insurance_cost}万円
- 医療イベント想定: {medical_info_str}
- 毎月の基本生活費: {living_expenses_monthly}万円 / 住居費: {housing_expenses_monthly}万円
- 想定実質利回り: {base_real_return_rate}% / インフレ率: {expense_change_rate}%

【シミュレーション結果サマリー】
- 資産ピーク時: {peak_wealth:,.0f}万円
- 80歳時点の総資産: {wealth_at_80:,.0f}万円
- 資産破綻（マイナス）の有無・年齢: {f"{base_res['depletion_age']}歳で破綻" if base_res['depletion_age'] is not None else "100歳まで破綻なし"}
"""
                prompt = f"""
あなたは優秀なファイナンシャルプランナー（FP）です。以下の企業型DCや民間・公的保険の個別管理、医療費イベントを含むライフプランシミュレーション結果を分析し、ユーザーに対して親身かつ具体的で実用的なアドバイス・家計診断を行ってください。

{summary_text}

以下の構成で回答を出力してください：
1. **全体の評価・総評**（この家計の強みと最大の懸念点、民間・公的保険の分担や企業型DC活用の評価）
2. **懸念されるリスクへの対策**（保険料負担や医療イベント、60歳時の5,000万円の住宅購入費、キャッシュフローについて）
3. **具体的なアクションプラン**（今日から実行できる改善提案を2〜3個）
"""
                
                response = None
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=prompt,
                        )
                        break
                    except Exception as api_err:
                        err_str = str(api_err)
                        if ("503" in err_str or "UNAVAILABLE" in err_str or "overloaded" in err_str.lower()) and attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                        else:
                            raise api_err

                st.markdown("---")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"APIの呼び出し中にエラーが発生しました（サーバー側が一時的に混雑しています。少し時間を置いて再度お試しください）: {e}")
