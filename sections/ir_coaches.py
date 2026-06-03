import streamlit as st
import pandas as pd
from utils.filters import (
    section_pending_offers,
    section_home_insurance,
    section_missing_client_info,
)


def _kpi_row(cols_data: list[tuple[str, int, str]]):
    """Renderiza una fila de KPI cards. cols_data = [(label, value, color), ...]"""
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


def _priority_badge(tier: str) -> str:
    if "Alta" in tier:
        return "🔴"
    if "Media" in tier:
        return "🟡"
    return "⚪"


def render(df: pd.DataFrame, filters: dict):
    """Renderiza la pestaña IR & Coaches Team."""

    # ── Aplicar filtros de sidebar ────────────────────────────────────────
    if filters.get("ir_names"):
        df = df[df["investor_relations_name"].isin(filters["ir_names"])]
    if filters.get("coaches"):
        df = df[df["coach"].isin(filters["coaches"])]
    if filters.get("priority"):
        from utils.filters import add_priority_tier, POST_RENO_STATUSES, PRE_RENO_STATUSES
        df = add_priority_tier(df)
        df = df[df["priority_tier"].isin(filters["priority"])]

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1 — Pending Subscription Offers
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("📄 Pending Subscription Offers", expanded=True):
        st.caption(
            "Falta `subscription_plan_offer` o `pm_selected_plan` — bloquea el envío automático de contratos."
        )
        result = section_pending_offers(df)

        if result.empty:
            st.success("Sin alertas activas.")
        else:
            total       = int(result["alertas"].sum())
            post_reno   = int(result[result["priority_tier"].str.contains("Alta",  na=False)]["alertas"].sum())
            pre_reno    = int(result[result["priority_tier"].str.contains("Media", na=False)]["alertas"].sum())
            n_users     = result["investor_relations_name"].nunique()

            _kpi_row([
                ("Total alertas",        total,     "#A32D2D"),
                ("Post-Reno (alta)",     post_reno, "#A32D2D"),
                ("Pre-Reno (media)",     pre_reno,  "#854F0B"),
                ("IR usuarios afectados", n_users,  "#185FA5"),
            ])
            st.markdown("---")

            # Tabla agrupada
            pivot = (
                result.pivot_table(
                    index="investor_relations_name",
                    columns="priority_tier",
                    values="alertas",
                    aggfunc="sum",
                    fill_value=0,
                )
                .reset_index()
                .rename(columns={"investor_relations_name": "IR Name"})
            )
            pivot["Total"] = pivot.select_dtypes("number").sum(axis=1)
            pivot = pivot.sort_values("Total", ascending=False)
            st.dataframe(pivot, use_container_width=True, hide_index=True)

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

            _kpi_row([
                ("Total alertas",    total,     "#A32D2D"),
                ("Post-Reno (alta)", post_reno, "#A32D2D"),
                ("Pre-Reno (media)", pre_reno,  "#854F0B"),
            ])
            st.markdown("---")

            pivot = (
                result.pivot_table(
                    index="investor_relations_name",
                    columns="priority_tier",
                    values="alertas",
                    aggfunc="sum",
                    fill_value=0,
                )
                .reset_index()
                .rename(columns={"investor_relations_name": "IR Name"})
            )
            pivot["Total"] = pivot.select_dtypes("number").sum(axis=1)
            pivot = pivot.sort_values("Total", ascending=False)
            st.dataframe(pivot, use_container_width=True, hide_index=True)

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

            _kpi_row([
                ("Total alertas",    total,   "#A32D2D"),
                ("Coaches afectados", n_coach, "#185FA5"),
            ])
            st.markdown("---")

            pivot = (
                result.pivot_table(
                    index="coach",
                    columns="priority_tier",
                    values="alertas",
                    aggfunc="sum",
                    fill_value=0,
                )
                .reset_index()
            )
            pivot["Total"] = pivot.select_dtypes("number").sum(axis=1)
            pivot = pivot.sort_values("Total", ascending=False)
            st.dataframe(pivot, use_container_width=True, hide_index=True)
