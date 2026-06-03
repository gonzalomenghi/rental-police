import streamlit as st
import pandas as pd

METABASE_URL = "https://metabase.prophero.com.au/public/question/e3c80ecb-a143-4fda-8f40-680d03ab4dac.csv"


@st.cache_data(ttl=300, show_spinner="Actualizando datos…")
def load_data() -> pd.DataFrame:
    df = pd.read_csv(METABASE_URL, dtype=str)
    df = df.replace({"": pd.NA, " ": pd.NA})
    return df
