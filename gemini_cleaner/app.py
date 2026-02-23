"""
Gemini 浮水印去除工具 — Pro Edition v3.2
A premium watermark removal tool with modern dark UI/UX.
Responsive-first design.
"""

import streamlit as st
from PIL import Image
import numpy as np
import tempfile
import io
import os
import sys
import zipfile
import time

# ── Monkeypatch for streamlit-drawable-canvas compatibility ──────
import streamlit.elements.image as st_image
if not hasattr(st_image, 'image_to_url'):
    try:
        from streamlit.elements.utils import image_to_url
        st_image.image_to_url = image_to_url
    except ImportError:
        try:
            from streamlit.runtime.media_file_manager import MediaFileManager
            def image_to_url(image, width, clamp, channels, output_format, image_id, allow_emoji=True):
                return ""
            st_image.image_to_url = image_to_url
        except:
            pass

from streamlit_drawable_canvas import st_canvas

# ── Import core engine ───────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from core.engine import (
    inpaint_image, get_first_frame, get_video_info,
    process_video, create_mask_from_rects
)

# ── Page Config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Gemini 浮水印去除工具",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load Custom CSS ──────────────────────────────────────────────
css_path = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Additional inline CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 0.8rem 0 1.2rem 0;">
        <div style="font-size: 2rem; margin-bottom: 0.2rem;">✨</div>
        <div style="font-size: 1rem; font-weight: 800;
             background: linear-gradient(135deg, #c4b5fd, #8b5cf6, #f0b429);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent;
             background-clip: text;">CleanMark Pro</div>
        <div class="version-badge" style="margin-top: 0.4rem;">v3.2</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "導航",
        ["🏠 首頁", "🖼️ 圖片修復", "📦 批量處理", "🎬 影片修復", "ℹ️ 關於"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown('<div class="settings-panel-title">⚙️ 修復設定</div>', unsafe_allow_html=True)

    inpaint_method = st.selectbox(
        "演算法",
        ["TELEA (快速)", "NS (精細)"],
        help="TELEA：基於快速行進法，速度快。NS：基於 Navier-Stokes 方程，效果更精細但較慢。"
    )
    method_key = "telea" if "TELEA" in inpaint_method else "ns"

    inpaint_radius = st.slider(
        "修復半徑",
        min_value=1, max_value=20, value=5,
        help="每個像素的修復鄰域半徑。較大的值可覆蓋更寬的浮水印，但可能產生模糊。"
    )

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color: #8c95a1; font-size: 0.72rem; padding-top: 0.3rem;">
        Powered by OpenCV<br/>
        Built with ❤️ using Streamlit
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_canvas_dimensions(img_width, img_height, max_width=600):
    """Calculate responsive canvas dimensions that fit the container."""
    canvas_width = min(img_width, max_width)
    ratio = canvas_width / img_width
    canvas_height = int(img_height * ratio)
    return canvas_width, canvas_height, ratio


def render_hero():
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">✨ CleanMark Pro</div>
        <div class="hero-subtitle">使用先進的計算機視覺技術，輕鬆去除圖片和影片中的浮水印</div>
    </div>
    """, unsafe_allow_html=True)


def render_step_flow(steps, active_index=0):
    """Render a horizontal step flow indicator (scrollable on small screens)."""
    html = '<div class="step-flow">'
    for i, (emoji, label) in enumerate(steps):
        if i < active_index:
            cls = "step-flow-item done"
        elif i == active_index:
            cls = "step-flow-item active"
        else:
            cls = "step-flow-item"
        html += f'''<div class="{cls}">
            <span class="step-flow-number">{i+1}</span>
            <span>{emoji} {label}</span>
        </div>'''
        if i < len(steps) - 1:
            html += '<span class="step-flow-arrow">→</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_action_hint(emoji, text):
    """Render a breathing action hint."""
    st.markdown(f'''
    <div class="action-hint">
        <span class="action-hint-icon">{emoji}</span>
        <span>{text}</span>
    </div>
    ''', unsafe_allow_html=True)


def render_empty_state(icon, title, subtitle=""):
    """Render a polished empty state placeholder."""
    sub_html = f'<div class="empty-state-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="glass-panel empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-text">{title}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_comparison(original, processed, col1_label="原圖", col2_label="修復結果"):
    """Render side-by-side comparison of original and processed images."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="comparison-label comparison-label-before">{col1_label}</div>',
                    unsafe_allow_html=True)
        st.image(original, use_container_width=True)
    with c2:
        st.markdown(f'<div class="comparison-label comparison-label-after">{col2_label}</div>',
                    unsafe_allow_html=True)
        st.image(processed, use_container_width=True)


def extract_rects_from_canvas(canvas_result, ratio):
    """Extract rectangle coordinates from canvas result, scaled to original image size."""
    rects = []
    if canvas_result.json_data is not None:
        for obj in canvas_result.json_data.get("objects", []):
            if obj.get("type") == "rect":
                rects.append((
                    int(obj["left"] / ratio),
                    int(obj["top"] / ratio),
                    int(obj["width"] / ratio),
                    int(obj["height"] / ratio)
                ))
    return rects


def format_duration(seconds):
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f} 秒"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes} 分 {secs:.0f} 秒"


# ═══════════════════════════════════════════════════════════════════
#  PAGE: HOME
# ═══════════════════════════════════════════════════════════════════

if page == "🏠 首頁":
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


# ═══════════════════════════════════════════════════════════════════
#  PAGE: SINGLE IMAGE
# ═══════════════════════════════════════════════════════════════════

