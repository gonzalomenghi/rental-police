#!/usr/bin/env python3
"""
Weekly export of Rental Police KPIs to Google Sheets.
Runs standalone (no Streamlit dependency) via GitHub Actions every Friday.

Required env var:
  GOOGLE_SHEETS_CREDENTIALS  — Google Service Account JSON key (full contents)
"""

import io
import json
import os
import sys
from datetime import datetime, date
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials

# ── Configuration ──────────────────────────────────────────────────────────────

METABASE_URL = (
    "https://metabase.prophero.app/public/question/"
    "e3c80ecb-a143-4fda-8f40-680d03ab4dac.csv"
)
SPREADSHEET_ID = "1et1Tog8Io65JTc_t-fKKo73Bm2CnduyCtLGwcZjc6Yg"
SHEET_NAME = "KPI Semanal"
MADRID_TZ = ZoneInfo("Europe/Madrid")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = [
    "Semana",
    "Fecha (viernes)",
    "Timestamp (Madrid)",
    "IR - Pending Offers",
    "IR - PM Plan Missing",
    "IR - Home Insurance",
    "IR - Missing Client Info",
    "Total IR",
    "Rental - PM sin asignar",
    "Rental - Ready to Rent",
    "Rental - Missing Lease",
    "Rental - Sub. Formalización",
    "Total Rental",
    "Supply - Missing Key Data",
    "Supply - Already Tenanted",
    "Total Supply",
    "Total General",
]


# ── Data loading (no Streamlit) ────────────────────────────────────────────────

def load_data() -> pd.DataFrame:
    resp = requests.get(
        METABASE_URL,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "text/csv,*/*"},
        timeout=30,
    )
    resp.raise_for_status()
    df = pd.read_csv(io.BytesIO(resp.content), dtype=str, encoding="utf-8")
    return df.replace({"": pd.NA, " ": pd.NA})


# ── Google Sheets helpers ──────────────────────────────────────────────────────

def get_sheets_client() -> gspread.Client:
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json:
        raise EnvironmentError("Missing GOOGLE_SHEETS_CREDENTIALS environment variable")
    creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
    return gspread.authorize(creds)


def get_or_create_sheet(client: gspread.Client) -> gspread.Worksheet:
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        return spreadsheet.worksheet(SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=SHEET_NAME, rows=500, cols=len(HEADERS))
        ws.append_row(HEADERS, value_input_option="USER_ENTERED")
        return ws


def week_key(now: datetime) -> str:
    iso = now.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Fetching data from Metabase...")
    df = load_data()
    print(f"  {len(df)} rows loaded.")

    # build_kpis reuses all business logic from utils/filters.py
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.snapshot import build_kpis

    print("Calculating KPIs...")
    kpis = build_kpis(df)

    ir_total     = sum(kpis[k] for k in ["ir_pending_offers", "ir_pm_plan_missing",
                                          "ir_home_insurance", "ir_missing_client"])
    rental_total = sum(kpis[k] for k in ["rental_unassigned_pm", "rental_ready_to_rent",
                                          "rental_missing_lease", "rental_sub_formal"])
    supply_total = kpis["supply_missing_kd"] + kpis["supply_tenanted"]
    grand_total  = ir_total + rental_total + supply_total

    now = datetime.now(MADRID_TZ)
    wk  = week_key(now)

    row = [
        wk,
        now.strftime("%Y-%m-%d"),
        now.strftime("%Y-%m-%d %H:%M"),
        kpis["ir_pending_offers"],
        kpis["ir_pm_plan_missing"],
        kpis["ir_home_insurance"],
        kpis["ir_missing_client"],
        ir_total,
        kpis["rental_unassigned_pm"],
        kpis["rental_ready_to_rent"],
        kpis["rental_missing_lease"],
        kpis["rental_sub_formal"],
        rental_total,
        kpis["supply_missing_kd"],
        kpis["supply_tenanted"],
        supply_total,
        grand_total,
    ]

    print(f"Connecting to Google Sheets...")
    client = get_sheets_client()
    sheet  = get_or_create_sheet(client)

    # Avoid duplicating the same week if the job runs twice
    existing_weeks = [r[0] for r in sheet.get_all_values()[1:] if r]
    if wk in existing_weeks:
        print(f"  Week {wk} already exported — skipping.")
        return

    sheet.append_row(row, value_input_option="USER_ENTERED")
    print(f"  Row appended: {dict(zip(HEADERS, row))}")
    print(f"Grand total alerts this week: {grand_total}")
    print("Done.")


if __name__ == "__main__":
    main()