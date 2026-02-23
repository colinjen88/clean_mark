import streamlit as st
from PIL import Image
import time
import io
from streamlit_drawable_canvas import st_canvas
from core.engine import inpaint_image
from utils.helpers import get_canvas_dimensions, extract_rects_from_canvas
from utils.ui import render_step_flow, render_action_hint, render_empty_state, render_comparison

def render_single_image(inpaint_radius, method_key):
    st.markdown("""
    <div class="section-header">
        <span class="section-header-icon">🖼️</span>
        <span class="section-header-text">智能圖片修復</span>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "上傳圖片",
        type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
        key="single_upload",
        help="支持 PNG、JPG、WEBP、BMP、TIFF 格式"
    )

    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")

        # Step flow
        render_step_flow([
            ("📤", "上傳圖片"),
            ("🎯", "框選浮水印"),
            ("✨", "開始修復"),
            ("⬇️", "下載結果"),
        ], active_index=1)

        # Image info panel (full-width, above the canvas)
        st.markdown(f"""
        <div class="settings-panel">
            <div class="settings-panel-title">📐 圖片資訊</div>
            <div style="color: #b0bac5; font-size: 0.85rem; line-height: 1.6;">
                <strong>解析度</strong>：{image.width} × {image.height} px ｜
                <strong>檔案</strong>：{uploaded_file.name} ｜
                <strong>大小</strong>：{uploaded_file.size / 1024:.1f} KB
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Operation hint
        st.markdown("""
        <div class="info-card">
            <strong>💡 操作提示</strong>：
            在下方畫布上<strong style="color: #f0b429 !important;">拖拽框選</strong>浮水印區域，
            支持框選<strong style="color: #f0b429 !important;">多個區域</strong>，所有區域都將被修復。
        </div>
        """, unsafe_allow_html=True)

        # Canvas — responsive width
        canvas_width, canvas_height, ratio = get_canvas_dimensions(image.width, image.height)

        canvas_result = st_canvas(
            fill_color="rgba(139, 92, 246, 0.25)",
            stroke_width=2,
            stroke_color="#8b5cf6",
            background_image=image,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="rect",
            key="canvas_single",
        )

        render_action_hint("👆", "在畫布上拖拽繪製選取框")

        # Process button (full-width on mobile)
        process_btn = st.button("✨ 開始修復", key="btn_single", use_container_width=True)

        if process_btn:
            rects = extract_rects_from_canvas(canvas_result, ratio)

            if len(rects) == 0:
                st.warning("⚠️ 請先在圖片上框選至少一個浮水印區域。")
                render_action_hint("🎯", "請回到畫布上拖拽框選浮水印區域後再點擊修復")
            else:
                with st.spinner(f"🔧 正在修復 {len(rects)} 個區域..."):
                    start_time = time.time()
                    result_img = inpaint_image(image, rects, radius=inpaint_radius, method=method_key)
                    elapsed = time.time() - start_time

                # Updated step flow
                render_step_flow([
                    ("📤", "上傳圖片"),
                    ("🎯", "框選浮水印"),
                    ("✨", "開始修復"),
                    ("⬇️", "下載結果"),
                ], active_index=3)

                st.markdown(f"""
                <div class="success-badge">
                    ✅ 修復完成！耗時 {elapsed:.2f} 秒，共處理 {len(rects)} 個區域
                </div>
                """, unsafe_allow_html=True)
                st.markdown("", unsafe_allow_html=True)

                # Comparison
                render_comparison(image, result_img)

                # Download
                buf = io.BytesIO()
                result_img.save(buf, format="PNG")
                st.download_button(
                    label="⬇️ 下載修復後的圖片",
                    data=buf.getvalue(),
                    file_name=f"cleaned_{uploaded_file.name.rsplit('.', 1)[0]}.png",
                    mime="image/png",
                    use_container_width=True
                )
    else:
        render_step_flow([
            ("📤", "上傳圖片"),
            ("🎯", "框選浮水印"),
            ("✨", "開始修復"),
            ("⬇️", "下載結果"),
        ], active_index=0)

        render_empty_state(
            "🖼️",
            "拖拽或點擊上方區域上傳圖片開始修復",
            "支持 PNG、JPG、WEBP、BMP、TIFF 格式"
        )
