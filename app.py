import pandas as pd

class FinancialSimulation:
    def __init__(self, config: dict):
        """
        シミュレーション初期化設定
        """
        self.config = config
        
        # 税率設定
        self.TAX_RATE_TAXABLE = 0.20315  # 特定口座の税率（所得税15.315% + 住民税5%）
        
        # 新NISA制度上限設定
        self.NISA_ANNUAL_LIMIT = 3_600_000   # 年間投資枠（つみたて120万 + 成長240万）
        self.NISA_LIFETIME_LIMIT = 18_000_000 # 生涯投資枠上限

    # ==========================================
    # 1. 手取り収入計算モジュール（精緻化）
    # ==========================================
    
    @staticmethod
    def calculate_salary_net_income(gross_income: float) -> float:
        """
        給与所得の手取り額計算（超過累進税率・社会保険料上限・給与所得控除を考慮）
        """
        if gross_income <= 0:
            return 0.0

        # ① 給与所得控除の計算
        if gross_income <= 1_625_000:
            kyuyo_koshu = 550_000
        elif gross_income <= 1_800_000:
            kyuyo_koshu = gross_income * 0.40 - 100_000
        elif gross_income <= 3_600_000:
            kyuyo_koshu = gross_income * 0.30 - 80_000
        elif gross_income <= 6_600_000:
            kyuyo_koshu = gross_income * 0.20 + 280_000
        elif gross_income <= 8_500_000:
            kyuyo_koshu = gross_income * 0.10 + 940_000
        else:
            kyuyo_koshu = 1_950_000  # 上限控除額

        employment_income = max(0.0, gross_income - kyuyo_koshu)

        # ② 社会保険料の計算（健康保険・厚生年金・雇用保険：目安約15%、上限を設定）
        # 標準報酬月額上限（厚生年金・健康保険の年間上限額相当でキャップ設定）
        shakai_hoken = min(gross_income * 0.15, 1_800_000)

        # ③ 課税所得の計算（基礎控除 48万円）
        basic_deduction = 480_000
        taxable_income = max(0.0, employment_income - shakai_hoken - basic_deduction)

        # ④ 所得税の計算（超過累進税率 + 復興特別所得税2.1%）
        if taxable_income <= 1_950_000:
            income_tax = taxable_income * 0.05
        elif taxable_income <= 3_300_000:
            income_tax = taxable_income * 0.10 - 97_500
        elif taxable_income <= 6_950_000:
            income_tax = taxable_income * 0.20 - 427_500
        elif taxable_income <= 9_000_000:
            income_tax = taxable_income * 0.23 - 636_000
        elif taxable_income <= 18_000_000:
            income_tax = taxable_income * 0.33 - 1_536_000
        elif taxable_income <= 40_000_000:
            income_tax = taxable_income * 0.40 - 2_796_000
        else:
            income_tax = taxable_income * 0.45 - 4_796_000

        income_tax *= 1.021  # 復興特別所得税

        # ⑤ 住民税の計算（標準税率10%）
        resident_tax = max(0.0, taxable_income * 0.10)

        # 手取り額 = 額面 - 社会保険料 - 所得税 - 住民税
        net_income = gross_income - shakai_hoken - income_tax - resident_tax
        return max(0.0, net_income)

    @staticmethod
    def calculate_pension_net_income(gross_pension: float, age: int) -> float:
        """
        公的年金等の手取り額計算（公的年金等控除・国保・介護保険料を考慮）
        """
        if gross_pension <= 0:
            return 0.0

        # ① 公的年金等控除の計算（65歳以上を想定）
        if age >= 65:
            if gross_pension <= 1_100_000:
                pension_koshu = gross_pension
            elif gross_pension <= 3_300_000:
                pension_koshu = 1_100_000
            elif gross_pension <= 4_100_000:
                pension_koshu = gross_pension * 0.25 + 275_000
            elif gross_pension <= 7_700_000:
                pension_koshu = gross_pension * 0.15 + 685_000
            elif gross_pension <= 10_000_000:
                pension_koshu = gross_pension * 0.05 + 1_455_000
            else:
                pension_koshu = 1_955_000
        else:
            # 65歳未満の場合
            if gross_pension <= 600_000:
                pension_koshu = gross_pension
            elif gross_pension <= 1_300_000:
                pension_koshu = 600_000
            elif gross_pension <= 4_100_000:
                pension_koshu = gross_pension * 0.25 + 275_000
            else:
                pension_koshu = 1_955_000

        pension_income = max(0.0, gross_pension - pension_koshu)

        # ② 国民健康保険料および介護保険料（概算：約10%）
        social_insurance = gross_pension * 0.10

        # ③ 課税所得の計算（基礎控除48万円）
        basic_deduction = 480_000
        taxable_income = max(0.0, pension_income - social_insurance - basic_deduction)

        # ④ 所得税・住民税の計算
        income_tax = (taxable_income * 0.05) * 1.021 if taxable_income > 0 else 0.0
        resident_tax = (taxable_income * 0.10) if taxable_income > 0 else 0.0

        net_pension = gross_pension - social_insurance - income_tax - resident_tax
        return max(0.0, net_pension)

    # ==========================================
    # 2. 夫の年収計算（ベースアップ・インフレ連動）
    # ==========================================
    
    def calculate_husband_gross_income(self, age: int, year_index: int) -> float:
        """
        夫の年齢別ベース年収にインフレ（ベースアップ率）を掛け合わせて額面年収を算出
        """
        # 年齢別ベース年収テーブル（退職金・再雇用考慮）
        if age < 30:
            base_gross = 4_500_000
        elif age < 35:
            base_gross = 5_500_000
        elif age < 40:
            base_gross = 6_500_000
        elif age < 45:
            base_gross = 7_500_000
        elif age < 50:
            base_gross = 8_200_000
        elif age < 55:
            base_gross = 8_800_000
        elif age < 60:
            base_gross = 9_000_000
        elif age < 65:
            base_gross = 5_000_000  # 60〜64歳：役職定年・再雇用
        elif age < 70:
            base_gross = 2_000_000  # 65〜69歳：継続雇用/パート
        else:
            base_gross = 0          # 完全退職（年金生活へ）

        # インフレ・ベースアップ率の適用
        wage_growth_rate = self.config.get("wage_growth_rate", self.config["expense_change_rate"])
        inflation_factor = (1.0 + wage_growth_rate) ** year_index

        return base_gross * inflation_factor

    # ==========================================
    # 3. シミュレーション実行メインロジック
    # ==========================================
    
    def run_simulation(self) -> pd.DataFrame:
        c = self.config

        # 初期資産状態
        cash_balance = c["initial_cash"]
        taxable_asset = c["initial_taxable_asset"]
        nisa_asset = c["initial_nisa_asset"]
        nisa_cum_principal = c["initial_nisa_asset"]  # NISA累計投資額（上限1,800万管理用）

        results = []

        for year_idx in range(c["simulation_years"]):
            current_year = c["start_year"] + year_idx
            husband_age = c["husband_start_age"] + year_idx
            wife_age = c["wife_start_age"] + year_idx

            # ----------------------------------
            # A. 収入計算（給与 vs 年金）
            # ----------------------------------
            # 夫の収入
            if husband_age < c["pension_start_age"]:
                h_gross = self.calculate_husband_gross_income(husband_age, year_idx)
                h_net = self.calculate_salary_net_income(h_gross)
            else:
                h_gross = c["husband_pension_gross"] * ((1 + c["expense_change_rate"]) ** year_idx)
                h_net = self.calculate_pension_net_income(h_gross, husband_age)

            # 妻の収入
            if wife_age < c["pension_start_age"]:
                w_gross = c["wife_base_gross_income"] * ((1 + c["income_change_rate_w"]) ** year_idx)
                w_net = self.calculate_salary_net_income(w_gross)
            else:
                w_gross = c["wife_pension_gross"] * ((1 + c["expense_change_rate"]) ** year_idx)
                w_net = self.calculate_pension_net_income(w_gross, wife_age)

            total_net_income = h_net + w_net

            # ----------------------------------
            # B. 支出計算（インフレ連動）
            # ----------------------------------
            current_living_expense = c["base_annual_expense"] * ((1 + c["expense_change_rate"]) ** year_idx)

            # ライフイベント等の特別支出（学費・住宅リフォーム等）
            special_expense = c.get("special_expenses", {}).get(year_idx, 0)
            total_expense = current_living_expense + special_expense

            # ----------------------------------
            # C. 単年度収支（キャッシュフロー）
            # ----------------------------------
            net_cashflow = total_net_income - total_expense

            # ----------------------------------
            # D. 資産運用・NISA振分け処理
            # ----------------------------------
            # 1. 既存運用資産の利回り・配当金計算
            # 特定口座の配当・運用益（課税 20.315% 適用）
            taxable_return = taxable_asset * c["investment_yield"] * (1.0 - self.TAX_RATE_TAXABLE)
            taxable_asset += taxable_return

            # NISA口座の配当・運用益（非課税 1.0 適用）
            nisa_return = nisa_asset * c["investment_yield"] * 1.0
            nisa_asset += nisa_return

            # 2. 余剰資金の投資・または不足金の取崩し処理
            if net_cashflow > 0:
                # 黒字の場合：まず生活防衛資金キャッシュに一定残し、残りを投資へ
                cash_balance += net_cashflow
                
                # キャッシュが目標保有額を超過した場合、超えた分を投資へ
                target_cash = current_living_expense * 0.5  # 半年分の生活費を現金保持
                if cash_balance > target_cash:
                    surplus_to_invest = cash_balance - target_cash
                    cash_balance = target_cash

                    # NISA枠への優先投資（年間360万 & 生涯1800万制限）
                    nisa_room_annual = self.NISA_ANNUAL_LIMIT
                    nisa_room_lifetime = max(0.0, self.NISA_LIFETIME_LIMIT - nisa_cum_principal)
                    nisa_investable = min(surplus_to_invest, nisa_room_annual, nisa_room_lifetime)

                    if nisa_investable > 0:
                        nisa_asset += nisa_investable
                        nisa_cum_principal += nisa_investable
                        surplus_to_invest -= nisa_investable

                    # NISA枠から溢れた分は特定口座へ
                    if surplus_to_invest > 0:
                        taxable_asset += surplus_to_invest

            else:
                # 赤字の場合：現金 → 特定口座 → NISA口座の順で崩す
                deficit = abs(net_cashflow)

                # ① 現金から取崩し
                withdraw_cash = min(cash_balance, deficit)
                cash_balance -= withdraw_cash
                deficit -= withdraw_cash

                # ② 特定口座から取崩し（取崩し時に運用益部分に対する課税を考慮）
                if deficit > 0 and taxable_asset > 0:
                    # 簡略化モデル：特定口座資産の取崩し（元本比率約70%と仮定し、利益30%分に課税）
                    effective_tax_on_withdrawal = 0.30 * self.TAX_RATE_TAXABLE
                    net_withdrawal_factor = 1.0 - effective_tax_on_withdrawal

                    withdraw_taxable_needed = deficit / net_withdrawal_factor
                    actual_withdraw_taxable = min(taxable_asset, withdraw_taxable_needed)
                    
                    taxable_asset -= actual_withdraw_taxable
                    deficit -= actual_withdraw_taxable * net_withdrawal_factor

                # ③ NISA口座から取崩し（非課税）
                if deficit > 0 and nisa_asset > 0:
                    withdraw_nisa = min(nisa_asset, deficit)
                    nisa_asset -= withdraw_nisa
                    deficit -= withdraw_nisa

            # 総資産
            total_assets = cash_balance + taxable_asset + nisa_asset

            # レコード保存
            results.append({
                "年": current_year,
                "夫年齢": husband_age,
                "妻年齢": wife_age,
                "夫額面年収": round(h_gross),
                "夫手取り": round(h_net),
                "妻額面年収": round(w_gross),
                "妻手取り": round(w_net),
                "世帯手取り合計": round(total_net_income),
                "年間支出": round(total_expense),
                "単年度収支": round(net_cashflow),
                "現金残高": round(cash_balance),
                "特定口座資産": round(taxable_asset),
                "NISA口座資産": round(nisa_asset),
                "NISA累計元本": round(nisa_cum_principal),
                "総資産額": round(total_assets)
            })

        return pd.DataFrame(results)


