import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import warnings

# ページ設定（タイトルやレイアウト）
st.set_page_config(page_title="F-DLC XPS Analyzer", layout="wide")
st.title("🧪 F-DLC XPS 自動解析アプリ")
st.markdown("XPSファイル (`.xps`, `.csv`, `.txt`) をアップロードすると、**C1sピーク分離**と**結合状態の割合**を自動算出します。")

# サイドバー（設定用）
st.sidebar.header("解析設定")
show_raw_data = st.sidebar.checkbox("生データを表示する", value=False)

# --- 関数定義（いつものロジック） ---
def gaussian(x, amp, center, width):
    return amp * np.exp(-(x - center)**2 / (2 * width**2))

def model_func(x, a1, c1, w1, a2, c2, w2, a3, c3, w3, slope, intercept):
    return gaussian(x, a1, c1, w1) + gaussian(x, a2, c2, w2) + gaussian(x, a3, c3, w3) + slope * x + intercept

# --- メイン処理 ---
# ファイルアップローダー
uploaded_file = st.file_uploader("ファイルをここにドラッグ＆ドロップしてください", type=['xps', 'csv', 'txt', 'mod'])

if uploaded_file is not None:
    st.success(f"読み込み中: {uploaded_file.name}")

    try:
        # 1. ヘッダー行を探す（ストリーム処理）
        # Streamlitのアップロードファイルはバイナリなのでデコードして読む
        content = uploaded_file.getvalue().decode('utf-8', errors='ignore').splitlines()
        target_header_row = -1
        
        for i, line in enumerate(content[:50]): # 最初の50行を探索
            if "Binding Energy" in line:
                target_header_row = i
                break
        
        if target_header_row == -1:
            st.error("エラー: データ内に 'Binding Energy' の列が見つかりませんでした。")
            st.stop()

        # 2. データ読み込み
        # ファイルポインタを先頭に戻してからPandasで読む
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, header=target_header_row, sep='\t', engine='python', on_bad_lines='skip')
        
        # 列名の特定
        try:
            col_be = [c for c in df.columns if "Binding" in str(c)][0]
            col_int = [c for c in df.columns if "Intensity" in str(c)][0]
        except IndexError:
            st.error("エラー: 列名（Binding Energy / Intensity）が特定できませんでした。")
            st.stop()

        # 3. データ整形
        x_raw = pd.to_numeric(df[col_be], errors='coerce').values
        y_raw = pd.to_numeric(df[col_int], errors='coerce').values
        mask_nan = ~np.isnan(x_raw) & ~np.isnan(y_raw)
        x_raw, y_raw = x_raw[mask_nan], y_raw[mask_nan]

        # C1s領域切り出し
        mask = (x_raw >= 280) & (x_raw <= 296)
        x_data = x_raw[mask]
        y_data = y_raw[mask]

        if len(x_data) < 5:
            st.error("エラー: C1s領域 (280-296eV) のデータが含まれていません。")
            st.stop()

        # 4. フィッティング実行
        y_max = np.max(y_data)
        initial_guess = [
            y_max, 284.5, 1.0,  # C-C
            y_max*0.3, 287.0, 1.0,  # C-F
            y_max*0.1, 290.0, 1.0,  # C-F2
            0, np.min(y_data)   # BG
        ]
        
        bounds = (
            [0, 283.5, 0.5, 0, 286.0, 0.5, 0, 289.0, 0.5, -np.inf, -np.inf],
            [np.inf, 285.5, 2.0, np.inf, 288.5, 2.0, np.inf, 292.0, 2.0, np.inf, np.inf]
        )

        try:
            popt, _ = curve_fit(model_func, x_data, y_data, p0=initial_guess, bounds=bounds, maxfev=10000)
        except:
            st.warning("制約付きフィッティングに失敗しました。制約なしで再試行します。")
            popt, _ = curve_fit(model_func, x_data, y_data, p0=initial_guess, maxfev=10000)

        # 5. 結果計算
        fit_y = model_func(x_data, *popt)
        bg_y = popt[9] * x_data + popt[10]
        
        # 面積比率
        area1 = popt[0] * popt[2]
        area2 = popt[3] * popt[5]
        area3 = popt[6] * popt[8]
        total_area = area1 + area2 + area3
        r1, r2, r3 = area1/total_area*100, area2/total_area*100, area3/total_area*100

        # --- 表示パート ---
        
        # 画面を2分割 (左: 数値, 右: グラフ)
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("📊 解析結果")
            st.info(f"ファイル名: {uploaded_file.name}")
            
            # メトリクス表示（大きく表示）
            st.metric("C-C / C-H (284.5eV)", f"{r1:.1f} %")
            st.metric("C-F (287.0eV)",       f"{r2:.1f} %")
            st.metric("C-F2 (290.0eV)",      f"{r3:.1f} %")
            
            # 生データの確認
            if show_raw_data:
                st.write("元データプレビュー:")
                st.dataframe(df.head())

        with col2:
            st.subheader("📈 フィッティンググラフ")
            
            # グラフ描画 (Matplotlib)
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.scatter(x_data, y_data, s=20, facecolors='none', edgecolors='gray', label='Raw Data', alpha=0.6)
            ax.plot(x_data, fit_y, color='red', linewidth=2, label='Total Fit')
            
            # 塗りつぶしプロット
            peak1_y = gaussian(x_data, *popt[0:3]) + bg_y
            peak2_y = gaussian(x_data, *popt[3:6]) + bg_y
            peak3_y = gaussian(x_data, *popt[6:9]) + bg_y
            
            ax.fill_between(x_data, bg_y, peak1_y, color='blue', alpha=0.2, label='C-C')
            ax.plot(x_data, peak1_y, '--', color='blue')
            
            ax.fill_between(x_data, bg_y, peak2_y, color='green', alpha=0.2, label='C-F')
            ax.plot(x_data, peak2_y, '--', color='green')
            
            ax.fill_between(x_data, bg_y, peak3_y, color='orange', alpha=0.2, label='C-F2')
            ax.plot(x_data, peak3_y, '--', color='orange')
            
            ax.plot(x_data, bg_y, ':', color='black', label='BG')
            
            ax.invert_xaxis()
            ax.set_xlabel("Binding Energy (eV)")
            ax.set_ylabel("Intensity")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Streamlit上にグラフを表示
            st.pyplot(fig)

    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {e}")

else:
    st.info("👆 上記のエリアにXPSファイルをアップロードしてください。")