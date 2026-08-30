import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

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

# パステル＆ポップなカラーパレット
COLOR_PRIMARY = "#FF6B6B"  # コーラルピンク
COLOR_SECONDARY = "#4D96FF"  # スカイブルー
COLOR_ACCENT = "#FFD93D"  # サンイエロー
COLOR_GREEN = "#6BCB77"  # ミントグリーン
COLOR_PURPLE = "#9D4EDD"  # ラベンダー
COLOR_DARK = "#2B2D42"  # チャコールグレー

# 画面設定とカスタムCSS
st.set_page_config(page_title="ライフプランシミュレーション", layout="wide")

st.markdown(
    """
<style>
    .main { background-color: #FFFDF9; }
    .metric-card {
        background-color: #FFFFFF;
        border: 2px solid #FFE3E3;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.08);
    }
    .metric-title { font-size: 0.85rem; color: #8D99AE; font-weight: 600; margin-bottom: 5px; }
    .metric-value { font-size: 1.5rem; color: #2B2D42; font-weight: 700; }
</style>
""",
    unsafe_allow_html=True,
)

# メインタイトル
st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <h1 style="font-size: 1.4rem; font-weight: 600; color: #2B2D42; letter-spacing: -0.025em; margin-bottom: 4px;">
            ライフプランシミュレーション
        </h1>
        <p style="font-size: 0.85rem; color: #8D99AE; font-weight: 400;">
            将来の資産形成・キャッシュフロー・教育費・老後リスクを可視化します
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# ------------------------------------------
# サイドバー設定パネル
# ------------------------------------------
if st.sidebar.button("🔄 全設定を初期値に戻す", use_container_width=True):
    st.session_state.clear()
    st.session_state["scroll_sidebar_to_top"] = True
    st.rerun()

st.sidebar.header("👨‍👩‍👧‍👦 家族・働き方設定")
current_age_h = st.sidebar.slider("夫の現在の年齢（歳）", 20, 60, 29)
current_age_w = st.sidebar.slider("妻の現在の年齢（歳）", 20, 60, 30)
retirement_age_h = st.sidebar.slider("夫の退職年齢（歳）", 50, 75, 65)
retirement_age_w = st.sidebar.slider("妻の退職年齢（歳）", 50, 75, 55)
pension_start_age_h = st.sidebar.slider("夫の年金受給開始年齢（歳）", 60, 75, 65)
pension_start_age_w = st.sidebar.slider("妻の年金受給開始年齢（歳）", 60, 75, 70)

st.sidebar.header("🏦 年金設定")
pension_at_65_h = st.sidebar.number_input("夫の65歳時点の年金見込額（万円）", 0, 1000, 260, step=5)
pension_at_65_w = st.sidebar.number_input("妻の65歳時点の年金見込額（万円）", 0, 1000, 165, step=5)
pension_indexation_rate = st.sidebar.slider("年金額の年間改定率（%）", 0.0, 3.0, 1.0, step=0.1)

st.sidebar.header("👶 子ども・育休設定")
child_count = st.sidebar.selectbox("子供の人数", [0, 1, 2, 3], index=1)
first_birth_age_h = st.sidebar.slider("第1子誕生時の夫の年齢", 22, 50, 31)
birth_interval = st.sidebar.slider("きょうだいの年齢差（年）", 1, 5, 3)
maternity_leave_per_child = st.sidebar.selectbox("子1人あたりの産休・育休期間（年）", [1, 2, 3], index=1)
nursery_cost_0_to_2 = st.sidebar.number_input("0〜2歳の保育費等（年額・万円）", 0, 200, 30, step=5)

child_courses = {}
course_labels = {
    "ALL_PUBLIC": "大学まで全公立",
    "PUBLIC_UNIV_RIKEI": "高校公立・大学私立理系",
    "PUBLIC_UNIV_BUNKEI": "高校公立・大学私立文系",
}
for n in range(1, child_count + 1):
    child_courses[n] = st.sidebar.selectbox(f"第{n}子の進路", list(course_labels.keys()), format_func=lambda x: course_labels[x], index=0 if n==1 else 1)

