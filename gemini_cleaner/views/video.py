import streamlit as st
import time
import tempfile
import os
from streamlit_drawable_canvas import st_canvas
from core.engine import get_video_info, get_first_frame, process_video
from utils.helpers import get_canvas_dimensions, extract_rects_from_canvas, format_duration
from utils.ui import render_step_flow, render_action_hint, render_empty_state

def render_video(inpaint_radius, method_key):
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
