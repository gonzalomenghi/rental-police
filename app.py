import streamlit as st
import pandas as pd

from utils.data import load_data
from sections import ir_coaches, rental_team, supply_team

# ── Configuración de página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rental Police",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS mínimo para ajustar look ───────────────────────────────────────────────
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { background: #1a1a2e; }
    [data-testid="stSidebar"] * { color: #f0f0f0 !important; }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] { background: #3a3a5c; }
    div[data-testid="metric-container"] { background: #f5f5f5; border-radius: 8px; padding: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Carga de datos ─────────────────────────────────────────────────────────────
df = load_data()

# ── Sidebar — Header ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ Rental Police")
    st.markdown("*Quality control & audit dashboard*")
    st.markdown("---")

    st.markdown("### Filtros globales")

    # IR Names
    ir_options = sorted(df["investor_relations_name"].dropna().unique().tolist())
    ir_filter  = st.multiselect("IR Name", ir_options, placeholder="Todos")

    # Coaches
    coach_options = sorted(df["coach"].dropna().unique().tolist())
    coach_filter  = st.multiselect("Coach", coach_options, placeholder="Todos")

    # Rental Leads
    rl_options = sorted(df["rental_lead"].dropna().unique().tolist())
    rl_filter  = st.multiselect("Rental Lead", rl_options, placeholder="Todos")

    # Supply Leads
    sl_options = sorted(df["supply_lead"].dropna().unique().tolist())
    sl_filter  = st.multiselect("Supply Lead", sl_options, placeholder="Todos")

    # Prioridad
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

    st.markdown(
        f"<div style='font-size:11px;color:#888;margin-top:8px'>"
        f"{len(df):,} registros cargados</div>",
        unsafe_allow_html=True,
    )

# ── Diccionario de filtros para pasar a cada pestaña ──────────────────────────
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
    st.title("🛡️ Rental Police")
    st.caption("Sistema de control de calidad y auditoría de tareas pendientes")
with col_meta:
    active = sum([
        bool(ir_filter), bool(coach_filter),
        bool(rl_filter), bool(sl_filter), bool(priority_filter),
    ])
    if active:
        st.info(f"{active} filtro(s) activo(s)")

# ── Pestañas principales ───────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "👥 IR & Coaches Team",
    "🏪 Rental Team",
    "📍 Supply Team",
])

with st.expander("🔍 DEBUG — columnas del CSV (eliminar después)", expanded=False):
    st.write(sorted(df.columns.tolist()))

with tab1:
    try:
        ir_coaches.render(df, filters)
    except Exception as e:
        st.error(f"Error en Tab 1: {e}")

with tab2:
    try:
        rental_team.render(df, filters)
    except Exception as e:
        st.error(f"Error en Tab 2: {e}")

with tab3:
    try:
        supply_team.render(df, filters)
    except Exception as e:
        st.error(f"Error en Tab 3: {e}")
