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
from utils.helpers import get_canvas_dimensions, extract_rects_from_canvas, format_duration
from utils.ui import render_hero, render_step_flow, render_action_hint, render_empty_state, render_comparison


# ═══════════════════════════════════════════════════════════════════
#  ROUTING
# ═══════════════════════════════════════════════════════════════════

from views.home import render_home
from views.single_image import render_single_image
from views.batch_processing import render_batch_processing
from views.video import render_video
from views.about import render_about

if page == "🏠 首頁":
    render_home()
elif page == "🖼️ 圖片修復":
    render_single_image(inpaint_radius, method_key)
elif page == "📦 批量處理":
    render_batch_processing(inpaint_radius, method_key)
elif page == "🎬 影片修復":
    render_video(inpaint_radius, method_key)
elif page == "ℹ️ 關於":
    render_about()

