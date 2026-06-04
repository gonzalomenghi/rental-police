import streamlit as st
import pandas as pd
from utils.ui import kpi_row, show_detail, CRITICAL_RED, WARNING_ORANGE, OCEAN_BLUE
from utils.filters import (
    section_supply_missing_key_data, section_supply_missing_key_data_detail,
    section_already_tenanted, section_already_tenanted_detail,
    is_empty,
)


def _drill_down(result: pd.DataFrame, row_idx: int, gap_cols: dict,
                detail_fn, df: pd.DataFrame, lead_col: str, section_key: str):
    """
    gap_cols: {label: result_column_name}
    Shows radio if multiple gap types have data, direct selection if only one.
    """
    row         = result.iloc[row_idx]
    supply_lead = row[lead_col]
    available   = [label for label, col in gap_cols.items() if row[col] > 0]
    if not available:
        return
    if len(available) == 1:
        gap_type = available[0]
    else:
        gap_type = st.radio(
            "Tipo de dato faltante:",
            available,
            horizontal=True,
            key=f"{section_key}_{supply_lead}",
        )
    detail = detail_fn(df, supply_lead=supply_lead, gap_type=gap_type)
    show_detail(detail, f"{supply_lead} — {gap_type}")


def render(df: pd.DataFrame, filters: dict):
    if filters.get("supply_leads"):
        df = df[df["supply_lead"].isin(filters["supply_leads"])]

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1 — Missing Key Data
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("🗺️ Missing Key Data", expanded=True):
        st.caption(
            "Propiedades sin `suburb_section_name` o `area_cluster`. Solo España, no-test, prioridad High."
        )
        result  = section_supply_missing_key_data(df)
        no_lead = int(is_empty(df["supply_lead"]).sum())

        if result.empty:
            kpi_row([("🚩 Propiedades sin supply_lead", no_lead, CRITICAL_RED, True)])
            st.success("Sin alertas activas en geografía.")
        else:
            total_suburb  = int(result["Unitsw_no_Suburb_section_name"].sum())
            total_cluster = int(result["Unitsw_no_area_cluster"].sum())

            kpi_row([
                ("🚩 Sin supply_lead",    no_lead,       CRITICAL_RED,   True),
                ("Sin suburb section",    total_suburb,  WARNING_ORANGE, False),
                ("Sin area cluster",      total_cluster, WARNING_ORANGE, False),
            ])
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            event = st.dataframe(
                result, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                _drill_down(
                    result, event.selection.rows[0],
                    gap_cols={
                        "Sin suburb section": "Unitsw_no_Suburb_section_name",
                        "Sin area cluster":   "Unitsw_no_area_cluster",
                    },
                    detail_fn=section_supply_missing_key_data_detail,
                    df=df, lead_col="supply_lead", section_key="sec1",
                )

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2 — Already Tenanted Properties
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("🏢 Already Tenanted Properties", expanded=True):
        st.caption(
            "`already_tenanted = Yes`, `contract_date > 2025-01-01`. Al menos un doc sin ✅ Ready."
        )
        result = section_already_tenanted(df)

        if result.empty:
            st.success("Sin alertas activas.")
        else:
            total          = int(result["count"].sum())
            miss_tenant    = int(result["missing_tenant"].sum())
            miss_rental    = int(result["missing_rental"].sum())
            miss_insurance = int(result["missing_insurance"].sum())

            kpi_row([
                ("Total alertas",       total,          CRITICAL_RED,   True),
                ("Missing tenant info", miss_tenant,    WARNING_ORANGE, False),
                ("Missing rental docs", miss_rental,    WARNING_ORANGE, False),
                ("Missing insurance",   miss_insurance, WARNING_ORANGE, False),
            ])
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            event = st.dataframe(
                result, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                _drill_down(
                    result, event.selection.rows[0],
                    gap_cols={
                        "Missing tenant info": "missing_tenant",
                        "Missing rental docs": "missing_rental",
                        "Missing insurance":   "missing_insurance",
                    },
                    detail_fn=section_already_tenanted_detail,
                    df=df, lead_col="supply_lead", section_key="sec2",
                )
