import streamlit as st
import pandas as pd

from utils.data import load_data
from sections import ir_coaches, rental_team, supply_team, summary

# ── Configuración de página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rental Police",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand Design System CSS ────────────────────────────────────────────────────
# Palette: Ocean Blue #009CDF | Space Blue #26204E | Sky Blue #A5D7FC | Sand #E8E2DC
# Font: Manrope — applied via body (inherits to content); NOT via * !important
# which would break Streamlit's Material Icons (expander arrows, etc.).
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap');

    /* ── Base font via inheritance — does NOT override icon fonts ─────────── */
    body { font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif; }

    /* ── Sidebar — Space Blue ─────────────────────────────────────────────── */
    [data-testid="stSidebar"] { background: #26204E !important; }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown * { color: #E8E2DC !important; }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background: #009CDF !important; color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] span {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] hr { border-color: #3d3660 !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: #009CDF !important; color: #FFFFFF !important;
        border: none !important; border-radius: 8px !important;
        font-weight: 600 !important; width: 100%;
    }

    /* ── Tab navigation ───────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px; background: #F5F2EE;
        padding: 5px 6px; border-radius: 10px; margin-bottom: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600 !important; font-size: 14px !important;
        color: #26204E !important; border-radius: 7px !important;
        padding: 7px 16px !important; border: none !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: #26204E !important; color: #FFFFFF !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }

    /* ── Expander parcels ─────────────────────────────────────────────────── */
    [data-testid="stExpander"] {
        border: 1px solid #E8E2DC !important; border-radius: 12px !important;
        overflow: hidden; margin-bottom: 14px !important;
        box-shadow: 0 1px 4px rgba(38,32,78,0.07) !important;
    }
    [data-testid="stExpander"] > details > summary {
        background: #F8F5F2 !important; padding: 12px 16px !important;
        font-weight: 700 !important; font-size: 15px !important;
        color: #26204E !important;
    }
    [data-testid="stExpander"] > details > summary:hover {
        background: #EFE9E3 !important;
    }

    /* ── Misc ─────────────────────────────────────────────────────────────── */
    [data-testid="stAlert"] { border-radius: 8px !important; }
    div[data-testid="metric-container"] { background: transparent !important; }
    .block-container { padding-top: 1.5rem !important; max-width: 1400px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Carga de datos ─────────────────────────────────────────────────────────────
df = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.html(
        '<div style="font-family:\'Manrope\',sans-serif;margin-bottom:4px">'
        '<div style="font-size:20px;font-weight:700;color:#FFFFFF">🛡️ Rental Police</div>'
        '<div style="font-size:12px;color:#A5D7FC;margin-top:2px">Quality control &amp; audit dashboard</div>'
        '</div>'
    )
    st.markdown("---")
    st.markdown("### Filtros globales")

    ir_options    = sorted(df["investor_relations_name"].dropna().unique().tolist())
    ir_filter     = st.multiselect("IR Name", ir_options, placeholder="Todos")

    coach_options = sorted(df["coach"].dropna().unique().tolist())
    coach_filter  = st.multiselect("Coach", coach_options, placeholder="Todos")

    rl_options    = sorted(df["rental_lead"].dropna().unique().tolist())
    rl_filter     = st.multiselect("Rental Lead", rl_options, placeholder="Todos")

    sl_options    = sorted(df["supply_lead"].dropna().unique().tolist())
    sl_filter     = st.multiselect("Supply Lead", sl_options, placeholder="Todos")

    st.markdown("---")
    st.markdown("### Prioridad")
    priority_filter = st.multiselect(
        "Tier",
        ["🔴 Post-Reno (Alta)", "🟡 Pre-Reno (Media)", "Sin prioridad definida"],
        placeholder="Todas",
    )

    st.markdown("---")
    if st.button("🔄 Refrescar datos"):
        st.cache_data.clear()
        st.rerun()

    st.html(
        f'<div style="font-size:11px;color:#A5D7FC;margin-top:8px">'
        f'{len(df):,} registros cargados</div>'
    )

# ── Filtros globales ───────────────────────────────────────────────────────────
filters = {
    "ir_names":     ir_filter,
    "coaches":      coach_filter,
    "rental_leads": rl_filter,
    "supply_leads": sl_filter,
    "priority":     priority_filter,
}

# ── Header principal ───────────────────────────────────────────────────────────
col_title, col_meta = st.columns([3, 1])
with col_title:
    st.html(
        '<div style="font-family:\'Manrope\',sans-serif;margin-bottom:4px">'
        '<div style="font-size:28px;font-weight:700;color:#26204E">🛡️ Rental Police</div>'
        '<div style="font-size:13px;color:#666">'
        'Sistema de control de calidad y auditoría de tareas pendientes</div>'
        '</div>'
    )
with col_meta:
    active = sum([
        bool(ir_filter), bool(coach_filter),
        bool(rl_filter), bool(sl_filter), bool(priority_filter),
    ])
    if active:
        st.info(f"{active} filtro(s) activo(s)")

# ── Pestañas principales ───────────────────────────────────────────────────────
tab0, tab1, tab2, tab3 = st.tabs([
    "📊 Dashboard",
    "👥 IR & Coaches Team",
    "🏪 Rental Team",
    "📍 Supply Team",
])

with tab0:
    summary.render(df, filters)

with tab1:
    ir_coaches.render(df, filters)

with tab2:
    rental_team.render(df, filters)

with tab3:
    supply_team.render(df, filters)