st.sidebar.header("💰 収入・働き方設定")
gross_income_w = st.sidebar.number_input("妻の現在年収 (万円)", 0, 5000, 400, step=10)
income_change_rate_w = st.sidebar.slider("妻の年収上昇率 (%/年)", 0.0, 5.0, 1.25, step=0.05)
child_care_reduction_years = st.sidebar.selectbox("育児短時間勤務の期間（年）", [1, 2, 3, 4, 5, 6, 7, 8], index=4)

st.sidebar.header("💼 退職金設定")
retirement_payout_h = st.sidebar.number_input("夫の退職金 (万円)", 0, 5000, 2000, step=100)
retirement_payout_w = st.sidebar.number_input("妻の退職金 (万円)", 0, 5000, 500, step=100)

st.sidebar.header("📈 資産・運用・経済設定")
current_cash = st.sidebar.number_input("現在の現預金 (万円)", 0, 50000, 1000, step=50)
current_investment = st.sidebar.number_input("現在の投資信託 (万円)", 0, 50000, 1300, step=50)
current_stock = st.sidebar.number_input("現在の株式 (万円)", 0, 50000, 130, step=10)
annual_return_rate = st.sidebar.slider("投資信託の想定利回り [標準] (%)", 0.0, 15.0, 4.5, step=0.1)
bearish_return_rate = st.sidebar.slider("投資信託の想定利回り [弱気] (%)", -5.0, 10.0, 1.5, step=0.1)
bullish_return_rate = st.sidebar.slider("投資信託の想定利回り [強気] (%)", 0.0, 20.0, 7.5, step=0.1)
expense_change_rate = st.sidebar.slider("インフレ率（生活費上昇率 %）", 0.0, 5.0, 1.5, step=0.1)
max_cash_limit = st.sidebar.number_input("現預金の保有上限 (万円)", 100, 5000, 1000, step=50)

st.sidebar.header("🛡️ リスク・生活防衛設定")
min_cash_months = st.sidebar.slider("生活防衛資金（生活費の月数分を常に現金確保）", 0, 24, 6)

st.sidebar.header("🏠 住宅・生活費・年間支出設定")
living_expenses_monthly = st.sidebar.number_input("基本生活費 (毎月・万円)", 0, 100, 33, step=1)
housing_expenses_monthly = st.sidebar.number_input("住居費 (毎月・万円)", 0, 50, 15, step=1)
annual_travel_cost = st.sidebar.number_input("年間旅行費 (万円)", 0, 200, 30, step=5)
general_medical_cost = st.sidebar.number_input("年間医療費 (万円)", 0, 50, 5, step=1)
annual_social_cost = st.sidebar.number_input("年間交際費 (万円)", 0, 100, 20, step=5)
regional_house_cost = st.sidebar.number_input("定年時 住宅購入費用 (万円)", 0, 20000, 5000, step=100)
annual_home_maintenance_cost = st.sidebar.number_input("老後の住宅維持費・固定資産税（年・万円）", 0, 300, 50, step=5)
annual_retirement_insurance_cost = st.sidebar.number_input("老後の健康・介護保険等（年・万円）", 0, 300, 60, step=5)
next_year_one_time_expense = st.sidebar.number_input("翌年の臨時支出（万円）", 0, 2000, 200, step=10)

st.sidebar.header("🚗 車・車両費設定")
car_purchase_price = st.sidebar.number_input("車の購入価格 (万円)", 0, 1000, 300, step=50)
car_replacement_cycle = st.sidebar.slider("車の買替サイクル (年)", 5, 20, 10)
car_maintenance_cost = st.sidebar.number_input("車の年間維持費 (万円)", 0, 200, 40, step=5)
migration_medical_cost_multiplier = st.sidebar.slider("老後の医療費増加倍率", 1.0, 10.0, 4.0, step=0.5)

st.sidebar.header("🪦 老後リスク・相続設定")
husband_death_age = st.sidebar.slider("夫の想定死亡年齢", 60, 100, 85)
nursing_care_cost = st.sidebar.number_input("介護一時費用（万円）", 0, 2000, 500, step=50)
funeral_cost = st.sidebar.number_input("葬儀・相続費用（万円）", 0, 1000, 300, step=50)
survivor_pension_ratio = st.sidebar.slider("遺族年金割合（夫の年金に対する%）", 0, 100, 75, step=5)
widow_expense_ratio = st.sidebar.slider("夫死亡後の生活費割合（%）", 50, 100, 70, step=5)

