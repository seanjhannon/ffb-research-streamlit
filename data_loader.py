import streamlit as st
import nfl_data_py as nfl

@st.cache_data(show_spinner="Loading data ...")
def load_data_one_year(year):
    """Loads a single year of data in a cached manner"""
    return nfl.import_weekly_data([year])