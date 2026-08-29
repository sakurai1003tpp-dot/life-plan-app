import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# システム内の日本語フォントを自動検出して適用する設定
for font in fm.fontManager.ttflist:
    if 'IPA' in font.name or 'Noto Sans CJK' in font.name or 'VL Gothic' in font.name or 'Meiryo' in font.name:
        plt.rcParams['font.family'] = font.name
        break
else:
    # 見つからない場合のフォールバック
    plt.rcParams['font.family'] = 'sans-serif'

plt.rcParams['axes.unicode_minus'] = False