st.sidebar.header("📐 グラフ表示設定")
chart_scale = st.sidebar.slider("グラフの表示倍率", 0.5, 1.0, 1.0, step=0.1)

if st.session_state.pop("scroll_sidebar_to_top", False):
    components.html(
        """
        <script>
            const scrollSidebarToTop = () => {
                try {
                    const parentDocument = window.parent.document;
                    const sidebar = parentDocument.querySelector('[data-testid="stSidebar"]');
                    const sidebarContent = parentDocument.querySelector('[data-testid="stSidebarUserContent"], [data-testid="stSidebarContent"]');
                    const target = sidebarContent || sidebar;
                    if (!target) return;
                    let element = target;
                    while (element && element !== parentDocument.body) {
                        element.scrollTop = 0;
                        element = element.parentElement;
                    }
                    target.scrollIntoView({ block: 'start' });
                } catch (error) {}
            };
            [0, 150, 400, 800].forEach((delay) => setTimeout(scrollSidebarToTop, delay));
        </script>
        """,
        height=0,
    )

living_expenses = living_expenses_monthly * 12
housing_expenses_base = housing_expenses_monthly * 12

# ------------------------------------------
# 計算補助用パラメータと関数
# ------------------------------------------
overtime_hours_per_month = 45
overtime_multiplier = 1.25
child_care_income_reduction_rate = 0.30
stock_return_rate = 1.5
stock_dividend_yield = 2.5
investment_stop_age_h = 60
migration_housing_expenses = 50
housing_increase_on_child = 60
migration_living_expense_ratio = 0.80

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
        base_income_at_41 = 1200.0 / (1 + (1.25 * 45 * 12 / 1920))
        return 532.72 + (age - 29) * ((base_income_at_41 - 532.72) / 12)
    else:
        peak_target_income = 1500.0
        start_income_at_42 = 1100.0
        last_working_age = retirement_age_h - 1
        years_span = max(1, last_working_age - 42)
        current_offset = age - 42
        return start_income_at_42 + current_offset * ((peak_target_income - start_income_at_42) / years_span)

def calculate_husband_gross_income(age):
    base = calculate_husband_base_gross_income(age)
    if base <= 0:
        return 0
    if age < 42:
        hourly_rate = (base * 10000) / 1920
        annual_overtime_pay = hourly_rate * overtime_multiplier * overtime_hours_per_month * 12
        return base + (annual_overtime_pay / 10000)
    else:
        return base

def adjust_pension_for_start_age(pension_at_65, start_age):
    if start_age >= 65:
        return pension_at_65 * (1 + (start_age - 65) * 12 * 0.007)
    return pension_at_65 * (1 - (65 - start_age) * 12 * 0.004)

calculated_pension_h = adjust_pension_for_start_age(pension_at_65_h, pension_start_age_h)
calculated_pension_w = adjust_pension_for_start_age(pension_at_65_w, pension_start_age_w)

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
        else: return 58.30

def get_child_living_expense_addition(c_age, course_type=None):
    if not (0 <= c_age <= 21): return 0
    if c_age <= 3: return 15
    elif c_age <= 11: return 30
    elif c_age <= 17: return 55
    else: return 75.34 if course_type == "ALL_PUBLIC" else 63.15


