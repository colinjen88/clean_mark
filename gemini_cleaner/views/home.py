import streamlit as st
from utils.ui import render_hero, render_step_flow

def render_home():
    render_hero()

    # Feature cards — Streamlit columns handle responsive automatically
    cols = st.columns(3)

    with cols[0]:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🖼️</span>
            <div class="feature-title">智能圖片修復</div>
            <div class="feature-desc">
                上傳圖片，框選浮水印區域，一鍵去除。支持多區域選取和即時預覽對比。
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">📦</span>
            <div class="feature-title">批量處理工廠</div>
            <div class="feature-desc">
                設定一次浮水印位置，自動批量處理數十張圖片。結果打包 ZIP 一鍵下載。
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🎬</span>
            <div class="feature-title">影片逐幀修復</div>
            <div class="feature-desc">
                上傳影片，在預覽幀上框選浮水印，系統自動逐幀修復。支持進度追蹤。
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Quick-start step flow
    st.markdown("""
    <div style="text-align:center; margin: 1rem 0 0.4rem 0;">
        <span style="font-size: 0.8rem; font-weight: 600; color: #b0bac5; text-transform: uppercase; letter-spacing: 0.06em;">
            快速使用流程
        </span>
    </div>
    """, unsafe_allow_html=True)

    render_step_flow([
        ("📂", "選擇功能"),
        ("📤", "上傳檔案"),
        ("🎯", "框選浮水印"),
        ("⚙️", "調整參數"),
        ("✨", "開始修復"),
        ("⬇️", "下載結果"),
    ], active_index=0)

    # Quick start guide
    with st.expander("📖 詳細使用指南", expanded=False):
        st.markdown("""
        ### 使用步驟

        1. **選擇功能** — 在左側導航欄選擇圖片修復、批量處理或影片修復
        2. **上傳檔案** — 拖拽或點擊上傳區域選擇檔案
        3. **框選浮水印** — 在畫布上用滑鼠拖拽框選浮水印區域（可框選多個）
        4. **調整參數** — 在左側面板調整修復演算法和半徑
        5. **開始修復** — 點擊修復按鈕，等待處理完成
        6. **下載結果** — 預覽修復效果後下載處理後的檔案

        ### 演算法說明

        | 演算法 | 特點 | 推薦場景 |
        |--------|------|----------|
        | **TELEA** | 快速行進法，速度快 | 大面積浮水印、批量處理 |
        | **NS** | Navier-Stokes 方程，效果精細 | 複雜紋理區域、高品質需求 |

        ### 修復半徑

        - **小半徑 (1-5)**：適合細小浮水印文字
        - **中半徑 (5-10)**：通用推薦值
        - **大半徑 (10-20)**：適合大面積浮水印，但可能略有模糊
        """)

    # Stats — 4 columns, 2x2 on mobile via CSS
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">2</div>
            <div class="metric-label">修復演算法</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">∞</div>
            <div class="metric-label">批量處理數</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">6+</div>
            <div class="metric-label">影片格式</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">100%</div>
            <div class="metric-label">本地離線</div>
        </div>
        """, unsafe_allow_html=True)
