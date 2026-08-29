import pandas as pd
import streamlit as st

# ------------------------------------------
# 画面設定とカスタムスタイル
# ------------------------------------------
st.set_page_config(page_title="ライフプラン・シミュレーション", layout="wide")

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

st.title("📊 ライフプラン・シミュレーション（完全版）")
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

st.sidebar.header("💰 収入・働き方設定")
gross_income_h_start = st.sidebar.number_input(
    "夫の現在年収 (万円)", 0, 5000, 720, step=10
)
gross_income_w = st.sidebar.number_input(
    "妻の現在年収 (万円)", 0, 5000, 400, step=10
)
income_change_rate_w = st.sidebar.slider(
    "妻の年収上昇率 (%/年)", 0.0, 5.0, 1.25, step=0.05
)

st.sidebar.header("📈 資産・運用設定")
current_cash = st.sidebar.number_input(
    "現在の現預金 (万円)", 0, 50000, 1000, step=50
)
current_investment = st.sidebar.number_input(
    "現在の投資信託 (万円)", 0, 50000, 1300, step=50
)
current_stock = st.sidebar.number_input("現在の株式 (万円)", 0, 50000, 300, step=50)
annual_return_rate = st.sidebar.slider(
    "投資信託の想定利回り (%)", 0.0, 10.0, 4.0, step=0.1
)

st.sidebar.header("🏠 住宅・生活費設定")
living_expenses = st.sidebar.number_input(
    "基本生活費 (年間・万円)", 0, 2000, 400, step=10
)
regional_house_cost = st.sidebar.number_input(
    "住宅購入費用 (万円・一時支出)", 0, 20000, 5000, step=100
)
house_purchase_age_h = st.sidebar.slider("住宅購入時の夫の年齢", 20, 80, 35)

# ------------------------------------------
# シミュレーション計算処理
# ------------------------------------------
max_age = 100
years_to_simulate = max_age - current_age_h

ages_h = []
total_assets = []
cash_list = []
investment_list = []
stock_list = []
incomes = []
expenses = []

cash = current_cash
investment = current_investment
stock = current_stock

for i in range(years_to_simulate + 1):
  age_h = current_age_h + i
  age_w = current_age_w + i

  if age_h > max_age:
    break

  ages_h.append(age_h)

  # 収入計算
  inc_h = (
      gross_income_h_start if age_h < retirement_age_h else 200
  )  # 退職後再雇用等
  inc_w = (
      gross_income_w * ((1 + income_change_rate_w / 100) ** i)
      if age_w < retirement_age_w
      else 100
  )

  if age_h >= pension_start_age_h:
    inc_h += 150  # 年金想定
  if age_w >= pension_start_age_w:
    inc_w += 120  # 年金想定

  total_inc = inc_h + inc_w
  incomes.append(total_inc)

  # 支出計算
  exp = living_expenses
  if age_h == house_purchase_age_h:
    exp += regional_house_cost
  expenses.append(exp)

  # 資産運用・増減
  if i > 0:
    investment *= 1 + annual_return_rate / 100
    net_cash_flow = total_inc - exp
    cash += net_cash_flow

  total_assets.append(cash + investment + stock)
  cash_list.append(cash)
  investment_list.append(investment)
  stock_list.append(stock)

# ------------------------------------------
# データフレームの作成（Streamlit標準描画用）
# ------------------------------------------
df_assets = pd.DataFrame(
    {
        "夫の年齢": ages_h,
        "現預金": cash_list,
        "投資信託": investment_list,
        "株式": stock_list,
    }
).set_index("夫の年齢")

df_cashflow = pd.DataFrame(
    {"夫の年齢": ages_h, "年間収入": incomes, "年間支出": expenses}
).set_index("夫の年齢")

# ------------------------------------------
# 画面への描画（Streamlitネイティブ機能で文字化けゼロ）
# ------------------------------------------
st.subheader("📈 総資産の推移")
st.area_chart(df_assets)

st.subheader("💰 年間収入と支出の推移")
st.line_chart(df_cashflow)

st.subheader("🥧 最終資産バランス（100歳時点）")
df_pie = pd.DataFrame(
    {
        "資産種類": ["現預金", "投資信託", "株式"],
        "金額": [
            max(0, cash),
            max(0, investment),
            max(0, stock),
        ],
    }
).set_index("資産種類")
st.bar_chart(df_pie)

# CSVエクスポート
st.markdown("---")
st.subheader("📥 シミュレーションデータのダウンロード")
df_export = pd.DataFrame(
    {
        "夫の年齢": ages_h,
        "総資産": total_assets,
        "現預金": cash_list,
        "投資信託": investment_list,
        "株式": stock_list,
        "年間収入": incomes,
        "年間支出": expenses,
    }
)
st.download_button(
    label="CSV形式でダウンロード",
    data=df_export.to_csv(index=False).encode("utf-8"),
    file_name="life_plan.csv",
    mime="text/csv",
)
