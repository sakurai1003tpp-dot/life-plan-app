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
