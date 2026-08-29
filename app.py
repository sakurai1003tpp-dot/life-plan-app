import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import streamlit as st

# ------------------------------------------
# グラフの日本語対応・基本設定
# ------------------------------------------
# Streamlit CloudなどのLinux環境で利用可能な日本語フォントを自動検出して設定
import platform
if platform.system() == "Linux":
    # Linux環境（Streamlit Cloud等）向けのフォント設定
    plt.rcParams["font.family"] = "IPAexGothic"
elif platform.system() == "Darwin":
    # Mac向け
    plt.rcParams["font.family"] = "Hiragino Sans"
else:
    # Windows向け
    plt.rcParams["font.family"] = "Meiryo"

plt.rcParams["axes.unicode_minus"] = False  # マイナス記号の文字化け対策
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
st.markdown("---")

# ------------------------------------------
# サイドバー設定パネル
# ------------------------------------------
st.sidebar.header("👨‍👩‍👧‍👦 家族・働き方設定")
current_age_h = st.sidebar.slider("夫の現在の年齢（歳）", 20, 60, 29)
current_age_w = st.sidebar.slider("妻の現在の年齢（歳）", 20, 60, 30)
retirement_age_h = st.sidebar.slider("夫の退職年齢（歳）", 50, 75, 65)
retirement_age_w = st.sidebar.slider("妻の退職年齢（歳）", 50, 75, 55)
pension_start_age_h = st.sidebar.slider("夫の年金受給開始年齢（歳）", 60, 75, 65)
pension_start_age_w = st.sidebar.slider("妻の年金受給開始年齢（歳）", 60, 75, 70)

st.sidebar.header("👶 子ども・育休設定")
child_count = st.sidebar.selectbox("子供の人数", [0, 1, 2, 3], index=1)
first_birth_age_h = st.sidebar.slider("第1子誕生時の夫の年齢", 22, 50, 31)
birth_interval = st.sidebar.slider("きょうだいの年齢差（年）", 1, 5, 3)

maternity_leave_per_child = st.sidebar.selectbox(
    "子1人あたりの産休・育休期間（年）", [1, 2, 3], index=1
)

child_courses = {}
course_labels = {
    "ALL_PUBLIC": "大学まで全公立",
    "PUBLIC_UNIV_RIKEI": "高校まで公立・大学は私立理系",
    "PUBLIC_UNIV_BUNKEI": "高校まで公立・大学は私立文系",
}
if child_count >= 1:
    c1_choice = st.sidebar.selectbox(
        "第1子の進路",
        list(course_labels.keys()),
        format_func=lambda x: course_labels[x],
        index=0,
    )
    child_courses[1] = c1_choice
if child_count >= 2:
    c2_choice = st.sidebar.selectbox(
        "第2子の進路",
        list(course_labels.keys()),
        format_func=lambda x: course_labels[x],
        index=1,
    )
    child_courses[2] = c2_choice
if child_count >= 3:
    c3_choice = st.sidebar.selectbox(
        "第3子の進路",
        list(course_labels.keys()),
        format_func=lambda x: course_labels[x],
        index=2,
    )
    child_courses[3] = c3_choice

st.sidebar.header("💰 収入・働き方設定")
gross_income_w = st.sidebar.number_input(
    "妻の現在年収 (万円)", 0, 5000, 400, step=10
)
income_change_rate_w = st.sidebar.slider(
    "妻の年収上昇率 (%/年)", 0.0, 5.0, 1.25, step=0.05
)
child_care_reduction_years = st.sidebar.selectbox(
    "育児短時間勤務の期間（年）", [1, 2, 3, 4, 5, 6, 7, 8], index=4
)

st.sidebar.header("📈 資産・運用・経済設定")
current_cash = st.sidebar.number_input(
    "現在の現預金 (万円)", 0, 50000, 1000, step=50
)
current_investment = st.sidebar.number_input(
    "現在の投資信託 (万円)", 0, 50000, 1300, step=50
)
current_stock = st.sidebar.number_input("現在の株式 (万円)", 0, 50000, 300, step=50)
annual_return_rate = st.sidebar.slider(
    "投資信託の想定利回り (%)", 0.0, 15.0, 4.0, step=0.1
)
expense_change_rate = st.sidebar.slider(
    "インフレ率（年間生活費の上昇率 %）", 0.0, 5.0, 1.5, step=0.1
)
max_cash_limit = st.sidebar.number_input(
    "現預金の保有上限 (万円)", 100, 5000, 1000, step=50
)

st.sidebar.header("🏠 住宅・生活費・年間支出設定")
living_expenses_monthly = st.sidebar.number_input(
    "基本生活費 (毎月・万円)", 0, 100, 33, step=1
)
housing_expenses_monthly = st.sidebar.number_input(
    "住居費 (毎月・万円)", 0, 50, 15, step=1
)
annual_travel_cost = st.sidebar.number_input(
    "年間旅行費 (万円)", 0, 200, 30, step=5
)
general_medical_cost = st.sidebar.number_input(
    "年間医療費 (万円)", 0, 50, 5, step=1
)
annual_social_cost = st.sidebar.number_input(
    "年間交際費 (万円)", 0, 100, 20, step=5
)
regional_house_cost = st.sidebar.number_input(
    "定年時 住宅購入費用 (万円)", 0, 20000, 5000, step=100
)

living_expenses = living_expenses_monthly * 12
housing_expenses_base = housing_expenses_monthly * 12

# ------------------------------------------
# 計算ロジック
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
    elif age <= 42:
        return 532.72 + (age - 29) * ((1100.0 - 532.72) / 13)
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
        if course_type == "ALL_PUBLIC":
            return 120
        elif course_type == "PUBLIC_UNIV_RIKEI":
            return 205
        elif course_type == "PUBLIC_UNIV_BUNKEI":
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
    age_h = current
