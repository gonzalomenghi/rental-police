import streamlit as st
import pandas as pd
from utils.filters import (
    section_unassigned_pm,
    section_ready_to_rent_gaps,
    section_missing_lease,
    section_subscription_formalisation,
)


def _kpi_row(cols_data: list[tuple[str, int, str]]):
    cols = st.columns(len(cols_data))
    for col, (label, value, color) in zip(cols, cols_data):
        with col:
            st.markdown(
                f"""<div style="background:#f5f5f5;border-radius:8px;padding:12px 16px;">
                <div style="font-size:12px;color:#888;margin-bottom:4px">{label}</div>
                <div style="font-size:24px;font-weight:500;color:{color}">{value}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def render(df: pd.DataFrame, filters: dict):
    """Renderiza la pestaña Rental Team."""

    if filters.get("rental_leads"):
        df = df[df["rental_lead"].isin(filters["rental_leads"])]

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1 — Unassigned Property Managers
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("👤 Unassigned Property Managers", expanded=True):
        st.caption(
            "Propiedades en Settled / Property Leased con `pm_company` totalmente vacío."
        )
        result = section_unassigned_pm(df)

        if result.empty:
            st.success("Sin alertas activas.")
        else:
            settled  = int((result["stage"].str.lower() == "settled").sum())
            leased   = int((result["stage"].str.lower() == "property leased").sum())

            _kpi_row([
                ("Sin PM asignado",      len(result), "#A32D2D"),
                ("Stage: Settled",       settled,     "#854F0B"),
                ("Stage: Property leased", leased,    "#854F0B"),
            ])
            st.markdown("---")
            st.dataframe(result, use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2 — Ready-to-Rent Data Gaps
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("📅 Ready-to-Rent Data Gaps", expanded=True):
        st.caption(
            "Fechas clave faltantes en propiedades Published / Ready to rent / Tenant found."
        )
        result = section_ready_to_rent_gaps(df)

        if result.empty:
            st.success("Sin alertas activas.")
        else:
            miss_real  = int(result["miss_real_ready"].sum())
            miss_ready = int(result["miss_ready"].sum())
            miss_delay = int(result["miss_delay"].sum())

            _kpi_row([
                ("Pending real ready date", miss_real,  "#A32D2D"),
                ("Pending ready date",      miss_ready, "#854F0B"),
                ("Pending delay reason",    miss_delay, "#854F0B"),
            ])
            st.markdown("---")

            display_cols = [
                "uniqueid", "stage", "set_up_status",
                "miss_real_ready", "miss_ready", "miss_delay", "total_missing",
            ]
            available = [c for c in display_cols if c in result.columns]
            st.dataframe(result[available], use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3 — Missing Lease & Subscription Info
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("📋 Missing Lease & Subscription Info", expanded=True):
        st.caption(
            "Datos de cierre contractual faltantes una vez encontrado el inquilino."
        )

        # Sub-bloque A
        st.markdown("**Sub-A — Missing Lease**")
        lease_result = section_missing_lease(df)
        if lease_result.empty:
            st.success("Sin alertas activas.")
        else:
            _kpi_row([("Total alertas sub-A", int(lease_result["count"].sum()), "#A32D2D")])
            st.dataframe(lease_result, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Sub-bloque B
        st.markdown("**Sub-B — Subscription Plan Formalisation**")
        sub_result = section_subscription_formalisation(df)
        if sub_result.empty:
            st.success("Sin alertas activas.")
        else:
            _kpi_row([("Total alertas sub-B", int(sub_result["count"].sum()), "#A32D2D")])
            st.dataframe(sub_result, use_container_width=True, hide_index=True)
