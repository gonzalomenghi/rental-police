"""
Weekly KPI snapshot storage for Week-over-Week (WoW) evolution tracking.

Snapshots are saved to data/snapshots.json relative to the project root.
On Streamlit Community Cloud the file persists within a deployment session
but resets when the app redeploys from git. For long-term persistence, commit
the file to the repository or migrate to a cloud store (GCS, S3, etc.).
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

_DATA_DIR      = Path(__file__).parent.parent / "data"
_SNAPSHOT_FILE = _DATA_DIR / "snapshots.json"


def week_key() -> str:
    """Return current ISO week as 'YYYY-Www' string (e.g. '2026-W23')."""
    iso = datetime.now().isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def load_snapshots() -> dict:
    """Load all saved weekly snapshots from disk. Returns {} on any error."""
    if not _SNAPSHOT_FILE.exists():
        return {}
    try:
        return json.loads(_SNAPSHOT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def build_kpis(df: pd.DataFrame) -> dict:
    """
    Calculate all KPI totals from the full (unfiltered) dataset.
    Returns a flat dict of {kpi_key: int}.
    """
    from utils.filters import (
        section_pending_offers, section_pm_plan_missing,
        section_home_insurance, section_missing_client_info,
        section_unassigned_pm, section_ready_to_rent_gaps,
        section_missing_lease, section_subscription_formalisation,
        section_supply_missing_key_data, section_already_tenanted,
    )

    def _s(fn, col):
        try:
            r = fn(df)
            return int(r[col].sum()) if not r.empty else 0
        except Exception:
            return 0

    def _n(fn):
        try:
            return int(len(fn(df)))
        except Exception:
            return 0

    return {
        "ir_pending_offers":    _s(section_pending_offers,              "alertas"),
        "ir_pm_plan_missing":   _s(section_pm_plan_missing,             "alertas"),
        "ir_home_insurance":    _s(section_home_insurance,              "alertas"),
        "ir_missing_client":    _s(section_missing_client_info,         "alertas"),
        "rental_unassigned_pm": _n(section_unassigned_pm),
        "rental_ready_to_rent": _s(section_ready_to_rent_gaps,          "Total"),
        "rental_missing_lease": _s(section_missing_lease,               "count"),
        "rental_sub_formal":    _s(section_subscription_formalisation,  "count"),
        "supply_missing_kd":    _s(section_supply_missing_key_data,     "Totals_to_be_reviewed"),
        "supply_tenanted":      _s(section_already_tenanted,            "count"),
    }


def ensure_weekly_snapshot(df: pd.DataFrame) -> None:
    """Save this week's KPIs if no entry exists yet for the current week."""
    key       = week_key()
    snapshots = load_snapshots()
    if key in snapshots:
        return
    kpis = build_kpis(df)
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    snapshots[key] = kpis
    try:
        _SNAPSHOT_FILE.write_text(json.dumps(snapshots, indent=2), encoding="utf-8")
    except OSError:
        pass  # gracefully skip on read-only filesystems


def get_wow_deltas(current_kpis: dict) -> dict:
    """
    Return {kpi_key: delta} comparing current KPIs to the previous week's snapshot.
    Returns an empty dict when no prior snapshot exists.
    """
    snapshots   = load_snapshots()
    current_wk  = week_key()
    prev_keys   = sorted(k for k in snapshots if k < current_wk)
    if not prev_keys:
        return {}
    prev = snapshots[prev_keys[-1]]
    return {k: current_kpis.get(k, 0) - prev.get(k, 0) for k in current_kpis}


def get_trend_data() -> pd.DataFrame:
    """
    Return a DataFrame with one row per saved week and one column per KPI key.
    Columns: 'week', plus one column per KPI.
    Returns an empty DataFrame when no snapshots exist.
    """
    snapshots = load_snapshots()
    if not snapshots:
        return pd.DataFrame()
    rows = [{"week": wk, **kpis} for wk, kpis in sorted(snapshots.items())]
    return pd.DataFrame(rows)