# ------------------------------------------
# シミュレーション実行エンジン
# ------------------------------------------
def run_simulation(inv_return_rate):
    res = {k: [] for k in [
        "age", "total_wealth", "cash", "investment", "stock", "net_income", "total_expense",
        "annual_balance", "child1", "child2", "child3", "total_child", "cash_ratio",
        "inv_ratio", "stock_ratio", "husband_gross", "wife_gross", "pension_gross",
        "household_gross", "husband_net", "wife_net", "pension_net", "household_net"
    ]}
    
    sim_cash, sim_investment, sim_stock = current_cash, current_investment, current_stock
    asset_depletion_age = None
    
    for i in range(100 - current_age_h + 1):
        age_h = current_age_h + i
        age_w = current_age_w + i
        inflation_factor = (1 + expense_change_rate / 100) ** i
        
        is_husband_alive = age_h <= husband_death_age
        is_death_year = age_h == husband_death_age

        annual_dividend = 0
        if i > 0:
            sim_investment *= (1 + inv_return_rate / 100)
            sim_stock *= (1 + stock_return_rate / 100)
            annual_dividend = (sim_stock * (stock_dividend_yield / 100)) * 0.79685

        # 収入計算
        if is_husband_alive:
            gross_h = calculate_husband_gross_income(age_h) if age_h < retirement_age_h else 0
            net_h = calculate_net_income(gross_h)
        else:
            gross_h, net_h = 0, 0

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
            current_gross_w, net_w = 0, 0

        # 退職金
        extra_retirement_cash = 0
        if is_husband_alive and age_h == retirement_age_h: extra_retirement_cash += retirement_payout_h
        if age_w == retirement_age_w: extra_retirement_cash += retirement_payout_w

        # 年金計算（遺族年金対応）
        base_pension_w = calculated_pension_w * ((1 + pension_indexation_rate / 100) ** i) if age_w >= pension_start_age_w else 0
        base_pension_h = calculated_pension_h * ((1 + pension_indexation_rate / 100) ** i) if age_h >= pension_start_age_h else 0
        
        if is_husband_alive:
            pension_gross_h, pension_gross_w = base_pension_h, base_pension_w
        else:
            pension_gross_h = 0
            # 夫の年金をベースに遺族年金を加算
            husband_base_for_survivor = calculated_pension_h * ((1 + pension_indexation_rate / 100) ** i)
            pension_gross_w = base_pension_w + (husband_base_for_survivor * (survivor_pension_ratio / 100))
            
        current_pension_gross = pension_gross_h + pension_gross_w
        current_pension_net = current_pension_gross

        total_gross = gross_h + current_gross_w + current_pension_gross
        pure_annual_income = net_h + net_w + current_pension_net + annual_dividend

        # 支出計算
        is_migrated = age_h >= retirement_age_h and age_w >= retirement_age_w

        total_child_living_addition = 0
        c1_exp, c2_exp, c3_exp = 0, 0, 0
        if child_count >= 1:
            c1_age = age_h - first_birth_age_h
            total_child_living_addition += get_child_living_expense_addition(c1_age, child_courses.get(1))
            c1_exp = get_child_yearly_expense(c1_age, child_courses.get(1)) * inflation_factor
        if child_count >= 2:
            c2_age = age_h - (first_birth_age_h + birth_interval)
            total_child_living_addition += get_child_living_expense_addition(c2_age, child_courses.get(2))
            c2_exp = get_child_yearly_expense(c2_age, child_courses.get(2)) * inflation_factor
        if child_count >= 3:
            c3_age = age_h - (first_birth_age_h + birth_interval * 2)
            total_child_living_addition += get_child_living_expense_addition(c3_age, child_courses.get(3))
            c3_exp = get_child_yearly_expense(c3_age, child_courses.get(3)) * inflation_factor
            
        total_child_expense = c1_exp + c2_exp + c3_exp

        if not is_migrated:
            current_housing = housing_expenses_base + (housing_increase_on_child if (child_count > 0 and age_h >= first_birth_age_h) else 0)
            base_living_with_children = living_expenses + total_child_living_addition
            
            # 夫死亡後は生活費を圧縮
            if not is_husband_alive:
                base_living_with_children *= (widow_expense_ratio / 100)
                
            annual_expense = (base_living_with_children + current_housing + annual_travel_cost + general_medical_cost + annual_social_cost) * inflation_factor
        else:
            base_expense_fixed = (living_expenses * migration_living_expense_ratio) + migration_housing_expenses + total_annual_car_cost + annual_travel_cost + annual_social_cost
            if not is_husband_alive:
                base_expense_fixed *= (widow_expense_ratio / 100)
                
            annual_expense = (
                base_expense_fixed * (0.90 if age_h >= 75 else 1.0)
                + general_medical_cost * migration_medical_cost_multiplier
                + annual_home_maintenance_cost
                + annual_retirement_insurance_cost
            ) * inflation_factor

        extra_one_time_expense = next_year_one_time_expense if i == 1 else 0
        if is_death_year:
            extra_one_time_expense += (funeral_cost + nursing_care_cost) * inflation_factor

        pure_total_expense = annual_expense + total_child_expense + extra_one_time_expense
        pure_annual_balance = pure_annual_income - pure_total_expense
        sim_cash += pure_annual_balance + extra_retirement_cash

        # 定年時の住宅購入
        if is_husband_alive and age_h == retirement_age_h:
            sim_cash += sim_stock
            sim_stock = 0
            inflated_house_purchase_cost = regional_house_cost * inflation_factor
            needed = inflated_house_purchase_cost - sim_cash
            if needed > 0:
                sale = min(needed, sim_investment)
                sim_investment -= sale
                sim_cash += sale
            sim_cash -= inflated_house_purchase_cost

        # 生活防衛資金（変動型）の確保ルール
        current_min_cash_reserve = ((annual_expense + total_child_expense) / 12) * min_cash_months
        if sim_cash < current_min_cash_reserve:
            shortfall = current_min_cash_reserve - sim_cash
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
        if total_wealth < 0 and asset_depletion_age is None:
            asset_depletion_age = age_h
            
        c_ratio = (sim_cash / total_wealth) * 100 if total_wealth > 0 else 100
        i_ratio = (sim_investment / total_wealth) * 100 if total_wealth > 0 else 0
        s_ratio = (sim_stock / total_wealth) * 100 if total_wealth > 0 else 0

        res["age"].append(age_h)
        res["total_wealth"].append(total_wealth)
        res["cash"].append(sim_cash)
        res["investment"].append(sim_investment)
        res["stock"].append(sim_stock)
        res["net_income"].append(pure_annual_income)
        res["total_expense"].append(pure_total_expense)
        res["annual_balance"].append(pure_annual_balance)
        res["child1"].append(c1_exp)
        res["child2"].append(c2_exp)
        res["child3"].append(c3_exp)
        res["total_child"].append(total_child_expense)
        res["cash_ratio"].append(c_ratio)
        res["inv_ratio"].append(i_ratio)
        res["stock_ratio"].append(s_ratio)
        res["husband_gross"].append(gross_h)
        res["wife_gross"].append(current_gross_w)
        res["pension_gross"].append(current_pension_gross)
        res["household_gross"].append(total_gross)
        res["husband_net"].append(net_h)
        res["wife_net"].append(net_w)
        res["pension_net"].append(current_pension_net)
        res["household_net"].append(pure_annual_income)
        
    return res, asset_depletion_age

