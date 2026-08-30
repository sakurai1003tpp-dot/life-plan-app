# ------------------------------------------
# サイドバー設定パネル（Expanderで整理）
# ------------------------------------------
st.sidebar.markdown("### ⚙️ シミュレーション設定")
if st.sidebar.button("🔄 全設定を初期値に戻す", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# グラフの大きさを変えるバーを独立して配置
chart_scale = st.sidebar.slider("グラフの表示倍率", 0.5, 1.0, 1.0, step=0.1)

st.sidebar.markdown("---")

with st.sidebar.expander("👨‍👩‍👧‍👦 家族・働き方設定", expanded=True):
    current_age_h = st.slider("夫の現在の年齢（歳）", 20, 60, 29)
    current_age_w = st.slider("妻の現在の年齢（歳）", 20, 60, 30)
    retirement_age_h = st.slider("夫の退職年齢（歳）", 50, 75, 65)
    retirement_age_w = st.slider("妻の退職年齢（歳）", 50, 75, 55)
    pension_start_age_h = st.slider("夫の年金受給開始年齢（歳）", 60, 75, 65)
    pension_start_age_w = st.slider("妻の年金受給開始年齢（歳）", 60, 75, 70)

# （中略：他のエキスパンダーやコードはそのまま）

with st.sidebar.expander("🚗 車・老後支出設定"):
    car_purchase_price = st.number_input("車の購入価格 (万円)", 0, 1000, 300, step=10)
    car_maintenance_cost = st.number_input("車の年間維持費 (万円)", 0, 100, 40, step=1)
    car_replacement_cycle = st.slider("車の買替サイクル (年)", 5, 20, 10)
    regional_house_cost = st.number_input("定年時 住宅購入費用 (万円)", 0, 20000, 4500, step=100)
    annual_home_maintenance_cost = st.number_input("老後の住宅維持費（年額・万円）", 0, 300, 50, step=5)
    annual_retirement_insurance_cost = st.number_input("老後の健康保険等（年額・万円）", 0, 300, 60, step=5)
    migration_medical_cost_multiplier = st.slider("老後の医療費倍率", 1.0, 10.0, 4.0, step=0.1)
    next_year_one_time_expense = st.number_input("翌年の臨時支出（万円）", 0, 2000, 200, step=10)
    # chart_scale はサイドバー上部に移動したため、ここからは削除しています
