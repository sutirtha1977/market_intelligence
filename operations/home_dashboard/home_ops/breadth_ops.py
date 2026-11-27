# operations/home_dashboard/home_ops/breadth_ops.py

import streamlit as st

from core.styles import COLOR_MAP
from operations.home_dashboard.home_ops.home_data import SERIES_COLORS, get_breadth


def _build_chart(series: dict):
    # IMPORTANT: lazy import - plotly is heavy
    import plotly.graph_objects as go

    fig = go.Figure()
    for name, color in SERIES_COLORS.items():
        fig.add_trace(go.Scatter(x=series["dates"], y=series[name], name=name,
                                 mode="lines", line=dict(color=color, width=2)))
    fig.update_layout(
        height=330, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="v", x=1.01, y=1),
        xaxis=dict(showgrid=True, gridcolor=COLOR_MAP["gray-10"], tickangle=-30, nticks=7),
        yaxis=dict(showgrid=True, gridcolor=COLOR_MAP["gray-10"], range=[0, 100]),
    )
    return fig


def _render_panel(col, market: str):
    data = get_breadth(market)
    pills = "".join(
        f'<div class="pill {"" if v >= 50 else "bear"}"><div class="l">{k}</div><div class="v">{v:.1f}%</div>'
        f'<div class="s">{"Bullish" if v >= 50 else "Bearish"}</div></div>'
        for k, v in data["latest"].items()
    )
    with col:
        st.markdown(
            f'<div class="card"><div class="sma-title">{data["flag"]} SMA Breadth (Last 30 days)</div>'
            f'<div class="pills">{pills}</div></div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(_build_chart(data["series"]),
                        width="stretch",
                        config={"displayModeBar": False},
                        key=f"breadth_{market}")


def handle_breadth_section():
    left, right = st.columns(2)
    _render_panel(left, "IN")
    _render_panel(right, "US")