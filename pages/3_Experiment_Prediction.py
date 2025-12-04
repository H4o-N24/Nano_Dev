import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI Prediction", layout="wide")
st.title("3. 実験結果予測AI")

# ダミーデータ生成
np.random.seed(42)
df = pd.DataFrame({
    'Power': np.random.randint(50, 250, 50),
    'Pressure': np.random.randint(5, 30, 50),
    'Flow': np.random.randint(5, 40, 50),
    'Time': np.random.randint(10, 90, 50)
})
df['ContactAngle'] = 50 + 1.5*df['Flow'] - 0.1*df['Power'] + np.random.normal(0, 5, 50)

st.sidebar.header("条件入力")
power = st.sidebar.slider("電力 (W)", 50, 300, 100)
flow = st.sidebar.slider("ガス流量 (sccm)", 0, 50, 20)
pressure = st.sidebar.slider("圧力 (Pa)", 5, 50, 10)
time = st.sidebar.slider("時間 (min)", 10, 120, 60)

# 学習
model = RandomForestRegressor(n_estimators=100)
X = df[['Power', 'Pressure', 'Flow', 'Time']]
y = df['ContactAngle']
model.fit(X, y)

pred = model.predict([[power, pressure, flow, time]])[0]

c1, c2 = st.columns(2)
c1.metric("予測接触角", f"{pred:.1f} °")
c2.bar_chart(pd.DataFrame({'Importance': model.feature_importances_}, index=X.columns))