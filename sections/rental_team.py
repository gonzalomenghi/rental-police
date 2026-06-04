import streamlit as st
import pandas as pd
from utils.ui import kpi_row, show_detail, CRITICAL_RED, WARNING_ORANGE, OCEAN_BLUE
from utils.filters import (
    is_empty,
    section_unassigned_pm,
    section_ready_to_rent_gaps, section_ready_to_rent_gaps_detail,
    section_missing_lease, section_missing_lease_detail,
    section_subscription_formalisation, section_subscription_formalisation_detail,
)


def render(df: pd.DataFrame, filters: dict):
    if filters.get("rental_leads"):
        df = df[df["rental_lead"].isin(filters["rental_leads"])]

    df = df[~is_empty(df["rental_lead"])]

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
            settled = int((result["stage"].str.lower() == "settled").sum())
            leased  = int((result["stage"].str.lower() == "property leased").sum())

            kpi_row([
                ("🚩 Sin PM asignado",      len(result), CRITICAL_RED,   True),
                ("Stage: Settled",          settled,     WARNING_ORANGE, False),
                ("Stage: Property leased",  leased,      WARNING_ORANGE, False),
            ])
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.dataframe(result, use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2 — Ready-to-Rent Data Gaps
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("📅 Ready-to-Rent Data Gaps", expanded=True):
        st.caption(
            "Fechas clave faltantes en propiedades Published / Ready to rent / Tenant found, agrupadas por Rental Lead."
        )
        result = section_ready_to_rent_gaps(df)

        if result.empty:
            st.success("Sin alertas activas.")
        else:
            miss_real  = int(result["Pending - Real Ready Date"].sum())
            miss_ready = int(result["Pending - Ready Date"].sum())
            miss_delay = int(result["Pending - Delay reason"].sum())

            kpi_row([
                ("Pending real ready date", miss_real,  CRITICAL_RED,   True),
                ("Pending ready date",       miss_ready, WARNING_ORANGE, False),
                ("Pending delay reason",     miss_delay, WARNING_ORANGE, False),
            ])
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            GAP_COLS = ["Pending - Real Ready Date", "Pending - Ready Date", "Pending - Delay reason"]
            event = st.dataframe(
                result, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                row         = result.iloc[event.selection.rows[0]]
                rental_lead = row["rental_lead"]
                available   = [c for c in GAP_COLS if row[c] > 0]
                if len(available) == 1:
                    gap_type = available[0]
                else:
                    gap_type = st.radio(
                        "Tipo de dato faltante:",
                        available,
                        horizontal=True,
                        key=f"gap_{rental_lead}",
                    )
                detail = section_ready_to_rent_gaps_detail(df, rental_lead=rental_lead, gap_type=gap_type)
                show_detail(detail, f"{rental_lead} — {gap_type}")

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3 — Missing Lease & Subscription Info
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("📋 Missing Lease & Subscription Info", expanded=True):
        st.caption(
            "Datos de cierre contractual faltantes una vez encontrado el inquilino."
        )

        # Sub-bloque A
        st.markdown("**Sub-A — Missing Lease**")
        lease_result = section_missing_lease(df).reset_index(drop=True)
        if lease_result.empty:
            st.success("Sin alertas activas.")
        else:
            kpi_row([
                ("Total alertas sub-A", int(lease_result["count"].sum()), CRITICAL_RED, True),
            ])
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            event = st.dataframe(
                lease_result, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                row    = lease_result.iloc[event.selection.rows[0]]
                detail = section_missing_lease_detail(df, stage=row["stage"], rental_lead=row["rental_lead"])
                show_detail(detail, f"{row['stage']} / {row['rental_lead']}")

        st.markdown("---")

        # Sub-bloque B
        st.markdown("**Sub-B — Subscription Plan Formalisation**")
        sub_result = section_subscription_formalisation(df).reset_index(drop=True)
        if sub_result.empty:
            st.success("Sin alertas activas.")
        else:
            kpi_row([
                ("Total alertas sub-B", int(sub_result["count"].sum()), CRITICAL_RED, True),
            ])
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            event = st.dataframe(
                sub_result, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                row    = sub_result.iloc[event.selection.rows[0]]
                detail = section_subscription_formalisation_detail(df, stage=row["stage"], rental_lead=row["rental_lead"])
                show_detail(detail, f"{row['stage']} / {row['rental_lead']}")
