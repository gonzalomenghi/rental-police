import pandas as pd

# ── Constantes de negocio ──────────────────────────────────────────────────────

SUB_PLANS = [
    "Subscription - Premium",
    "Subscription - Room rental",
    "Subscription - Basic",
    "Subscription - Basic + Insurance",
    "Subscription - Premium + Insurance",
]

POST_RENO_STATUSES = [
    "Tenant found (pending to formalize documentation)",
    "Furnishing",
    "Final check",
    "Final check V1",
    "Utilities activation",
    "Cleaning",
    "Published",
    "Ready to sell",
    "Ready to rent",
    "Ready to publish",
    "On Hold",
    "Final check post utilities",
]

PRE_RENO_STATUSES = [
    "Pending to visit",
    "Pending to budget (from renovator)",
    "Pending to validate budget (from client)",
    "Reno to start",
    "Reno in progress",
]

EXCLUDED_ENGAGEMENT_TYPES = ["Value Partner", "Value Hero"]

LEASE_EXCLUDED_PLANS = [
    "Out of PH",
    "Commercialization",
    "Subscription - Room rental",
    "Acomodador",
    "Room rental variable",
    "Rent to rent JJ",
]

SUB_FORMALISATION_PLANS = [
    "Subscription - Premium",
    "Subscription - Basic",
    "Subscription - Basic + Insurance",
    "Subscription - Premium + Insurance"
]


# ── Helpers ────────────────────────────────────────────────────────────────────

DETAIL_COLS = ["uniqueid", "transaction_name", "address", "stage", "set_up_status"]


def _pick_detail(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in DETAIL_COLS if c in df.columns]
    return df[cols].drop_duplicates().reset_index(drop=True)


def is_empty(series: pd.Series) -> pd.Series:
    """True donde el valor es NaN o string vacío/solo espacios."""
    return series.isna() | (series.astype(str).str.strip() == "")


def add_priority_tier(df: pd.DataFrame) -> pd.DataFrame:
    """Añade columna 'priority_tier' según set_up_status."""
    df = df.copy()
    df["priority_tier"] = "Sin prioridad definida"
    df.loc[df["set_up_status"].isin(POST_RENO_STATUSES), "priority_tier"] = "🔴 Post-Reno (Alta)"
    df.loc[df["set_up_status"].isin(PRE_RENO_STATUSES),  "priority_tier"] = "🟡 Pre-Reno (Media)"
    return df


# ── Filtro base para Pestaña 1 (IR & Coaches) ─────────────────────────────────

def base_filter_ir(df: pd.DataFrame) -> pd.DataFrame:
    plan_ok = df["pm_selected_plan"].isin(SUB_PLANS)

    stage_ok = (
        df["stage"].str.contains("Settled|Property Leased|Vacante", na=False, case=False)
        | df["engagement_stage"].str.contains("Settled", na=False, case=False)
    )

    status_ok = df["set_up_status"].isin(POST_RENO_STATUSES + PRE_RENO_STATUSES)

    type_ok = ~df["engagement_type"].isin(EXCLUDED_ENGAGEMENT_TYPES)

    return df[plan_ok & stage_ok & status_ok & type_ok].copy()


# ── Pestaña 1 — Sección 1: Pending Subscription Offers ────────────────────────

def section_pending_offers(df: pd.DataFrame) -> pd.DataFrame:
    base  = add_priority_tier(base_filter_ir(df))
    alert = base[is_empty(base["subscription_plan_offer"])]
    return (
        alert.groupby(["investor_relations_name", "priority_tier"])
        .size()
        .reset_index(name="alertas")
        .sort_values("alertas", ascending=False)
    )


# ── Pestaña 1 — Sección 1B: PM Selected Plan Missing ──────────────────────────

def section_pm_plan_missing(df: pd.DataFrame) -> pd.DataFrame:
    # No filtra por pm_selected_plan (buscamos justamente los que no lo tienen)
    stage_ok  = (
        df["stage"].str.contains("Settled|Property Leased|Vacante", na=False, case=False)
        | df["engagement_stage"].str.contains("Settled", na=False, case=False)
    )
    status_ok = df["set_up_status"].isin(POST_RENO_STATUSES + PRE_RENO_STATUSES)
    type_ok   = ~df["engagement_type"].isin(EXCLUDED_ENGAGEMENT_TYPES)
    base  = add_priority_tier(df[stage_ok & status_ok & type_ok].copy())
    alert = base[is_empty(base["pm_selected_plan"])]
    return (
        alert.groupby(["investor_relations_name", "priority_tier"])
        .size()
        .reset_index(name="alertas")
        .sort_values("alertas", ascending=False)
    )