# 3パターンのシミュレーション実行
res_std, depletion_age_std = run_simulation(annual_return_rate)
res_bear, _ = run_simulation(bearish_return_rate)
res_bull, _ = run_simulation(bullish_return_rate)


# ------------------------------------------
# メトリクスカードとアラートの表示
# ------------------------------------------
initial_total_wealth = current_cash + current_investment + current_stock
peak_wealth = max(res_std["total_wealth"])

target_age_80 = current_age_h + (80 - current_age_h)
if target_age_80 in res_std["age"]:
    wealth_at_80 = res_std["total_wealth"][res_std["age"].index(target_age_80)]
else:
    wealth_at_80 = res_std["total_wealth"][-1]

if child_count == 0:
    child_info_str = "子供 0人"
else:
    courses_summary = [f"第{n}: {course_labels[child_courses[n]]}" for n in range(1, child_count + 1)]
    child_info_str = f"子供 {child_count}人 (" + ", ".join(courses_summary) + ")"

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">現在の総資産</div><div class="metric-value">{initial_total_wealth:,.0f} 万円</div></div>', unsafe_allow_html=True)
with col2:
    peak_age = res_std["age"][res_std["total_wealth"].index(peak_wealth)]
    st.markdown(f'<div class="metric-card"><div class="metric-title">資産ピーク時（{peak_age}歳）</div><div class="metric-value">{peak_wealth:,.0f} 万円</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">80歳時点の残高 (標準)</div><div class="metric-value">{wealth_at_80:,.0f} 万円</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">家族・進路設定</div><div class="metric-value" style="font-size: 0.9rem; padding-top: 5px;">{child_info_str}</div></div>', unsafe_allow_html=True)

