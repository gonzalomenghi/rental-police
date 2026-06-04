import streamlit as st
import pandas as pd
from utils.filters import (
    section_pending_offers, section_pending_offers_detail,
    section_home_insurance, section_home_insurance_detail,
    section_missing_client_info, section_missing_client_info_detail,
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


def _drill_down(pivot: pd.DataFrame, owner_col: str, row_idx: int, detail_fn, df: pd.DataFrame, owner_kwarg: str, section_key: str):
    """Muestra detalle para la fila seleccionada. Si hay múltiples tiers, muestra radio."""
    owner = pivot.iloc[row_idx][owner_col]
    priority_cols = [c for c in pivot.columns if c not in (owner_col, "Total")]
    # Solo tiers con datos en esa fila
    available = [c for c in priority_cols if pivot.iloc[row_idx][c] > 0]
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
    _show_detail(detail, f"{owner} — {selected}")


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
            total     = int(result["alertas"].sum())
            post_reno = int(result[result["priority_tier"].str.contains("Alta",  na=False)]["alertas"].sum())
            pre_reno  = int(result[result["priority_tier"].str.contains("Media", na=False)]["alertas"].sum())
            n_users   = result["investor_relations_name"].nunique()

            _kpi_row([
                ("Total alertas",         total,     "#A32D2D"),
                ("Post-Reno (alta)",      post_reno, "#A32D2D"),
                ("Pre-Reno (media)",      pre_reno,  "#854F0B"),
                ("IR usuarios afectados", n_users,   "#185FA5"),
            ])
            st.markdown("---")

            pivot = _make_pivot(result, "investor_relations_name", "IR Name")
            event = st.dataframe(
                pivot, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                _drill_down(pivot, "IR Name", event.selection.rows[0],
                            section_pending_offers_detail, df, "ir_name", "sec1")

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

            _kpi_row([
                ("Total alertas",     total,   "#A32D2D"),
                ("Coaches afectados", n_coach, "#185FA5"),
            ])
            st.markdown("---")

            pivot = _make_pivot(result, "coach", "Coach")
            event = st.dataframe(
                pivot, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            if event.selection.rows:
                _drill_down(pivot, "Coach", event.selection.rows[0],
                            section_missing_client_info_detail, df, "coach", "sec3")