elif page == "🖼️ 圖片修復":
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


# ═══════════════════════════════════════════════════════════════════
#  PAGE: BATCH PROCESSING
# ═══════════════════════════════════════════════════════════════════

elif page == "📦 批量處理":
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


# ═══════════════════════════════════════════════════════════════════
#  PAGE: VIDEO
# ═══════════════════════════════════════════════════════════════════

elif page == "🎬 影片修復":
    st.markdown("""
    <div class="section-header">
        <span class="section-header-icon">🎬</span>
        <span class="section-header-text">影片逐幀修復</span>
    </div>
    """, unsafe_allow_html=True)

    uploaded_video = st.file_uploader(
        "上傳影片",
        type=["mp4", "mov", "avi", "mpeg", "webm", "mkv"],
        key="video_upload",
        help="支持 MP4、MOV、AVI、MPEG、WebM、MKV 格式"
    )

    if uploaded_video:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_video.read())
        video_path = tfile.name
        tfile.close()

        try:
            vid_info = get_video_info(video_path)
            first_frame_img = get_first_frame(video_path)

            render_step_flow([
                ("📤", "上傳影片"),
                ("🎯", "框選浮水印"),
                ("🎬", "開始修復"),
                ("⬇️", "下載結果"),
            ], active_index=1)

            # Video info — use 2 cols on mobile-friendly layout
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="font-size: 1.1rem;">{vid_info['width']}×{vid_info['height']}</div>
                    <div class="metric-label">解析度</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="font-size: 1.1rem;">{vid_info['fps']:.1f}</div>
                    <div class="metric-label">FPS</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="font-size: 1.1rem;">{vid_info['total_frames']}</div>
                    <div class="metric-label">總幀數</div>
                </div>
                """, unsafe_allow_html=True)
            with c4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="font-size: 1.1rem;">{format_duration(vid_info['duration'])}</div>
                    <div class="metric-label">時長</div>
                </div>
                """, unsafe_allow_html=True)

            render_action_hint("🎯", "在下方預覽幀上拖拽框選浮水印區域")

            canvas_width, canvas_height, ratio = get_canvas_dimensions(first_frame_img.width, first_frame_img.height)

            canvas_video = st_canvas(
                fill_color="rgba(139, 92, 246, 0.25)",
                stroke_width=2,
                stroke_color="#8b5cf6",
                background_image=first_frame_img,
                update_streamlit=True,
                height=canvas_height,
                width=canvas_width,
                drawing_mode="rect",
                key="canvas_video",
            )

            est_time = vid_info['total_frames'] * 0.02
            st.markdown(f"""
            <div style="color: #8c95a1; font-size: 0.82rem; margin-top: 0.3rem;">
                ⏱️ 預估處理時間：<strong style="color: #f0b429;">{format_duration(est_time)}</strong>（實際時間視硬體效能而定）
            </div>
            """, unsafe_allow_html=True)

            video_btn = st.button("🎬 開始影片修復", key="btn_video", use_container_width=True)

            if video_btn:
                rects = extract_rects_from_canvas(canvas_video, ratio)

                if len(rects) == 0:
                    st.warning("⚠️ 請先在預覽幀上框選浮水印區域。")
                    render_action_hint("🎯", "請先在預覽幀上框選浮水印位置")
                else:
                    progress_bar = st.progress(0, text="影片修復中...")
                    start_time = time.time()

                    def update_progress(current, total):
                        if total > 0:
                            pct = current / total
                            elapsed_t = time.time() - start_time
                            if current > 0:
                                eta = (elapsed_t / current) * (total - current)
                                progress_bar.progress(
                                    min(pct, 1.0),
                                    text=f"處理中... {current}/{total} 幀 · 預估剩餘 {format_duration(eta)}"
                                )
                            else:
                                progress_bar.progress(0, text="啟動中...")

                    try:
                        processed_path = process_video(
                            video_path, rects,
                            radius=inpaint_radius, method=method_key,
                            progress_callback=update_progress
                        )

                        elapsed = time.time() - start_time
                        progress_bar.progress(1.0, text="完成！")

                        render_step_flow([
                            ("📤", "上傳影片"),
                            ("🎯", "框選浮水印"),
                            ("🎬", "開始修復"),
                            ("⬇️", "下載結果"),
                        ], active_index=3)

                        st.markdown(f"""
                        <div class="success-badge">
                            ✅ 影片修復完成！耗時 {format_duration(elapsed)}
                        </div>
                        """, unsafe_allow_html=True)

                        st.video(processed_path)

                        with open(processed_path, 'rb') as f:
                            video_bytes = f.read()

                        st.download_button(
                            label="⬇️ 下載修復後的影片",
                            data=video_bytes,
                            file_name=f"cleaned_{uploaded_video.name}",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"❌ 影片處理失敗：{e}")

                    try:
                        if os.path.exists(video_path):
                            os.unlink(video_path)
                    except:
                        pass

        except Exception as e:
            st.error(f"❌ 無法讀取影片：{e}")
    else:
        render_step_flow([
            ("📤", "上傳影片"),
            ("🎯", "框選浮水印"),
            ("🎬", "開始修復"),
            ("⬇️", "下載結果"),
        ], active_index=0)

        render_empty_state(
            "🎬",
            "上傳影片檔案開始修復",
            "支持 MP4、MOV、AVI、MPEG、WebM、MKV 格式"
        )


# ═══════════════════════════════════════════════════════════════════
#  PAGE: ABOUT
# ═══════════════════════════════════════════════════════════════════

elif page == "ℹ️ 關於":
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
