import streamlit as st

st.set_page_config(
    page_title="My Research Tools",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 研究用DXツール集")

st.markdown(
    """
    ### 概要
    実験データの解析から予測までを一貫して行うための統合プラットフォームです。
    以下のメニュー、または左側のサイドバーからツールを選択してください。
    """
)

st.divider() # 仕切り線

st.subheader("📂 収録ツール一覧")

# 1. XPS解析へのリンク
st.page_link("pages/1_XPS_Analysis.py", label="1. XPS Analysis", icon="📊", help="F-DLC膜のC1sピーク分離と組成解析を行います")

# 2. 接触角測定へのリンク
st.page_link("pages/2_Contact_Angle.py", label="2. Contact Angle", icon="💧", help="画像処理による接触角測定 (Human-in-the-loop)を行います")

# 3. AI予測へのリンク（今回追加！）
st.page_link("pages/3_Experiment_Prediction.py", label="3. Experiment Prediction", icon="🤖", help="過去データに基づくAIシミュレーションを行います")

st.divider()

st.info("👈 左のサイドバーからも移動できます")