import io
import streamlit as st
import pandas as pd
import requests

METABASE_URL = "https://metabase.prophero.com.au/public/question/e3c80ecb-a143-4fda-8f40-680d03ab4dac.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/csv,*/*",
}


@st.cache_data(ttl=300, show_spinner="Actualizando datos…")
def load_data() -> pd.DataFrame:
    response = requests.get(METABASE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text), dtype=str)
    df = df.replace({"": pd.NA, " ": pd.NA})
    return df
