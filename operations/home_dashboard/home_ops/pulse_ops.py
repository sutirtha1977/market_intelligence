# operations/home_dashboard/home_ops/pulse_ops.py

import streamlit as st

from operations.home_dashboard.home_ops.home_data import (
    TODAY,
    get_next_event,
    get_vix,
    get_index_cards,
)


def handle_header_section():
    # Title
    # st.markdown('<div class="card hero"><h1>MARKET PULSE</h1></div>', unsafe_allow_html=True)
    # st.write("")

    # Next event countdown
    ev = get_next_event()
    days_left = (ev["date"] - TODAY).days
    st.markdown(
        f"""
<div class="card row">
  <div class="event">🗓️&nbsp; {ev["name"]}</div>
  <div class="event" style="font-weight:500">{days_left} days left ({ev["date"].strftime("%d %b %Y")})</div>
</div>""",
        unsafe_allow_html=True,
    )
    st.write("")

    # VIX
    vix = get_vix()
    cls = "neg" if vix["change"] < 0 else "pos"
    st.markdown(
        f"""
<div class="card row">
  <div class="vix">🇮🇳 VIX {vix["value"]:.2f}<span class="chg {cls}">({vix["change"]:+.2f})</span></div>
  <div class="regime">{vix["regime"]}</div>
</div>""",
        unsafe_allow_html=True,
    )
    st.write("")


def _index_card(i: dict) -> str:
    return f"""
<div class="card idx {i['bias']}">
  <div class="row"><div class="name">{i['name']}</div><div class="badge {i['bias']}">{i['bias']}</div></div>
  <div class="metrics">
    <span>OI <b>{i['oi']:.2f}</b></span>
    <span>VOL <b>{i['vol']:.2f}</b></span>
    <span>ΔOI <b>{i['doi']:.2f}</b></span>
  </div>
  <div class="expiry">Expiry: {i['expiry']}</div>
</div>"""


def handle_index_section():
    cards = get_index_cards()
    for start in range(0, len(cards), 4):
        cols = st.columns(4)
        for col, c in zip(cols, cards[start:start + 4]):
            col.markdown(_index_card(c), unsafe_allow_html=True)
        st.write("")