# ==========================================
# 4. 実行サンプルコード
# ==========================================
if __name__ == "__main__":
    # シミュレーションのパラメータ設定
    config_data = {
        "start_year": 2026,
        "simulation_years": 40,
        
        # 家族構成
        "husband_start_age": 35,
        "wife_start_age": 33,
        "pension_start_age": 65,
        
        # 夫・妻の収入条件
        "wage_growth_rate": 0.014,        # 夫のベースアップ率/賃金上昇率（1.4%）
        "wife_base_gross_income": 2_000_000, # 妻の現在の額面年収
        "income_change_rate_w": 0.010,    # 妻の年収昇給率（1.0%）
        
        # 老後年金想定（額面）
        "husband_pension_gross": 2_200_000, # 夫の公的年金（年間220万）
        "wife_pension_gross": 1_100_000,    # 妻の公的年金（年間110万）
        
        # 支出設定
        "base_annual_expense": 4_800_000,  # 基本年間生活費（480万円）
        "expense_change_rate": 0.014,      # インフレ率（1.4%）
        "special_expenses": {               # イベン支出（経過年数: 金額）
            3: 1_500_000,  # 3年後：車買い替え
            10: 5_000_000, # 10年後：大学学費
            20: 2_000_000  # 20年後：リフォーム
        },
        
        # 初期資産および運用条件
        "initial_cash": 3_000_000,          # 初期現金
        "initial_taxable_asset": 2_000_000,  # 初期特定口座資産
        "initial_nisa_asset": 1_000_000,     # 初期NISA資産
        "investment_yield": 0.04             # 運用想定利回り（年率4%）
    }

    # シミュレーションの実行
    sim = FinancialSimulation(config_data)
    df_result = sim.run_simulation()

    # 結果表示（主要項目の抜粋）
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df_result[["年", "夫年齢", "夫額面年収", "世帯手取り合計", "年間支出", "単年度収支", "特定口座資産", "NISA口座資産", "総資産額"]].head(10))
