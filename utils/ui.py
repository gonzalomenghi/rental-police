import streamlit as st
import pandas as pd

# ── Brand color palette ────────────────────────────────────────────────────────
OCEAN_BLUE     = "#009CDF"
SPACE_BLUE     = "#26204E"
SKY_BLUE       = "#A5D7FC"
SAND           = "#E8E2DC"
CRITICAL_RED   = "#C0392B"
WARNING_ORANGE = "#D4760A"


def kpi_row(cols_data: list):
    """
    Renders branded KPI cards in a horizontal row.
    Each item: (label, value, color [, critical=False [, delta=None]])
      critical: bool — adds 🚩 flag and red left-border when value > 0
      delta:    int  — week-over-week change shown as ↑/↓ below the value
    """
    cols = st.columns(len(cols_data))
    for col, item in zip(cols, cols_data):
        label    = item[0]
        value    = item[1]
        color    = item[2]
        critical = item[3] if len(item) > 3 else False
        delta    = item[4] if len(item) > 4 else None

        flag         = "🚩 " if critical and value > 0 else ""
        border_color = CRITICAL_RED if critical and value > 0 else color

        delta_html = ""
        if delta is not None:
            sign  = "+" if delta > 0 else ""
            dcol  = CRITICAL_RED if delta > 0 else ("#1E8840" if delta < 0 else "#888888")
            trend = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
            delta_html = (
                f'<div style="font-size:11px;font-weight:600;color:{dcol};margin-top:5px">'
                f'{trend} {sign}{delta:,} vs sem. anterior</div>'
            )

        with col:
            st.markdown(
                f"""<div style="
                    background:#FFFFFF;
                    border-radius:10px;
                    padding:16px 20px;
                    border-left:5px solid {border_color};
                    box-shadow:0 1px 6px rgba(38,32,78,0.10);
                    font-family:'Manrope',sans-serif;
                ">
                    <div style="font-size:10px;font-weight:700;color:{SPACE_BLUE};
                                text-transform:uppercase;letter-spacing:0.8px;margin-bottom:6px"
                    >{flag}{label}</div>
                    <div style="font-size:28px;font-weight:700;color:{color};line-height:1.1"
                    >{value:,}</div>
                    {delta_html}
                </div>""",
                unsafe_allow_html=True,
            )


def show_detail(detail: pd.DataFrame, label: str):
    """Shows drill-down detail table with branded caption."""
    if not detail.empty:
        st.caption(f"📋 Detalle — **{label}** ({len(detail)} registros)")
        st.dataframe(detail, use_container_width=True, hide_index=True)
