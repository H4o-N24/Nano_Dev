import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

st.set_page_config(page_title="CH4+C2F6 Prediction", layout="wide")

st.title("🤖 F-DLC 混合ガス成膜シミュレーター")
st.markdown("""
**CH4 (メタン)** と **C2F6 (六フッ化エタン)** の混合比率、および電力・圧力・時間から、
膜の仕上がり（膜厚・接触角・F含有率）を予測します。
""")

# --- 1. サイドバー：実験条件の入力 ---
st.sidebar.header("🎛️ 次の実験条件")

# 混合ガスの流量設定
st.sidebar.subheader("ガス流量設定 (sccm)")
input_ch4 = st.sidebar.slider("CH4 流量", 0, 100, 20, help="炭素源。増やすと成膜速度が上がります。")
input_c2f6 = st.sidebar.slider("C2F6 流量", 0, 100, 5, help="フッ素源。増やすと撥水性が上がりますが、エッチングで膜が減ります。")

# その他のパラメータ
st.sidebar.subheader("プロセス条件")
input_power = st.sidebar.slider("電力 (Power) [W]", 50, 500, 100)
input_pressure = st.sidebar.slider("圧力 (Pressure) [Pa]", 1, 100, 10)
input_time = st.sidebar.slider("成膜時間 (Time) [min]", 1, 180, 60)

# 予測用データフレーム
input_df = pd.DataFrame({
    'CH4_Flow': [input_ch4],
    'C2F6_Flow': [input_c2f6],
    'Power': [input_power],
    'Pressure': [input_pressure],
    'Time': [input_time]
})

# --- 2. 学習データの読み込み ---
st.subheader("1. 学習データ (Excel/CSV) のアップロード")
st.markdown("必要な列名: `CH4_Flow`, `C2F6_Flow`, `Power`, `Pressure`, `Time` (入力) と、`Thickness`, `ContactAngle`, `F_Ratio` (結果)")

uploaded_file = st.file_uploader("ドラッグ＆ドロップしてください", type=['csv', 'xlsx'])

df = None

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.success(f"読み込み成功: {len(df)} 件のデータ")
    except Exception as e:
        st.error(f"エラー: {e}")
else:
    # --- ダミーデータ生成 (混合ガスの特性を反映) ---
    st.info("👆 データがないため、CH4+C2F6の特性を模したダミーデータで動作します。")
    np.random.seed(42)
    n = 100
    
    d_ch4 = np.random.randint(10, 50, n)
    d_c2f6 = np.random.randint(0, 30, n) # C2F6は添加剤的な量
    d_power = np.random.randint(50, 300, n)
    d_press = np.random.randint(5, 50, n)
    d_time = np.random.randint(10, 120, n)
    
    # 物理モデル（デモ用）
    # 膜厚: CH4と時間に比例。C2F6が入るとエッチング効果で減る。
    d_thick = (3.0 * d_ch4 - 1.5 * d_c2f6) * (d_time/60) + np.random.normal(0, 10, n)
    d_thick = np.maximum(d_thick, 0) # マイナスにならないように
    
    # 接触角: C2F6の比率が高いほど上がる。Powerが高いと架橋が進んで少し下がる。
    total_flow = d_ch4 + d_c2f6 + 0.1
    f_ratio_gas = d_c2f6 / total_flow
    d_angle = 70 + 80 * f_ratio_gas - 0.05 * d_power + np.random.normal(0, 3, n)
    
    # F含有率: ガス中のF比率に強く依存
    d_fratio = 5 + 60 * f_ratio_gas + np.random.normal(0, 2, n)
    
    df = pd.DataFrame({
        'CH4_Flow': d_ch4, 'C2F6_Flow': d_c2f6, 
        'Power': d_power, 'Pressure': d_press, 'Time': d_time,
        'Thickness': d_thick, 'ContactAngle': d_angle, 'F_Ratio': d_fratio
    })

with st.expander("学習データの中身を確認"):
    st.dataframe(df)

# --- 3. AIモデル構築 ---

# 説明変数
feature_cols = ['CH4_Flow', 'C2F6_Flow', 'Power', 'Pressure', 'Time']

# 必要な列があるかチェック
if not all(col in df.columns for col in feature_cols):
    st.error(f"エラー: データに必要な列 {feature_cols} が含まれていません。")
    st.stop()

X = df[feature_cols]

# ターゲット設定
targets = {
    '膜厚 (Thickness) [nm]': 'Thickness',
    '接触角 (Angle) [deg]': 'ContactAngle',
    'F含有率 (F%) [at%]': 'F_Ratio'
}

# --- 4. 予測と表示 ---
cols = st.columns(3)

for i, (label, col_name) in enumerate(targets.items()):
    if col_name in df.columns:
        y = df[col_name]
        
        # モデル学習
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # 予測
        pred = model.predict(input_df[feature_cols])[0]
        r2 = r2_score(y, model.predict(X))
        
        with cols[i]:
            st.metric(label, f"{pred:.1f}")
            st.caption(f"精度 R²: {r2:.2f}")
            
            # 重要度グラフ
            importances = model.feature_importances_
            fig, ax = plt.subplots(figsize=(4, 2.5))
            ax.barh(feature_cols, importances, color='teal')
            ax.set_title("パラメータ重要度")
            st.pyplot(fig)

# --- 5. 混合比シミュレーション ---
st.write("---")
st.subheader("📊 混合比による変化のシミュレーション")
st.markdown("CH4を固定し、**C2F6の流量だけを増やしていった場合**の変化をプロットします。")

# シミュレーション用データの作成
sim_c2f6 = np.linspace(0, 50, 50) # C2F6を0~50まで振る
sim_df = pd.DataFrame({
    'CH4_Flow': input_ch4,
    'C2F6_Flow': sim_c2f6,
    'Power': input_power,
    'Pressure': input_pressure,
    'Time': input_time
})

# 3つのターゲットを予測
fig2, ax2 = plt.subplots(figsize=(10, 5))

# 膜厚 (左軸)
y_thick_pred = RandomForestRegressor(n_estimators=100).fit(X, df['Thickness']).predict(sim_df)
ax2.plot(sim_c2f6, y_thick_pred, color='blue', label='Thickness', linewidth=2)
ax2.set_ylabel('Thickness [nm]', color='blue', fontsize=12)
ax2.set_xlabel('C2F6 Flow [sccm]', fontsize=12)
ax2.tick_params(axis='y', labelcolor='blue')

# 接触角 (右軸)
ax3 = ax2.twinx()
y_angle_pred = RandomForestRegressor(n_estimators=100).fit(X, df['ContactAngle']).predict(sim_df)
ax3.plot(sim_c2f6, y_angle_pred, color='red', label='Contact Angle', linewidth=2, linestyle='--')
ax3.set_ylabel('Contact Angle [deg]', color='red', fontsize=12)
ax3.tick_params(axis='y', labelcolor='red')

plt.title(f"Simulation: CH4 fixed at {input_ch4} sccm")
st.pyplot(fig2)

st.info("💡 ヒント: C2F6を増やすと接触角（赤線）は上がりますが、エッチング効果で膜厚（青線）が減るトレードオフが見えますか？")