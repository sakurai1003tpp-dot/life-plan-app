with tab6:
    st.markdown("### 🤖 Gemini AIによる家計診断")
    st.write("現在のパラメータとシミュレーション結果（資産推移・破綻年齢など）をAIに送信し、プロのファイナンシャルプランナーの視点から改善アドバイスを受け取ります。")
    
    if st.button("🚀 AIに家計診断を依頼する", type="primary"):
        with st.spinner("Geminiが家計の診断とアドバイスを生成中..."):
            try:
                # 💡 ここでコード内に直接APIキーを指定します
                client = genai.Client(api_key="AQ.Ab8RN6K-KKtdj7nYhxG2JU8LaGNvHuu2_1UkoxVNHXDfQ8F6QQ")
                
                # AIに渡すためのサマリーデータ作成
                summary_text = f"""
【シミュレーション条件・パラメータ】
- 夫の年齢: {current_age_h}歳（退職: {retirement_age_h}歳）
- 妻の年齢: {current_age_w}歳（退職: {retirement_age_w}歳）
- 子供の人数: {child_count}人
- 現在の資産: 現預金 {current_cash}万円 / 投資信託 {current_investment}万円 / 株式 {current_stock}万円 (合計: {initial_wealth}万円)
- 毎月の基本生活費: {living_expenses_monthly}万円 / 住居費: {housing_expenses_monthly}万円
- 投資信託想定実質利回り: {base_real_return_rate}% / インフレ率: {expense_change_rate}%

【シミュレーション結果サマリー】
- 資産ピーク時: {peak_wealth:,.0f}万円
- 80歳時点の総資産: {wealth_at_80:,.0f}万円
- 資産破綻（マイナス）の有無・年齢: {f"{base_res['depletion_age']}歳で破綻" if base_res['depletion_age'] is not None else "100歳まで破綻なし"}
"""
                prompt = f"""
あなたは優秀なファイナンシャルプランナー（FP）です。以下のライフプランシミュレーション結果を分析し、ユーザーに対して親身かつ具体的で実用的なアドバイス・家計診断を行ってください。

{summary_text}

以下の構成で回答を出力してください：
1. **全体の評価・総評**（この家計の強みと最大の懸念点）
2. **懸念されるリスクへの対策**（破綻リスクや資産配分のバランス、教育費・老後資金について）
3. **具体的なアクションプラン**（今日から実行できる改善提案を2〜3個）
"""
                response = client.models.generate_content(
                    model='gemini-3.7-flash',
                    contents=prompt,
                )
                st.markdown("---")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"APIの呼び出し中にエラーが発生しました: {e}")
