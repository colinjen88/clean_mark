import streamlit as st

def render_about():
    st.markdown("""
    <div class="section-header">
        <span class="section-header-icon">ℹ️</span>
        <span class="section-header-text">關於 CleanMark Pro</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-panel">
        <div class="hero-title" style="font-size: 1.4rem; margin-bottom: 0.8rem;">CleanMark Pro v3.2</div>
        <p style="color: #b0bac5 !important; line-height: 1.8; font-size: 0.9rem;">
            CleanMark Pro 是一款專業的浮水印去除工具，使用 OpenCV 的 inpainting 技術，
            能夠有效移除圖片和影片中的可見浮水印。所有處理都在本地完成，無需上傳到雲端，
            保障您的隱私安全。
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">🔧 技術棧</div>
            <div class="feature-desc">
                <strong>UI 框架</strong>：Streamlit<br/>
                <strong>圖像處理</strong>：OpenCV (cv2)<br/>
                <strong>數據處理</strong>：NumPy, Pillow<br/>
                <strong>交互組件</strong>：streamlit-drawable-canvas<br/>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">📋 修復演算法</div>
            <div class="feature-desc">
                <strong>TELEA</strong>：基於快速行進法（Fast Marching Method），
                從區域邊界向內修復，速度快。<br/><br/>
                <strong>Navier-Stokes</strong>：基於流體動力學方程，考慮等照度線延續，
                效果更精細。
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card" style="border-left-color: #f0b429; background: rgba(240, 180, 41, 0.05); border-color: rgba(240, 180, 41, 0.2);">
        <strong style="color: #f0b429 !important;">⚠️ 免責聲明</strong><br/>
        本工具僅用於去除可見浮水印，無法移除不可見的隱寫浮水印（如 SynthID）。<br/>
        請合理使用，尊重版權。
    </div>
    """, unsafe_allow_html=True)
