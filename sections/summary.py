import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.snapshot import (
    ensure_weekly_snapshot, build_kpis,
    get_wow_deltas, get_trend_data, week_key,
)
from utils.ui import (
    OCEAN_BLUE, SPACE_BLUE, SKY_BLUE, SAND,
    CRITICAL_RED, kpi_row,
)

# Area accent colors (within the brand blue family)
_IR_COLOR     = SPACE_BLUE     # #26204E — darkest, most senior
_RENTAL_COLOR = OCEAN_BLUE     # #009CDF — primary brand
_SUPPLY_COLOR = "#3EADD6"      # mid Ocean↔Sky Blue


# ── Chart builders ─────────────────────────────────────────────────────────────

def _bar_chart(sections_data: dict, bar_colors: list) -> go.Figure:
    labels = list(sections_data.keys())
    values = list(sections_data.values())
    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=bar_colors[:len(labels)],
        text=[str(v) if v > 0 else "" for v in values],
        textposition="outside",
        textfont=dict(family="Manrope", size=12, color=SPACE_BLUE),
        cliponaxis=False,
    ))
    fig.update_layout(
        font=dict(family="Manrope"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=30, b=120, l=10, r=10),
        xaxis=dict(tickfont=dict(family="Manrope", size=11), tickangle=-35),
        yaxis=dict(gridcolor="#EDEBE8", zeroline=False, title=""),
        showlegend=False,
        height=300,
    )
    return fig


def _donut_chart(area_totals: dict) -> go.Figure:
    labels = list(area_totals.keys())
    values = list(area_totals.values())
    total  = sum(values) or 1
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.58,
        marker_colors=[_IR_COLOR, _RENTAL_COLOR, _SUPPLY_COLOR],
        textfont=dict(family="Manrope", size=12),
        hovertemplate="%{label}: %{value} alertas (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        font=dict(family="Manrope"),
        paper_bgcolor="white",
        margin=dict(t=10, b=30, l=10, r=10),
        legend=dict(font=dict(family="Manrope", size=12), orientation="h", y=-0.08),
        height=300,
        annotations=[dict(
            text=f"<b>{total:,}</b><br>total",
            x=0.5, y=0.5,
            font=dict(size=18, family="Manrope", color=SPACE_BLUE),
            showarrow=False,
        )],
    )
    return fig


def _trend_chart(trend_df: pd.DataFrame) -> go.Figure:
    area_cfg = [
        ("👥 IR & Coaches", ["ir_pending_offers", "ir_pm_plan_missing",
                              "ir_home_insurance", "ir_missing_client"],          _IR_COLOR),
        ("🏪 Rental Team",  ["rental_unassigned_pm", "rental_ready_to_rent",
                              "rental_missing_lease", "rental_sub_formal"],       _RENTAL_COLOR),
        ("📍 Supply Team",  ["supply_missing_kd", "supply_tenanted"],             _SUPPLY_COLOR),
    ]
    fig = go.Figure()
    for name, cols, color in area_cfg:
        avail = [c for c in cols if c in trend_df.columns]
        if not avail:
            continue
        y = trend_df[avail].sum(axis=1)
        fig.add_trace(go.Scatter(
            x=trend_df["week"], y=y, name=name,
            mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=7),
            hovertemplate=f"{name}: %{{y}} alertas — semana %{{x}}<extra></extra>",
        ))
    fig.update_layout(
        font=dict(family="Manrope"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=20, l=10, r=10),
        legend=dict(
            font=dict(family="Manrope", size=12),
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        ),
        xaxis=dict(gridcolor="#EDEBE8", tickfont=dict(family="Manrope", size=11)),
        yaxis=dict(title="Alertas activas", gridcolor="#EDEBE8", zeroline=False),
        height=280,
    )
    return fig


# ── Mini KPI card (vertical area breakdown) ────────────────────────────────────

