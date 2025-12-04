import streamlit as st

st.set_page_config(
    page_title="My Research Tools",
    page_icon="🔬",
)

st.write("# 🔬 研究用DXツール集")

st.markdown(
    """
    実験データの解析ツールを統合したポータルです。
    左側のサイドバーから使用したいツールを選択してください。

    ### 収録ツール
    - **XPS Analysis**: F-DLC膜のC1sピーク分離と組成解析
    - **Contact Angle**: 水滴画像からの接触角測定 (θ/2法)
    """
)