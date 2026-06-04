import streamlit as st
import pandas as pd
from utils.ui import kpi_row, show_detail, CRITICAL_RED, WARNING_ORANGE, OCEAN_BLUE
from utils.filters import (
    section_pending_offers, section_pending_offers_detail,
    section_pm_plan_missing, section_pm_plan_missing_detail,
    section_home_insurance, section_home_insurance_detail,
    section_missing_client_info, section_missing_client_info_detail,
)


def _make_pivot(result: pd.DataFrame, index_col: str, label_col: str) -> pd.DataFrame:
    pivot = (
        result.pivot_table(
            index=index_col,
            columns="priority_tier",
            values="alertas",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
        .rename(columns={index_col: label_col})
    )
    pivot["Total"] = pivot.select_dtypes("number").sum(axis=1)
    return pivot.sort_values("Total", ascending=False).reset_index(drop=True)


def _drill_down(pivot: pd.DataFrame, owner_col: str, row_idx: int,
                detail_fn, df: pd.DataFrame, owner_kwarg: str, section_key: str):
    """Show detail for the selected row; radio selector when multiple tiers have data."""
    owner         = pivot.iloc[row_idx][owner_col]
    priority_cols = [c for c in pivot.columns if c not in (owner_col, "Total")]
    available     = [c for c in priority_cols if pivot.iloc[row_idx][c] > 0]
    if not available:
        return
    if len(available) == 1:
        selected = available[0]
    else:
        selected = st.radio(
            "Seleccionar prioridad:",
            available,
            horizontal=True,
            key=f"{section_key}_{owner}",
        )
    detail = detail_fn(df, **{owner_kwarg: owner}, priority_tier=selected)
    show_detail(detail, f"{owner} — {selected}")


def render(df: pd.DataFrame, filters: dict):
    if filters.get("ir_names"):
        df = df[df["investor_relations_name"].isin(filters["ir_names"])]
    if filters.get("coaches"):
        df = df[df["coach"].isin(filters["coaches"])]
    if filters.get("priority"):
        from utils.filters import add_priority_tier
        df = add_priority_tier(df)
        df = df[df["priority_tier"].isin(filters["priority"])]

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1 — Pending Subscription Offers & PM Selected Plan Missing
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("📄 Pending Subscription Offers & PM Selected Plan", expanded=True):

        # ── Sub-A: Pending Subscription Offers ───────────────────────────
        st.markdown("**Sub-A — Pending Subscription Offers**")
        st.caption("Falta `subscription_plan_offer` — bloquea el envío automático de contratos.")
        result = section_pending_offers(df)

        if result.empty:
            st.success("Sin alertas activas.")
        else:
            total     = int(result["alertas"].sum())
            post_reno = int(result[result["priority_tier"].str.contains("Alta",  na=False)]["alertas"].sum())
            pre_reno  = int(result[result["priority_tier"].str.contains("Media", na=False)]["alertas"].sum())
            n_users   = result["investor_relations_name"].nunique()

            kpi_row([
                ("Total alertas",         total,     CRITICAL_RED,   True),
                ("Post-Reno (alta) 🚩",   post_reno, CRITICAL_RED,   True),
                ("Pre-Reno (media)",       pre_reno,  WARNING_ORANGE, False),
                ("IR usuarios afectados",  n_users,   OCEAN_BLUE,     False),
            ])
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            pivot = _make_pivot(result, "investor_relations_name", "IR Name")
            event = st.dataframe(
                pivot, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                _drill_down(pivot, "IR Name", event.selection.rows[0],
                            section_pending_offers_detail, df, "ir_name", "sec1a")

        st.markdown("---")

        # ── Sub-B: PM Selected Plan Missing ──────────────────────────────
        st.markdown("**Sub-B — PM Selected Plan Missing**")
        st.caption("Falta `pm_selected_plan` — sin plan de gestión asignado.")
        result_pm = section_pm_plan_missing(df)

        if result_pm.empty:
            st.success("Sin alertas activas.")
        else:
            total_pm     = int(result_pm["alertas"].sum())
            post_reno_pm = int(result_pm[result_pm["priority_tier"].str.contains("Alta",  na=False)]["alertas"].sum())
            pre_reno_pm  = int(result_pm[result_pm["priority_tier"].str.contains("Media", na=False)]["alertas"].sum())
            n_users_pm   = result_pm["investor_relations_name"].nunique()

            kpi_row([
                ("Total alertas",         total_pm,     CRITICAL_RED,   True),
                ("Post-Reno (alta) 🚩",   post_reno_pm, CRITICAL_RED,   True),
                ("Pre-Reno (media)",       pre_reno_pm,  WARNING_ORANGE, False),
                ("IR usuarios afectados",  n_users_pm,   OCEAN_BLUE,     False),
            ])
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            pivot_pm = _make_pivot(result_pm, "investor_relations_name", "IR Name")
            event_pm = st.dataframe(
                pivot_pm, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event_pm.selection.rows:
                _drill_down(pivot_pm, "IR Name", event_pm.selection.rows[0],
                            section_pm_plan_missing_detail, df, "ir_name", "sec1b")

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2 — Home Insurance Tracking
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("🛡️ Home Insurance Tracking", expanded=True):
        st.caption(
            "Falta `home_insurance_offer`, `home_insurance_choice`, o `home_insurance_type` cuando choice = PropHero."
        )
        result = section_home_insurance(df)

        if result.empty:
            st.success("Sin alertas activas.")
        else:
            total     = int(result["alertas"].sum())
            post_reno = int(result[result["priority_tier"].str.contains("Alta",  na=False)]["alertas"].sum())
            pre_reno  = int(result[result["priority_tier"].str.contains("Media", na=False)]["alertas"].sum())

            kpi_row([
                ("Total alertas",      total,     CRITICAL_RED,   True),
                ("Post-Reno (alta) 🚩", post_reno, CRITICAL_RED,   True),
                ("Pre-Reno (media)",    pre_reno,  WARNING_ORANGE, False),
            ])
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            pivot = _make_pivot(result, "investor_relations_name", "IR Name")
            event = st.dataframe(
                pivot, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                _drill_down(pivot, "IR Name", event.selection.rows[0],
                            section_home_insurance_detail, df, "ir_name", "sec2")

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3 — Missing Client's Info
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("🪪 Missing Client's Info", expanded=True):
        st.caption(
            "Falta cualquiera de: `client_full_name`, `client_email`, `tech_bank_ownership_proof_urls`, `tech_id_copy_urls`."
        )
        result = section_missing_client_info(df)

        if result.empty:
            st.success("Sin alertas activas.")
        else:
            total   = int(result["alertas"].sum())
            n_coach = result["coach"].nunique()

            kpi_row([
                ("Total alertas",     total,   CRITICAL_RED, True),
                ("Coaches afectados", n_coach, OCEAN_BLUE,   False),
            ])
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            pivot = _make_pivot(result, "coach", "Coach")
            event = st.dataframe(
                pivot, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                _drill_down(pivot, "Coach", event.selection.rows[0],
                            section_missing_client_info_detail, df, "coach", "sec3")