# 枯渇時の詳細アラート計算
if depletion_age_std is not None:
    depletion_idx = res_std["age"].index(depletion_age_std)
    shortfalls = [b for b in res_std["annual_balance"][depletion_idx:] if b < 0]
    avg_shortfall = abs(sum(shortfalls) / len(shortfalls)) if shortfalls else 0
    final_shortfall = abs(res_std["total_wealth"][-1])
    
    st.error(
        f"⚠️ **{depletion_age_std}歳**で総資産がマイナスになる見込みです（標準シナリオ）。\n\n"
        f"資産枯渇後は、年間平均で **約{avg_shortfall:,.0f}万円** の赤字が発生し続けます。\n"
        f"100歳時点での最終的な累計不足額（借入残高）は **約{final_shortfall:,.0f}万円** に達する見込みです。\n\n"
        "➡ 運用利回り、住宅購入費、または固定費の見直しを検討してください。"
    )
else:
    st.success("✅ 標準シナリオでは、100歳まで総資産はマイナスにならない見込みです。")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------
# タブによる情報の整理
# ------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📈 資産・収支シミュレーション", "💰 収入・詳細推移", "👶 子育て費用", "📊 ポートフォリオ"])

with tab1:
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(10 * chart_scale, 11 * chart_scale), sharex=True)
    fig1.patch.set_facecolor("#FFFDF9")
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    # 3パターンの利回り比較
    ax1.plot(res_bull["age"], res_bull["total_wealth"], label=f"総資産 (強気: {bullish_return_rate}%)", color=COLOR_GREEN, linestyle="--", alpha=0.7, linewidth=1.5)
    ax1.plot(res_bear["age"], res_bear["total_wealth"], label=f"総資産 (弱気: {bearish_return_rate}%)", color=COLOR_PURPLE, linestyle="--", alpha=0.7, linewidth=1.5)
    ax1.plot(res_std["age"], res_std["total_wealth"], label=f"総資産 (標準: {annual_return_rate}%)", color=COLOR_PRIMARY, linewidth=3.0, solid_capstyle="round")
    
    ax1.plot(res_std["age"], res_std["cash"], label=f"現預金 (標準推移)", color="#A5B1C2", linestyle=":", linewidth=2.0)
    
    ax1.axvline(retirement_age_h, color="#FF869E", linestyle=":", linewidth=2, label="夫の退職")
    ax1.axvspan(retirement_age_h, 100, color="#F1F2F6", alpha=0.5)
    ax1.set_title("生涯資産シミュレーション (3シナリオ比較)", fontsize=13, fontweight="bold", color=COLOR_DARK, pad=12)
    ax1.set_ylabel("金額（万円）", fontsize=11, color=COLOR_DARK)
    ax1.grid(True, linestyle=":", alpha=0.6, color="#E4E5E9")
    ax1.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor="none")

    ax2.plot(res_std["age"], res_std["net_income"], label="手取り収入（標準）", color=COLOR_SECONDARY, linewidth=2.2)
    ax2.plot(res_std["age"], res_std["total_expense"], label="総支出（標準）", color=COLOR_PRIMARY, linewidth=2.2)
    ax2.plot(res_std["age"], res_std["annual_balance"], label="年間収支", color=COLOR_DARK, linewidth=1.8, linestyle="-.")
    
    ax2.fill_between(res_std["age"], res_std["annual_balance"], 0, where=[b >= 0 for b in res_std["annual_balance"]], color=COLOR_GREEN, alpha=0.2, interpolate=True)
    ax2.fill_between(res_std["age"], res_std["annual_balance"], 0, where=[b < 0 for b in res_std["annual_balance"]], color=COLOR_PRIMARY, alpha=0.2, interpolate=True)
    
    ax2.axhline(0, color="#A5B1C2", linestyle="--", alpha=0.7)
    ax2.axvline(retirement_age_h, color="#FF869E", linestyle=":", linewidth=2)
    ax2.axvspan(retirement_age_h, 100, color="#F1F2F6", alpha=0.5)
    ax2.set_title("年間収入・支出・収支 (標準シナリオ)", fontsize=13, fontweight="bold", color=COLOR_DARK, pad=12)
    ax2.set_xlabel("夫の年齢（歳）", fontsize=11, color=COLOR_DARK)
    ax2.set_ylabel("金額（万円）", fontsize=11, color=COLOR_DARK)
    ax2.grid(True, linestyle=":", alpha=0.6, color="#E4E5E9")
    ax2.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor="none")

    for ax in [ax1, ax2]:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#D1D8E0")
        ax.spines["bottom"].set_color("#D1D8E0")

    plt.tight_layout()
    st.pyplot(fig1, use_container_width=False)