# ── Pestaña 1 — Sección 2: Home Insurance Tracking ────────────────────────────

def section_home_insurance(df: pd.DataFrame) -> pd.DataFrame:
    base = add_priority_tier(base_filter_ir(df))

    settled_ok = (
        df["stage"].isin(["Settled", "Vacant"])
        | df["engagement_stage"].isin(["Settled"])
    )
    base = base[settled_ok]

    cond = (
        is_empty(base["home_insurance_offer"])
        | is_empty(base["home_insurance_choice"])
        | (
            (base["home_insurance_choice"] == "PropHero")
            & is_empty(base["home_insurance_type"])
        )
    )
    return (
        base[cond]
        .groupby(["investor_relations_name", "priority_tier"])
        .size()
        .reset_index(name="alertas")
        .sort_values("alertas", ascending=False)
    )


# ── Pestaña 1 — Sección 3: Missing Client's Info ──────────────────────────────

def section_missing_client_info(df: pd.DataFrame) -> pd.DataFrame:
    plan_ok = df["pm_selected_plan"].isin(SUB_PLANS)

    stage_ok = (
        df["stage"].isin(["Settled", "Vacant", "Property leased"])
        | df["engagement_stage"].str.contains("Settled", na=False, case=False)
    )

    # solo registros con set_up_status reconocido (post-reno o pre-reno)
    status_ok = df["set_up_status"].isin(POST_RENO_STATUSES + PRE_RENO_STATUSES)

    # engagement_type: NULL pasa el filtro (isin devuelve False para NaN → ~isin True)
    type_ok = ~df["engagement_type"].isin(EXCLUDED_ENGAGEMENT_TYPES)

    base = add_priority_tier(df[plan_ok & stage_ok & status_ok & type_ok].copy())

    cond = (
        is_empty(base["client_full_name"])
        | is_empty(base["client_email"])
        | is_empty(base["tech_bank_ownership_proof_urls"])
        | is_empty(base["tech_id_copy_urls"])
    )
    return (
        base[cond]
        .groupby(["coach", "priority_tier"])
        .size()
        .reset_index(name="alertas")
        .sort_values("alertas", ascending=False)
    )


# ── Pestaña 2 — Sección 1: Unassigned Property Managers ───────────────────────

def section_unassigned_pm(df: pd.DataFrame) -> pd.DataFrame:
    cond = (
        ~df["pm_selected_plan"].isin(["Out of PH", "Commercialization"])
        & df["stage"].isin(["Settled", "Property leased"])
        & is_empty(df["pm_company"])
    )
    return df[cond][
        ["stage", "set_up_status", "address", "uniqueid", "client_full_name"]
    ].copy()


# ── Pestaña 2 — Sección 2: Ready-to-Rent Data Gaps ────────────────────────────

def _ready_to_rent_base(df: pd.DataFrame) -> pd.DataFrame:
    status_ok = df["set_up_status"].isin([
        "Tenant found (pending to formalize documentation)",
        "Published",
        "Ready to rent",
    ])
    stage_ok = df["stage"].isin(["Settled", "Property leased", "Vacant"])
    lead_ok  = ~is_empty(df["rental_lead"])
    base = df[status_ok & stage_ok & lead_ok].copy()
    base["miss_real_ready"] = is_empty(base["real_property_ready_date"]).astype(int)
    base["miss_ready"]      = is_empty(base["property_ready_date"]).astype(int)
    # Delay reason solo se contabiliza cuando real_ready_date > property_ready_date
    real_dt  = pd.to_datetime(base["real_property_ready_date"], errors="coerce")
    prop_dt  = pd.to_datetime(base["property_ready_date"], errors="coerce")
    base["miss_delay"] = (is_empty(base["ready_delay_reason"]) & (real_dt > prop_dt)).astype(int)
    base["total_missing"] = base[["miss_real_ready", "miss_ready", "miss_delay"]].sum(axis=1)
    return base[base["total_missing"] > 0].copy()


