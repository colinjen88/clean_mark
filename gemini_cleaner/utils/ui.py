import streamlit as st

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
