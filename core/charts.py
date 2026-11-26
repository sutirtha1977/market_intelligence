# core/charts.py

from typing import Optional
import pandas as pd
from core.styles import COLOR_MAP, FONT_FAMILY
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --------------------------------------------------------------------------
def _hex(key: str, alpha: float | None = None) -> str:
    """Return a COLOR_MAP hex value, optionally as rgba(r,g,b,alpha)."""
    h = COLOR_MAP[key].lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if alpha is not None:
        return f"rgba({r},{g},{b},{alpha})"
    return COLOR_MAP[key]
# --------------------------------------------------------------------------
P: dict[str, str] = {
    # Candles
    "up_line":  _hex("green-70"),
    "up_fill":  _hex("green-50"),
    "dn_line":  _hex("red-70"),
    "dn_fill":  _hex("red-50"),
    # Bollinger bands
    "bb_band":  _hex("blue-600"),
    "bb_mid":   _hex("black"),
    # RSI lines
    "rsi":      _hex("black"),
    "ema_rsi":  _hex("emerald-600"),
    "wma_rsi":  _hex("rose-500"),
    # RSI reference levels
    "rsi_ob":   _hex("red-50",    0.35),
    "rsi_mid":  _hex("gray-50",   0.40),
    "rsi_os":   _hex("green-50",  0.35),
    # RS panel
    "rs":       _hex("blue-600"),
    "rs_ma":    _hex("orange-70"),
    "rs_zero":  _hex("gray-50",   0.50),
    # Optional reference price level
    "ref_line": _hex("red-50",    0.85),
    # Layout
    "bg_paper":     _hex("gray-0"),
    "bg_plot":      _hex("gray-5"),
    "grid":         _hex("gray-20",  0.70),
    "axis_line":    _hex("gray-30"),
    "tick":         _hex("gray-70"),
    "panel_label":  _hex("gray-50"),
    "hover_bg":     _hex("gray-0"),
    "hover_border": _hex("card-border"),
    "hover_text":   _hex("text-primary"),
    "title_text":   _hex("gray-90"),
}

# --------------------------------------------------------------------------
def _xaxis(**extra) -> dict:
    return dict(
        type="date",
        showgrid=True,
        gridcolor=P["grid"],
        gridwidth=0.5,
        zeroline=False,
        showline=True,
        linecolor=P["axis_line"],
        linewidth=0.5,

        tickfont=dict(
            family=FONT_FAMILY,
            size=10,
            color=P["tick"]
        ),

        tickformat="%d %b %Y",
        nticks=8,

        # =========================================================
        # SPIKE LINE SUPPORT
        # =========================================================
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor=P["axis_line"],
        spikethickness=1,

        **extra,
    )

# --------------------------------------------------------------------------
def _yaxis(**extra) -> dict:
    return dict(
        side="right",
        showgrid=True,
        gridcolor=P["grid"],
        gridwidth=0.5,
        zeroline=False,
        showline=True,
        linecolor=P["axis_line"],
        linewidth=0.5,
        tickfont=dict(family=FONT_FAMILY, size=10, color=P["tick"]),
        **extra,
    )

# --------------------------------------------------------------------------
def _label(text: str, y_ref: str) -> dict:
    """Uppercase 9 px caption pinned to the top-left of a subplot panel."""
    return dict(
        text=f"<b>{text.upper()}</b>",
        xref="paper",
        yref=y_ref,
        x=0.004,
        y=1.0,
        xanchor="left",
        yanchor="top",
        showarrow=False,
        font=dict(family=FONT_FAMILY, size=9, color=P["panel_label"]),
    )