def section_ready_to_rent_gaps(df: pd.DataFrame) -> pd.DataFrame:
    base = _ready_to_rent_base(df)
    grouped = (
        base.groupby("rental_lead")[["miss_real_ready", "miss_ready", "miss_delay"]]
        .sum()
        .rename(columns={
            "miss_real_ready": "Pending - Real Ready Date",
            "miss_ready":      "Pending - Ready Date",
            "miss_delay":      "Pending - Delay reason",
        })
        .reset_index()
    )
    grouped["Total"] = grouped[["Pending - Real Ready Date", "Pending - Ready Date", "Pending - Delay reason"]].sum(axis=1)
    return grouped[grouped["Total"] > 0].sort_values("Total", ascending=False).reset_index(drop=True)


def section_ready_to_rent_gaps_detail(df: pd.DataFrame, rental_lead=None, gap_type=None) -> pd.DataFrame:
    base = _ready_to_rent_base(df)
    if rental_lead:
        base = base[base["rental_lead"] == rental_lead]
    if gap_type == "Pending - Real Ready Date":
        base = base[base["miss_real_ready"] > 0]
    elif gap_type == "Pending - Ready Date":
        base = base[base["miss_ready"] > 0]
    elif gap_type == "Pending - Delay reason":
        base = base[base["miss_delay"] > 0]
    return _pick_detail(base)


# ── Pestaña 2 — Sección 3A: Missing Lease ─────────────────────────────────────

def section_missing_lease(df: pd.DataFrame) -> pd.DataFrame:
    plan_ok   = ~df["pm_selected_plan"].isin(LEASE_EXCLUDED_PLANS) | is_empty(df["pm_selected_plan"])
    status_ok = df["set_up_status"] == "Tenant found (pending to formalize documentation)"
    stage_ok  = df["stage"].isin(["Settled", "Property leased", "Vacant"])
    cond_miss = (
        is_empty(df["actual_rent"])
        | is_empty(df["lease_date"])
        | is_empty(df["rent_contract_date"])
    )
    result = df[plan_ok & status_ok & stage_ok & cond_miss]
    return (
        result.groupby(["rental_lead", "stage"])
        .size()
        .reset_index(name="count")
        .sort_values(["count", "rental_lead", "stage"], ascending=[False, True, True])
    )


# ── Pestaña 2 — Sección 3B: Subscription Plan Formalisation ───────────────────

def section_subscription_formalisation(df: pd.DataFrame) -> pd.DataFrame:
    plan_ok   = df["pm_selected_plan"].isin(SUB_FORMALISATION_PLANS)
    status_ok = df["set_up_status"] == "Tenant found (pending to formalize documentation)"
    stage_ok  = df["stage"].isin(["Settled", "Property leased", "Vacant"])
    cond_miss = (
        (~df["subscription_plan_offer"].str.contains("Accepted", na=True))
        | is_empty(df["rent_insurance"])
        | is_empty(df["actual_rent"])
        | is_empty(df["rent_insurance_choice"])
    )
    result = df[plan_ok & status_ok & stage_ok & cond_miss]
    return (
        result.groupby(["rental_lead", "stage"])
        .size()
        .reset_index(name="count")
        .sort_values(["count", "rental_lead", "stage"], ascending=[False, True, True])
    )


# ── Pestaña 3 — Sección 1: Missing Key Data (Supply) ──────────────────────────

