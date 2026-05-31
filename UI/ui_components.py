import streamlit as st
import plotly.graph_objects as go

def render_speedometer() -> int:
    """
    Me-render UI Pedal Gas, Rem, dan Speedometer lingkaran.
    Mengembalikan nilai kecepatan saat ini (int).
    """
    # ── 1. Init Session State ────────────────────────────────────────────────────
    if "kecepatan" not in st.session_state:
        st.session_state.kecepatan = 60

    # ── 2. CSS Injection — Tombol Gas & Rem ─────────────────────────────────────
    st.markdown("""
    <style>
    div[data-testid="column"] > div { display: flex; justify-content: center; }
    div[data-testid="stHorizontalBlock"] button {
        width: 100% !important; height: 54px !important; font-size: 1rem !important;
        font-weight: 700 !important; letter-spacing: 0.05em !important; border: none !important;
        border-radius: 8px !important; cursor: pointer !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease, filter 0.1s ease !important;
    }
    div[data-testid="stHorizontalBlock"] button:active {
        transform: scale(0.96) !important; filter: brightness(0.88) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) button:first-of-type {
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%) !important;
        color: #f0fdf4 !important; box-shadow: 0 4px 18px rgba(22, 163, 74, 0.45) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) button:first-of-type:hover {
        box-shadow: 0 6px 24px rgba(22, 163, 74, 0.65) !important; filter: brightness(1.08) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) button:last-of-type {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        color: #fff1f2 !important; box-shadow: 0 4px 18px rgba(220, 38, 38, 0.45) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) button:last-of-type:hover {
        box-shadow: 0 6px 24px rgba(220, 38, 38, 0.65) !important; filter: brightness(1.08) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── 3. Tombol Gas & Rem ──────────────────────────────────────────────────────
    col_gas, col_rem = st.columns(2)
    with col_gas:
        if st.button("⏩  PEDAL GAS  (+5)", key="btn_gas", use_container_width=True):
            st.session_state.kecepatan = min(150, st.session_state.kecepatan + 5)
    with col_rem:
        if st.button("⏪  PEDAL REM  (−5)", key="btn_rem", use_container_width=True):
            st.session_state.kecepatan = max(0, st.session_state.kecepatan - 5)

    # ── 4. Speedometer Gauge ─────────────────────────────────────────────────────
    kec = st.session_state.kecepatan

    if kec < 60: needle_color = "#22c55e"
    elif kec < 110: needle_color = "#facc15"
    else: needle_color = "#ef4444"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=kec,
        delta={"reference": 60, "increasing": {"color": "#ef4444"}, "decreasing": {"color": "#22c55e"}},
        number={"suffix": " km/h", "font": {"size": 36, "color": "#e2e8f0", "family": "monospace"}},
        gauge={
            "axis": {"range": [0, 150], "tickwidth": 2, "tickcolor": "#475569", "dtick": 30},
            "bar": {"color": needle_color, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
            "steps": [
                {"range": [0, 60], "color": "rgba(34,197,94,0.12)"},
                {"range": [60, 110], "color": "rgba(250,204,21,0.12)"},
                {"range": [110, 150], "color": "rgba(239,68,68,0.14)"},
            ],
            "threshold": {"line": {"color": "#f87171", "width": 3}, "thickness": 0.85, "value": 130},
        },
        title={"text": "🚗  VEHICLE SPEED", "font": {"size": 16, "color": "#94a3b8", "family": "monospace"}},
    ))

    fig.update_layout(
        paper_bgcolor="rgba(15,23,42,0.95)", font_color="#e2e8f0",
        margin=dict(t=60, b=20, l=30, r=30), height=300,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── 5. Kembalikan Nilai ──────────────────────────────────────────────────────
    return st.session_state.kecepatan