# --------------------------------------------------------------------------
def prepare_stock_chart_figure(
    df: pd.DataFrame,
    symbol_name: Optional[str] = None,
    reference_line: Optional[dict] = None,
) -> go.Figure:
    """
    Build a professional multi-panel stock chart.

    Parameters
    ----------
    df:
        DataFrame with required columns: date, open, high, low, close.
        Optional columns: bb_upper, bb_middle, bb_lower,
                          rsi_9, ema_rsi_9_3, wma_rsi_9_21,
                          rs, rs_ma.
    symbol_name:
        Ticker or instrument label shown in the chart header.
    reference_line:
        Dict with 'value' (float) and optional 'label' (str)
        to draw a dashed horizontal reference on the price panel.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    has_rs = "rs" in df.columns

    # ── Subplots ──────────────────────────────────────────────────────────────
    if has_rs:
        rows, row_heights = 3, [0.57, 0.25, 0.18]
    else:
        rows, row_heights = 2, [0.72, 0.28]

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=row_heights,
    )

    # ── Price panel ───────────────────────────────────────────────────────────
    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=symbol_name or "Price",
            increasing=dict(
                line=dict(color=P["up_line"], width=0.9),
                fillcolor=P["up_fill"],
            ),
            decreasing=dict(
                line=dict(color=P["dn_line"], width=0.9),
                fillcolor=P["dn_fill"],
            ),
            whiskerwidth=0.75,
        ),
        row=1, col=1,
    )

    # Bollinger bands: upper/lower = blue-600 at 50% opacity; mid = violet-500 dashed
    for bb_col, color, dash in [
        ("bb_upper",  P["bb_band"], None),
        ("bb_middle", P["bb_mid"],  None),
        ("bb_lower",  P["bb_band"], None),
    ]:
        if bb_col not in df.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df[bb_col],
                mode="lines",
                line=dict(color=color, width=1.0, dash=dash),
                name=bb_col,
                showlegend=False,
            ),
            row=1, col=1,
        )

    # Optional reference price level
    if reference_line and reference_line.get("value") is not None:
        fig.add_hline(
            y=float(reference_line["value"]),
            line=dict(color=P["ref_line"], width=1.0, dash="dot"),
            annotation_text=reference_line.get("label", "Ref"),
            annotation_font=dict(family=FONT_FAMILY, size=9, color=P["ref_line"]),
            annotation_position="top left",
            row=1, col=1,
        )

    # ── RSI panel ─────────────────────────────────────────────────────────────
    for rsi_col, color, width in [
        ("rsi_9",        P["rsi"],     2),
        ("rsi_3",        P["rsi"],     1),
        ("ema_rsi_9_3",  P["ema_rsi"], 1),
        ("wma_rsi_9_21", P["wma_rsi"], 2),
    ]:
        if rsi_col not in df.columns:
            continue

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df[rsi_col],
                mode="lines",
                line=dict(color=color, width=width),
                name=rsi_col,
                showlegend=False,
            ),
            row=2, col=1,
        )

    # ── RSI LEVELS (FIXED AS REQUESTED) ───────────────────────────────────────
    fig.add_hline(y=80, line=dict(color="red", width=1.5, dash="dot"), row=2, col=1)
    fig.add_hline(y=50, line=dict(color="black", width=1,), row=2, col=1)
    fig.add_hline(y=30, line=dict(color="green", width=1.5, dash="dot"), row=2, col=1)
    
    # ── DYNAMIC EMA / SMA SUPPORT ───────────────────────────────────────────
    ema_list = ["ema_3", "ema_5", "ema_7", "ema_9", "ema_10"]
    sma_list = ["sma_50", "sma_100", "sma_200"]
    for col in ema_list:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df[col],
                    mode="lines",
                    line=dict(color="red",width=1),
                    name=col,
                ),
                row=1, col=1,
            )
    for col in sma_list:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df[col],
                    mode="lines",
                    line=dict(width=2),
                    name=col,
                ),
                row=1, col=1,
            )

    # ── RS panel (optional) ───────────────────────────────────────────────────
    if has_rs:
        if "rs" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["rs"],
                    mode="lines",
                    line=dict(color=P["rs"], width=1.5),
                    name="RS",
                    showlegend=False,
                ),
                row=3, col=1,
            )
        if "rs_ma" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["rs_ma"],
                    mode="lines",
                    line=dict(color=P["rs_ma"], width=1.2),
                    name="RS MA",
                    showlegend=False,
                ),
                row=3, col=1,
            )
        fig.add_hline(
            y=0,
            line=dict(color=P["rs_zero"], width=0.8, dash="dot"),
            row=3, col=1,
        )

    # ── Layout ────────────────────────────────────────────────────────────────
    label = symbol_name or "Chart"
    _title_color = P["title_text"]
    _tick_color  = P["tick"]
    title_html = (
        f"<span style='font-family:{FONT_FAMILY};font-size:12px;"
        f"font-weight:600;letter-spacing:0.07em;"
        f"color:{_title_color}'>{label}</span>"
        f"<span style='font-family:{FONT_FAMILY};font-size:11px;"
        f"color:{_tick_color}'>&nbsp;&nbsp;</span>"
    )

    annotations = [
        _label("Price · BB(20,2)", "y domain"),
        _label("RSI, EMA, WMA", "y2 domain"),
    ]
    if has_rs:
        annotations.append(_label("Rel. Strength", "y3 domain"))

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=P["bg_paper"],
        plot_bgcolor=P["bg_plot"],
        height=590,
        spikedistance=-1,
        hoverdistance=100,
        title=dict(
            text=title_html,
            x=0.0,
            xanchor="left",
            pad=dict(l=14, t=8),
        ),
        font=dict(
            family=FONT_FAMILY,
            size=10,
            color=P["tick"]
        ),
        margin=dict(l=8, r=68, t=44, b=16),

        xaxis_rangeslider_visible=False,
        showlegend=False,

        hovermode="x",
        hoversubplots="axis",

        hoverlabel=dict(
            bgcolor=P["hover_bg"],
            bordercolor=P["hover_border"],
            font=dict(
                family=FONT_FAMILY,
                size=10,
                color=P["hover_text"]
            ),
            namelength=-1,
        ),

        annotations=annotations,
    )

    # ── Axes ──────────────────────────────────────────────────────────────────
    # X-axes: only the bottom panel shows date labels
    for i in range(1, rows + 1):
        fig.update_xaxes(
            **_xaxis(showticklabels=(i == rows)),
            row=i, col=1,
        )

    # Y-axes — price and RSI always present
    fig.update_layout(
        yaxis=_yaxis(tickformat=".0f"),
        yaxis2=_yaxis(
            range=[0, 100],
            tickvals=[30, 50, 70],
            tickformat=".0f",
        ),
    )

    # RS y-axis — conditional; separate call sidesteps the **{} Pylance error
    if has_rs:
        fig.update_layout(yaxis3=_yaxis(tickformat=".2f"))

    return fig
# --------------------------------------------------------------------------