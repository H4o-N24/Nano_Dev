import streamlit as st

st.set_page_config(
    page_title="My Research Tools",
    page_icon="🔬",
    layout="wide"
)

# --- サイドバー：ガス流量計算ツール (ここへ移動！) ---
with st.sidebar:
    st.divider()
    st.markdown("### 🧮 ガス流量計算 (MFC)")
    
    # 入力
    a = st.number_input("メタン流量 (sccm)", min_value=0.0, max_value=50.0, value=10.0, step=0.5)

    # 計算
    b = 50.0 - a    # C2F6流量
    
    # コンバージョンファクター計算
    c = 1.40    # Ar
    d = 0.75    # CH4
    e = 0.25    # C2F6
    
    f = a * c / d   # CH4設定値
    g = b * c / e   # C2F6設定値
    
    # 結果表示
    st.info(f"**CH4設定値:** {f:.2f}")
    st.info(f"**C2F6設定値:** {g:.2f}")
    
    st.caption(f"Total: 50 sccm")
    st.divider()

# --- メイン画面：メニュー ---
st.title("🔬 研究用DXツール集")

st.markdown(
    """
    ### 概要
    実験データの解析から予測までを一貫して行うための統合プラットフォームです。
    左側のサイドバーで**「ガス流量計算」**も行えます。
    """
)

st.subheader("📂 収録ツール一覧")

st.page_link("pages/1_XPS_Analysis.py", label="1. XPS Analysis", icon="📊", help="F-DLC膜のC1sピーク分離と組成解析")
st.page_link("pages/2_Contact_Angle.py", label="2. Contact Angle", icon="💧", help="画像処理による接触角測定")
st.page_link("pages/3_Experiment_Prediction.py", label="3. Experiment Prediction", icon="🤖", help="過去データに基づくAIシミュレーション")

st.divider()