def section_supply_missing_key_data(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["stage"].isin(["Pre-settlement", "Settled", "Property leased", "Vacant"])
    if "country" in df.columns:
        mask &= df["country"] == "Spain"
    if "test_flag" in df.columns:
        mask &= df["test_flag"].isna() | (df["test_flag"] != "Test")
    if "priority" in df.columns:
        mask &= df["priority"].str.contains("High", na=False)
    base = df[mask].copy()

    base["no_suburb"]  = is_empty(base["suburb_section_name"]).astype(int)
    base["no_cluster"] = is_empty(base["area_cluster"]).astype(int)

    grouped = (
        base.groupby("supply_lead")[["no_suburb", "no_cluster"]]
        .sum()
        .rename(columns={
            "no_suburb":  "Unitsw_no_Suburb_section_name",
            "no_cluster": "Unitsw_no_area_cluster",
        })
    )
    grouped["Totals_to_be_reviewed"] = grouped.sum(axis=1)

    return (
        grouped[grouped["Totals_to_be_reviewed"] > 0]
        .sort_values(["Totals_to_be_reviewed", "supply_lead"], ascending=[False, True])
        .reset_index()
    )


# ── Pestaña 3 — Sección 2: Already Tenanted Properties ────────────────────────

def section_already_tenanted(df: pd.DataFrame) -> pd.DataFrame:
    def not_ready(series: pd.Series) -> pd.Series:
        return ~series.str.contains("✅ Ready", na=False)

    base = df[
        (df["already_tenanted"] == "Yes")
        & (pd.to_datetime(df["contract_date"], errors="coerce") > pd.Timestamp("2025-01-01"))
    ].copy()

    alert_cond = (
        not_ready(base["supply_already_tenanted_tenant"])
        | not_ready(base["supply_already_tenanted_rental"])
        | not_ready(base["supply_already_tenanted_insurance"])
    )
    base = base[alert_cond].copy()

    base["miss_tenant"]    = not_ready(base["supply_already_tenanted_tenant"]).astype(int)
    base["miss_rental"]    = not_ready(base["supply_already_tenanted_rental"]).astype(int)
    base["miss_insurance"] = not_ready(base["supply_already_tenanted_insurance"]).astype(int)

    return (
        base.groupby("supply_lead")
        .agg(
            count=("miss_tenant", "count"),
            missing_tenant=("miss_tenant", "sum"),
            missing_rental=("miss_rental", "sum"),
            missing_insurance=("miss_insurance", "sum"),
        )
        .sort_values(["count", "supply_lead"], ascending=[False, True])
        .reset_index()
    )


# ── Funciones de detalle (drill-down por fila) ─────────────────────────────────

def section_pending_offers_detail(df: pd.DataFrame, ir_name=None, priority_tier=None) -> pd.DataFrame:
    base  = add_priority_tier(base_filter_ir(df))
    alert = base[is_empty(base["subscription_plan_offer"])]
    if ir_name:
        alert = alert[alert["investor_relations_name"] == ir_name]
    if priority_tier:
        alert = alert[alert["priority_tier"] == priority_tier]
    return _pick_detail(alert)


def section_pm_plan_missing_detail(df: pd.DataFrame, ir_name=None, priority_tier=None) -> pd.DataFrame:
    stage_ok  = (
        df["stage"].str.contains("Settled|Property Leased|Vacante", na=False, case=False)
        | df["engagement_stage"].str.contains("Settled", na=False, case=False)
    )
    status_ok = df["set_up_status"].isin(POST_RENO_STATUSES + PRE_RENO_STATUSES)
    type_ok   = ~df["engagement_type"].isin(EXCLUDED_ENGAGEMENT_TYPES)
    base  = add_priority_tier(df[stage_ok & status_ok & type_ok].copy())
    alert = base[is_empty(base["pm_selected_plan"])]
    if ir_name:
        alert = alert[alert["investor_relations_name"] == ir_name]
    if priority_tier:
        alert = alert[alert["priority_tier"] == priority_tier]
    return _pick_detail(alert)


def section_home_insurance_detail(df: pd.DataFrame, ir_name=None, priority_tier=None) -> pd.DataFrame:
    base = add_priority_tier(base_filter_ir(df))
    base = base[
        base["stage"].isin(["Settled", "Vacant"])
        | base["engagement_stage"].isin(["Settled"])
    ]
    cond = (
        is_empty(base["home_insurance_offer"])
        | is_empty(base["home_insurance_choice"])
        | ((base["home_insurance_choice"] == "PropHero") & is_empty(base["home_insurance_type"]))
    )
    alert = base[cond]
    if ir_name:
        alert = alert[alert["investor_relations_name"] == ir_name]
    if priority_tier:
        alert = alert[alert["priority_tier"] == priority_tier]
    return _pick_detail(alert)


def section_missing_client_info_detail(df: pd.DataFrame, coach=None, priority_tier=None) -> pd.DataFrame:
    plan_ok   = df["pm_selected_plan"].isin(SUB_PLANS)
    stage_ok  = (
        df["stage"].isin(["Settled", "Vacant", "Property leased"])
        | df["engagement_stage"].str.contains("Settled", na=False, case=False)
    )
    status_ok = df["set_up_status"].isin(POST_RENO_STATUSES + PRE_RENO_STATUSES)
    type_ok   = ~df["engagement_type"].isin(EXCLUDED_ENGAGEMENT_TYPES)
    base = add_priority_tier(df[plan_ok & stage_ok & status_ok & type_ok].copy())
    cond = (
        is_empty(base["client_full_name"])
        | is_empty(base["client_email"])
        | is_empty(base["tech_bank_ownership_proof_urls"])
        | is_empty(base["tech_id_copy_urls"])
    )
    alert = base[cond]
    if coach:
        alert = alert[alert["coach"] == coach]
    if priority_tier:
        alert = alert[alert["priority_tier"] == priority_tier]
    return _pick_detail(alert)


def section_missing_lease_detail(df: pd.DataFrame, stage=None, rental_lead=None) -> pd.DataFrame:
    plan_ok   = ~df["pm_selected_plan"].isin(LEASE_EXCLUDED_PLANS) | is_empty(df["pm_selected_plan"])
    status_ok = df["set_up_status"] == "Tenant found (pending to formalize documentation)"
    stage_ok  = df["stage"].isin(["Settled", "Property leased", "Vacant"])
    cond_miss = (
        is_empty(df["actual_rent"])
        | is_empty(df["lease_date"])
        | is_empty(df["rent_contract_date"])
    )
    alert = df[plan_ok & status_ok & stage_ok & cond_miss].copy()
    if stage:
        alert = alert[alert["stage"] == stage]
    if rental_lead:
        alert = alert[alert["rental_lead"] == rental_lead]
    return _pick_detail(alert)


def section_subscription_formalisation_detail(df: pd.DataFrame, stage=None, rental_lead=None) -> pd.DataFrame:
    plan_ok   = df["pm_selected_plan"].isin(SUB_FORMALISATION_PLANS)
    status_ok = df["set_up_status"] == "Tenant found (pending to formalize documentation)"
    stage_ok  = df["stage"].isin(["Settled", "Property leased", "Vacant"])
    cond_miss = (
        (~df["subscription_plan_offer"].str.contains("Accepted", na=True))
        | is_empty(df["rent_insurance"])
        | is_empty(df["actual_rent"])
        | is_empty(df["rent_insurance_choice"])
    )
    alert = df[plan_ok & status_ok & stage_ok & cond_miss].copy()
    if stage:
        alert = alert[alert["stage"] == stage]
    if rental_lead:
        alert = alert[alert["rental_lead"] == rental_lead]
    return _pick_detail(alert)


def section_supply_missing_key_data_detail(df: pd.DataFrame, supply_lead=None, gap_type=None) -> pd.DataFrame:
    mask = df["stage"].isin(["Pre-settlement", "Settled", "Property leased", "Vacant"])
    if "country" in df.columns:
        mask &= df["country"] == "Spain"
    if "test_flag" in df.columns:
        mask &= df["test_flag"].isna() | (df["test_flag"] != "Test")
    if "priority" in df.columns:
        mask &= df["priority"].str.contains("High", na=False)
    base = df[mask].copy()
    if gap_type == "Sin suburb section":
        alert = base[is_empty(base["suburb_section_name"])]
    elif gap_type == "Sin area cluster":
        alert = base[is_empty(base["area_cluster"])]
    else:
        alert = base[is_empty(base["suburb_section_name"]) | is_empty(base["area_cluster"])]
    if supply_lead:
        alert = alert[alert["supply_lead"] == supply_lead]
    return _pick_detail(alert)


def section_already_tenanted_detail(df: pd.DataFrame, supply_lead=None, gap_type=None) -> pd.DataFrame:
    def not_ready(series: pd.Series) -> pd.Series:
        return ~series.str.contains("✅ Ready", na=False)

    base = df[
        (df["already_tenanted"] == "Yes")
        & (pd.to_datetime(df["contract_date"], errors="coerce") > pd.Timestamp("2025-01-01"))
    ].copy()
    if gap_type == "Missing tenant info":
        alert = base[not_ready(base["supply_already_tenanted_tenant"])]
    elif gap_type == "Missing rental docs":
        alert = base[not_ready(base["supply_already_tenanted_rental"])]
    elif gap_type == "Missing insurance":
        alert = base[not_ready(base["supply_already_tenanted_insurance"])]
    else:
        alert = base[
            not_ready(base["supply_already_tenanted_tenant"])
            | not_ready(base["supply_already_tenanted_rental"])
            | not_ready(base["supply_already_tenanted_insurance"])
        ]
    if supply_lead:
        alert = alert[alert["supply_lead"] == supply_lead]
    return _pick_detail(alert)