def _mini_card(label: str, value: int, key: str, critical: bool, deltas: dict) -> str:
    delta  = deltas.get(key)
    flag   = "🚩 " if critical and value > 0 else ""
    vcolor = CRITICAL_RED if critical and value > 0 else SPACE_BLUE
    border = CRITICAL_RED if critical and value > 0 else OCEAN_BLUE

    d_html = ""
    if delta is not None:
        sign  = "+" if delta > 0 else ""
        dcol  = CRITICAL_RED if delta > 0 else ("#1E8840" if delta < 0 else "#888")
        trend = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
        d_html = (
            f'<span style="font-size:11px;font-weight:600;'
            f'color:{dcol};margin-left:6px">{trend}{sign}{delta:,}</span>'
        )

    return (
        f'<div style="background:#FFFFFF;border-radius:8px;padding:10px 14px;'
        f'border-left:4px solid {border};margin-bottom:8px;'
        f'box-shadow:0 1px 3px rgba(38,32,78,0.08);font-family:\'Manrope\',sans-serif;">'
        f'<div style="font-size:10px;font-weight:700;color:#666;'
        f'text-transform:uppercase;letter-spacing:0.5px">{flag}{label}</div>'
        f'<div style="font-size:20px;font-weight:700;color:{vcolor};line-height:1.3">'
        f'{value:,}{d_html}</div>'
        f'</div>'
    )


def _area_col(header_color: str, icon: str, title: str, items: list, deltas: dict):
    st.html(
        f'<div style="background:{header_color};border-radius:10px;padding:12px 16px;'
        f'font-family:\'Manrope\',sans-serif;margin-bottom:10px;">'
        f'<div style="font-size:15px;font-weight:700;color:#FFFFFF">{icon} {title}</div>'
        f'</div>'
    )
    for label, val, key, crit in items:
        st.html(_mini_card(label, val, key, crit, deltas))


# ── Main render ────────────────────────────────────────────────────────────────

