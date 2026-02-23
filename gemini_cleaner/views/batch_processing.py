import streamlit as st
from PIL import Image
import time
import io
import zipfile
from streamlit_drawable_canvas import st_canvas
from core.engine import inpaint_image
from utils.helpers import get_canvas_dimensions, extract_rects_from_canvas
from utils.ui import render_step_flow, render_action_hint, render_empty_state

def render_batch_processing(inpaint_radius, method_key):
    st.markdown("""
    <div class="section-header">
        <span class="section-header-icon">📦</span>
        <span class="section-header-text">批量處理工廠</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <strong>💡 操作說明</strong>：
        上傳多張<strong style="color: #f0b429 !important;">浮水印位置相同</strong>的圖片，
        在第一張圖上定義浮水印位置後，系統將自動套用到所有圖片。
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "上傳多張圖片",
        type=["png", "jpg", "jpeg", "webp", "bmp"],
        accept_multiple_files=True,
        key="batch_upload"
    )

    if uploaded_files and len(uploaded_files) > 0:
        render_step_flow([
            ("📤", "上傳圖片"),
            ("🎯", "框選浮水印"),
            ("🚀", "批量處理"),
            ("⬇️", "下載 ZIP"),
        ], active_index=1)

        st.markdown(f"""
        <div style="display: inline-flex; align-items: center; gap: 0.4rem; margin: 0.4rem 0 0.8rem 0;">
            <span class="notification-dot"></span>
            <span style="color: #f0f4f8; font-weight: 600; font-size: 0.9rem;">{len(uploaded_files)} 張圖片已上傳</span>
        </div>
        """, unsafe_allow_html=True)

        render_action_hint("🎯", "在第一張圖片上框選浮水印位置，此設定將套用到所有圖片")

        first_image = Image.open(uploaded_files[0]).convert("RGB")
        canvas_width, canvas_height, ratio = get_canvas_dimensions(first_image.width, first_image.height)

        canvas_batch = st_canvas(
            fill_color="rgba(139, 92, 246, 0.25)",
            stroke_width=2,
            stroke_color="#8b5cf6",
            background_image=first_image,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="rect",
            key="canvas_batch",
        )

        batch_btn = st.button("🚀 開始批量處理", key="btn_batch", use_container_width=True)

        if batch_btn:
            rects = extract_rects_from_canvas(canvas_batch, ratio)

            if len(rects) == 0:
                st.warning("⚠️ 請先在第一張圖片上框選浮水印區域。")
                render_action_hint("🎯", "請先在畫布上框選浮水印位置")
            else:
                zip_buffer = io.BytesIO()
                progress_bar = st.progress(0, text="準備中...")

                start_time = time.time()
                processed_count = 0
                failed_count = 0

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for i, uploaded_file in enumerate(uploaded_files):
                        try:
                            img = Image.open(uploaded_file).convert("RGB")
                            cleaned_img = inpaint_image(img, rects, radius=inpaint_radius, method=method_key)

                            img_byte_arr = io.BytesIO()
                            cleaned_img.save(img_byte_arr, format="PNG")
                            zip_file.writestr(
                                f"cleaned_{uploaded_file.name.rsplit('.', 1)[0]}.png",
                                img_byte_arr.getvalue()
                            )
                            processed_count += 1
                        except Exception as e:
                            failed_count += 1
                            st.warning(f"⚠️ 無法處理 {uploaded_file.name}: {e}")

                        progress = (i + 1) / len(uploaded_files)
                        progress_bar.progress(progress, text=f"處理中... {i+1}/{len(uploaded_files)}")

                elapsed = time.time() - start_time
                progress_bar.progress(1.0, text="完成！")

                render_step_flow([
                    ("📤", "上傳圖片"),
                    ("🎯", "框選浮水印"),
                    ("🚀", "批量處理"),
                    ("⬇️", "下載 ZIP"),
                ], active_index=3)

                fail_text = f'，失敗 {failed_count} 張' if failed_count > 0 else ''
                st.markdown(f"""
                <div class="success-badge">
                    ✅ 批量處理完成！成功 {processed_count} 張，耗時 {elapsed:.1f} 秒{fail_text}
                </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    label=f"⬇️ 下載所有結果 (ZIP · {processed_count} 張)",
                    data=zip_buffer.getvalue(),
                    file_name="cleaned_images.zip",
                    mime="application/zip",
                    use_container_width=True
                )
    else:
        render_step_flow([
            ("📤", "上傳圖片"),
            ("🎯", "框選浮水印"),
            ("🚀", "批量處理"),
            ("⬇️", "下載 ZIP"),
        ], active_index=0)

        render_empty_state(
            "📦",
            "上傳多張圖片開始批量處理",
            "支持 PNG、JPG、WEBP、BMP 格式，批量內所有圖片浮水印位置需一致"
        )
