import streamlit as st
import cv2
import numpy as np
from PIL import Image
import os
import datetime

st.set_page_config(page_title="Contact Angle Master", layout="wide")

st.title("💧 接触角測定アプリ (Human-in-the-loop)")
st.markdown("自動計測の結果を、**人間の目で見てスライダーで微調整**できます。")

# --- サイドバー設定 ---
st.sidebar.header("🔧 設定 & 調整")

# 1. 画像アップロード
uploaded_file = st.sidebar.file_uploader("画像をアップロード", type=['png', 'jpg', 'jpeg', 'bmp'])

# 2. パラメータ調整
mode = st.sidebar.radio("モード選択", ["Auto (大津の二値化)", "Manual (手動しきい値)"])

threshold_val = 0
if mode == "Manual (手動しきい値)":
    threshold_val = st.sidebar.slider("しきい値 (Threshold)", 0, 255, 128, help="これより明るい部分を水滴とみなします")

# 3. ノイズ除去・クロップ
blur_strength = st.sidebar.slider("ぼかし強度 (ノイズ除去)", 1, 21, 5, step=2)
crop_bottom = st.sidebar.slider("下の余分な部分をカット (px)", 0, 200, 0, help="反射や基板が邪魔な場合にカットします")

# --- メイン処理 ---
if uploaded_file is not None:
    # 画像読み込み
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_bgr = cv2.imdecode(file_bytes, 1)
    
    # クロップ処理（下の方にある反射などを消す）
    h_img, w_img = img_bgr.shape[:2]
    if crop_bottom > 0:
        img_bgr = img_bgr[0:h_img-crop_bottom, :]
    
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # ぼかし（ノイズ除去）
    blurred = cv2.GaussianBlur(gray, (blur_strength, blur_strength), 0)
    
    # 二値化 (水滴の抽出)
    if mode == "Auto (大津の二値化)":
        ret, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        used_thresh = ret
    else:
        ret, binary = cv2.threshold(blurred, threshold_val, 255, cv2.THRESH_BINARY)
        used_thresh = threshold_val

    # 輪郭抽出
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 結果画像用
    result_img = img_bgr.copy()
    theta_deg = 0.0
    droplet_found = False
    
    if contours:
        # 最大の輪郭を水滴とする
        droplet_contour = max(contours, key=cv2.contourArea)
        
        # あまりに小さいゴミは無視
        if cv2.contourArea(droplet_contour) > 100:
            droplet_found = True
            x, y, w, h = cv2.boundingRect(droplet_contour)
            
            # 接触角計算 (theta/2法)
            r = w / 2
            # 幾何学的にありえない値(h > r*2など)のガードが必要だが、簡易計算
            theta_rad = 2 * np.arctan(h / r)
            theta_deg = np.degrees(theta_rad)
            
            # 描画
            cv2.drawContours(result_img, [droplet_contour], -1, (0, 255, 0), 2) # 輪郭(緑)
            cv2.rectangle(result_img, (x, y), (x + w, y + h), (255, 0, 0), 2)   # 箱(青)
            
            # 中心線
            center_x = x + w // 2
            cv2.line(result_img, (center_x, y), (center_x, y + h), (0, 0, 255), 2) # 高さ(赤)

    # --- 画面表示 ---
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🖼️ 解析画面")
        # OpenCV(BGR) -> RGB変換して表示
        st.image(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        if mode == "Manual (手動しきい値)":
            st.caption(f"現在のしきい値: {used_thresh} (スライダーで調整して輪郭を合わせてください)")
        
        # 二値化画像（AIがどう見ているか）を確認用に出す
        with st.expander("AIの視界（二値化画像）を見る"):
            st.image(binary, caption="白=水滴, 黒=背景", use_container_width=True)

    with col2:
        st.subheader("📊 測定結果")
        if droplet_found:
            st.metric("接触角 (Contact Angle)", f"{theta_deg:.2f} °")
            st.write(f"- 水滴の高さ (h): {h} px")
            st.write(f"- 水滴の幅 (2r): {w} px")
            
            st.success("きれいな輪郭が取れていますか？")
            st.info("💡 ヒント: 影や反射が含まれてしまう場合は、左のサイドバーで「しきい値」や「カット範囲」を調整してください。")
            
            # 保存ボタン
            save_name = f"result_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            if st.button("📸 結果を保存する"):
                cv2.imwrite(save_name, result_img)
                st.toast(f"保存しました: {save_name}")
        else:
            st.warning("水滴を検出できませんでした。しきい値を調整してください。")

else:
    st.info("サイドバーから画像をアップロードしてください。")