def render(df: pd.DataFrame, _filters: dict):
    """Dashboard tab — always shows global unfiltered totals + WoW evolution."""

    # Save snapshot once per session (skips if current week already stored)
    if "snapshot_saved" not in st.session_state:
        ensure_weekly_snapshot(df)
        st.session_state.snapshot_saved = True

    # Current KPIs + deltas
    kpis   = build_kpis(df)
    deltas = get_wow_deltas(kpis)

    ir_total     = kpis["ir_pending_offers"] + kpis["ir_pm_plan_missing"] + kpis["ir_home_insurance"] + kpis["ir_missing_client"]
    rental_total = kpis["rental_unassigned_pm"] + kpis["rental_ready_to_rent"] + kpis["rental_missing_lease"] + kpis["rental_sub_formal"]
    supply_total = kpis["supply_missing_kd"] + kpis["supply_tenanted"]
    grand_total  = ir_total + rental_total + supply_total

    def _area_delta(*keys):
        return sum(deltas.get(k, 0) for k in keys) if deltas else None

    grand_delta  = _area_delta(*kpis.keys())
    ir_delta     = _area_delta("ir_pending_offers", "ir_pm_plan_missing", "ir_home_insurance", "ir_missing_client")
    rental_delta = _area_delta("rental_unassigned_pm", "rental_ready_to_rent", "rental_missing_lease", "rental_sub_formal")
    supply_delta = _area_delta("supply_missing_kd", "supply_tenanted")

    # ── Header banner ─────────────────────────────────────────────────────────
    wk = week_key()
    st.html(
        f'<div style="background:linear-gradient(135deg,{SPACE_BLUE} 0%,{OCEAN_BLUE} 100%);'
        f'border-radius:14px;padding:24px 32px;margin-bottom:20px;font-family:\'Manrope\',sans-serif;">'
        f'<div style="font-size:22px;font-weight:700;color:#FFFFFF;margin-bottom:4px">'
        f'🛡️ Rental Police — Dashboard Global</div>'
        f'<div style="font-size:13px;color:{SKY_BLUE};font-weight:500">'
        f'{wk} &nbsp;·&nbsp; {len(df):,} registros cargados &nbsp;·&nbsp; '
        f'Vista global sin filtros de equipo aplicados</div>'
        f'</div>'
    )

    # ── Top KPI row ───────────────────────────────────────────────────────────
    kpi_row([
        ("🚩 Total alertas activas", grand_total,  CRITICAL_RED,   True,  grand_delta),
        ("👥 IR & Coaches",          ir_total,     _IR_COLOR,      False, ir_delta),
        ("🏪 Rental Team",           rental_total, _RENTAL_COLOR,  False, rental_delta),
        ("📍 Supply Team",           supply_total, _SUPPLY_COLOR,  False, supply_delta),
    ])

    st.html("<div style='height:20px'></div>")

    # ── Charts ────────────────────────────────────────────────────────────────
    bar_colors = [
        _IR_COLOR, _IR_COLOR, _IR_COLOR, _IR_COLOR,
        _RENTAL_COLOR, _RENTAL_COLOR, _RENTAL_COLOR, _RENTAL_COLOR,
        _SUPPLY_COLOR, _SUPPLY_COLOR,
    ]
    sections_data = {
        "Sub. Offers":   kpis["ir_pending_offers"],
        "PM Plan":       kpis["ir_pm_plan_missing"],
        "Home Ins.":     kpis["ir_home_insurance"],
        "Client Info":   kpis["ir_missing_client"],
        "Sin PM":        kpis["rental_unassigned_pm"],
        "Ready-Rent":    kpis["rental_ready_to_rent"],
        "Miss. Lease":   kpis["rental_missing_lease"],
        "Sub. Formal.":  kpis["rental_sub_formal"],
        "Key Data":      kpis["supply_missing_kd"],
        "Tenanted":      kpis["supply_tenanted"],
    }
    area_totals = {
        "👥 IR & Coaches": ir_total,
        "🏪 Rental Team":  rental_total,
        "📍 Supply Team":  supply_total,
    }

    col_bar, col_donut = st.columns([3, 2])
    with col_bar:
        st.html(f'<p style="font-size:13px;font-weight:700;color:{SPACE_BLUE};font-family:Manrope;margin:0">Alertas por sección</p>')
        st.plotly_chart(
            _bar_chart(sections_data, bar_colors),
            use_container_width=True, config={"displayModeBar": False},
        )
    with col_donut:
        st.html(f'<p style="font-size:13px;font-weight:700;color:{SPACE_BLUE};font-family:Manrope;margin:0">Distribución por área</p>')
        st.plotly_chart(
            _donut_chart(area_totals),
            use_container_width=True, config={"displayModeBar": False},
        )

    # ── WoW trend chart ───────────────────────────────────────────────────────
    trend_df = get_trend_data()
    if len(trend_df) > 1:
        st.html(f'<p style="font-size:13px;font-weight:700;color:{SPACE_BLUE};font-family:Manrope;margin:4px 0 0 0">Evolución semanal (Week over Week)</p>')
        st.plotly_chart(
            _trend_chart(trend_df),
            use_container_width=True, config={"displayModeBar": False},
        )
    else:
        st.html(
            f'<div style="background:{SAND};border-radius:10px;padding:14px 18px;'
            f'font-family:\'Manrope\',sans-serif;color:{SPACE_BLUE};font-size:13px;margin-top:4px">'
            f'📈 El gráfico de evolución semanal aparecerá cuando se acumulen datos de al menos 2 semanas. '
            f'Los datos de <b>{wk}</b> ya están guardados.</div>'
        )

    st.html("<div style='height:16px'></div>")

    # ── Per-area breakdown ────────────────────────────────────────────────────
    col_ir, col_rental, col_supply = st.columns(3)

    with col_ir:
        _area_col(_IR_COLOR, "👥", "IR &amp; Coaches", [
            ("📄 Pending Sub. Offers",  kpis["ir_pending_offers"],  "ir_pending_offers",  True),
            ("📋 PM Selected Plan",     kpis["ir_pm_plan_missing"], "ir_pm_plan_missing", True),
            ("🛡️ Home Insurance",      kpis["ir_home_insurance"],  "ir_home_insurance",  False),
            ("🪪 Missing Client Info",  kpis["ir_missing_client"],  "ir_missing_client",  False),
        ], deltas)

    with col_rental:
        _area_col(_RENTAL_COLOR, "🏪", "Rental Team", [
            ("👤 Sin PM Asignado",      kpis["rental_unassigned_pm"], "rental_unassigned_pm", True),
            ("📅 Ready-to-Rent Gaps",  kpis["rental_ready_to_rent"], "rental_ready_to_rent", False),
            ("📋 Missing Lease",        kpis["rental_missing_lease"], "rental_missing_lease", False),
            ("📑 Sub. Formalisation",   kpis["rental_sub_formal"],    "rental_sub_formal",    False),
        ], deltas)

    with col_supply:
        _area_col(_SUPPLY_COLOR, "📍", "Supply Team", [
            ("🗺️ Missing Key Data",    kpis["supply_missing_kd"], "supply_missing_kd", True),
            ("🏢 Already Tenanted",    kpis["supply_tenanted"],   "supply_tenanted",   False),
        ], deltas)