with tab2:
    fig_income, (ax_g, ax_n) = plt.subplots(2, 1, figsize=(10 * chart_scale, 11 * chart_scale), sharex=True)
    fig_income.patch.set_facecolor("#FFFDF9")
    ax_g.set_facecolor("#FFFFFF")
    ax_n.set_facecolor("#FFFFFF")

    ax_g.plot(res_std["age"], res_std["household_gross"], label="世帯年収（額面）", color=COLOR_DARK, linewidth=2.5)
    ax_g.plot(res_std["age"], res_std["husband_gross"], label="夫の給与（額面）", color=COLOR_SECONDARY, linestyle="--", linewidth=2.0)
    ax_g.plot(res_std["age"], res_std["wife_gross"], label="妻の給与（額面）", color=COLOR_PRIMARY, linestyle="--", linewidth=2.0)
    ax_g.plot(res_std["age"], res_std["pension_gross"], label="年金（額面・遺族年金含む）", color=COLOR_PURPLE, linestyle=":", linewidth=2.2)
    
    ax_g.axvline(retirement_age_h, color="#FF869E", linestyle=":", label="夫の退職")
    ax_g.axvspan(retirement_age_h, 100, color="#F1F2F6", alpha=0.5)
    ax_g.set_title("額面収入の推移", fontsize=13, fontweight="bold", color=COLOR_DARK, pad=12)
    ax_g.set_ylabel("額面金額（万円）", fontsize=11, color=COLOR_DARK)
    ax_g.grid(True, linestyle=":", alpha=0.6, color="#E4E5E9")
    ax_g.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", edgecolor="none")

    ax_n.plot(res_std["age"], res_std["household_net"], label="世帯手取り収入", color=COLOR_GREEN, linewidth=2.5)
    ax_n.plot(res_std["age"], res_std["husband_net"], label="夫の手取り給与", color=COLOR_SECONDARY, linestyle="--", linewidth=2.0)
    ax_n.plot(res_std["age"], res_std["wife_net"], label="妻の手取り給与", color=COLOR_PRIMARY, linestyle="--", linewidth=2.0)
    ax_n.plot(res_std["age"], res_std["pension_net"], label="年金（手取り）", color=COLOR_PURPLE, linestyle=":", linewidth=2.2)
    
    ax_n.axvline(retirement_age_h, color="#FF869E", linestyle=":")
    ax_n.axvspan(retirement_age_h, 100, color="#F1F2F6", alpha=0.5)
    ax_n.set_title("手取り収入の推移", fontsize=13, fontweight="bold", color=COLOR_DARK, pad=12)
    ax_n.set_xlabel("夫の年齢（歳）", fontsize=11, color=COLOR_DARK)
    ax_n.set_ylabel("手取り金額（万円）", fontsize=11, color=COLOR_DARK)
    ax_n.grid(True, linestyle=":", alpha=0.6, color="#E4E5E9")
    ax_n.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", edgecolor="none")

    for ax in [ax_g, ax_n]:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#D1D8E0")
        ax.spines["bottom"].set_color("#D1D8E0")

    plt.tight_layout()
    st.pyplot(fig_income, use_container_width=False)

