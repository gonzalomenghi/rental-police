import streamlit as st
import pandas as pd
from utils.filters import (
    section_supply_missing_key_data, section_supply_missing_key_data_detail,
    section_already_tenanted, section_already_tenanted_detail,
    is_empty,
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


def _show_detail(detail: pd.DataFrame, label: str):
    if not detail.empty:
        st.caption(f"📋 Detalle — **{label}** ({len(detail)} registros)")
        st.dataframe(detail, use_container_width=True, hide_index=True)


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
        result = section_supply_missing_key_data(df)

        no_lead = int(is_empty(df["supply_lead"]).sum())

        if result.empty:
            _kpi_row([("Propiedades sin supply_lead", no_lead, "#A32D2D")])
            st.success("Sin alertas activas en geografía.")
        else:
            total_suburb  = int(result["Unitsw_no_Suburb_section_name"].sum())
            total_cluster = int(result["Unitsw_no_area_cluster"].sum())

            _kpi_row([
                ("Sin supply_lead",    no_lead,       "#A32D2D"),
                ("Sin suburb section", total_suburb,  "#854F0B"),
                ("Sin area cluster",   total_cluster, "#854F0B"),
            ])
            st.markdown("---")

            event = st.dataframe(
                result, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                supply_lead = result.iloc[event.selection.rows[0]]["supply_lead"]
                _show_detail(section_supply_missing_key_data_detail(df, supply_lead=supply_lead), supply_lead)

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

            _kpi_row([
                ("Total alertas",       total,          "#A32D2D"),
                ("Missing tenant info", miss_tenant,    "#854F0B"),
                ("Missing rental docs", miss_rental,    "#854F0B"),
                ("Missing insurance",   miss_insurance, "#854F0B"),
            ])
            st.markdown("---")

            event = st.dataframe(
                result, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                supply_lead = result.iloc[event.selection.rows[0]]["supply_lead"]
                _show_detail(section_already_tenanted_detail(df, supply_lead=supply_lead), supply_lead)