with tab3:
    fig_child, ax3 = plt.subplots(figsize=(10 * chart_scale, 6 * chart_scale))
    fig_child.patch.set_facecolor("#FFFDF9")
    ax3.set_facecolor("#FFFFFF")

    if child_count >= 1: ax3.plot(res_std["age"], res_std["child1"], label="第1子の費用", color=COLOR_SECONDARY, linewidth=2.2)
    if child_count >= 2: ax3.plot(res_std["age"], res_std["child2"], label="第2子の費用", color=COLOR_PURPLE, linewidth=2.2)
    if child_count >= 3: ax3.plot(res_std["age"], res_std["child3"], label="第3子の費用", color=COLOR_GREEN, linewidth=2.2)

    ax3.plot(res_std["age"], res_std["total_child"], label="子ども費用合計", color=COLOR_PRIMARY, linewidth=2.8, linestyle=":")
    ax3.axvline(retirement_age_h, color="#FF869E", linestyle=":")
    ax3.axvspan(retirement_age_h, 100, color="#F1F2F6", alpha=0.5)
    ax3.set_title("子どもの教育費", fontsize=13, fontweight="bold", color=COLOR_DARK, pad=12)
    ax3.set_xlabel("夫の年齢（歳）", fontsize=11, color=COLOR_DARK)
    ax3.set_ylabel("金額（万円）", fontsize=11, color=COLOR_DARK)
    ax3.grid(True, linestyle=":", alpha=0.6, color="#E4E5E9")
    ax3.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor="none")
    ax3.spines["top"].set_visible(False); ax3.spines["right"].set_visible(False)
    ax3.spines["left"].set_color("#D1D8E0"); ax3.spines["bottom"].set_color("#D1D8E0")

    plt.tight_layout()
    st.pyplot(fig_child, use_container_width=False)

with tab4:
    fig_port, ax4 = plt.subplots(figsize=(10 * chart_scale, 6 * chart_scale))
    fig_port.patch.set_facecolor("#FFFDF9")
    ax4.set_facecolor("#FFFFFF")

    ax4.stackplot(
        res_std["age"], res_std["cash_ratio"], res_std["inv_ratio"], res_std["stock_ratio"],
        labels=["現預金（%）", "投資信託（%）", "株式（%）"], colors=["#B8F2E6", "#FFAAA6", "#DFCCF1"], alpha=0.85,
    )
    ax4.axvline(retirement_age_h, color="#FF869E", linestyle=":")
    ax4.axvspan(retirement_age_h, 100, color="#F1F2F6", alpha=0.5)
    ax4.set_title("資産配分比率の推移 (標準)", fontsize=13, fontweight="bold", color=COLOR_DARK, pad=12)
    ax4.set_xlabel("夫の年齢（歳）", fontsize=11, color=COLOR_DARK)
    ax4.set_ylabel("比率（%）", fontsize=11, color=COLOR_DARK)
    ax4.set_ylim(0, 100)
    ax4.grid(True, linestyle=":", alpha=0.6, color="#E4E5E9")
    ax4.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", edgecolor="none")
    ax4.spines["top"].set_visible(False); ax4.spines["right"].set_visible(False)
    ax4.spines["left"].set_color("#D1D8E0"); ax4.spines["bottom"].set_color("#D1D8E0")

    plt.tight_layout()
    st.pyplot(fig_port, use_container_width=False)

# CSVエクスポート機能
st.markdown("---")
st.subheader("📥 シミュレーションデータのダウンロード (標準シナリオ)")
df_export = pd.DataFrame({
    "夫の年齢（歳）": res_std["age"],
    "総資産（万円）": res_std["total_wealth"],
    "現預金（万円）": res_std["cash"],
    "投資信託（万円）": res_std["investment"],
    "株式（万円）": res_std["stock"],
    "手取り収入（万円）": res_std["net_income"],
    "年金額面（万円）": res_std["pension_gross"],
    "総支出（万円）": res_std["total_expense"],
    "年間収支（万円）": res_std["annual_balance"],
    "子ども費用合計（万円）": res_std["total_child"],
})

csv_data = df_export.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="CSV形式で標準シナリオのデータをダウンロード",
    data=csv_data,
    file_name="life_plan_simulation.csv",
    mime="text/csv",
)
