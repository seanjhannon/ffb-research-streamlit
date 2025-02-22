import streamlit as st

import utils.data_loader as data_loader
from utils.scoring import StandardScoringFormat, PPRScoringFormat

# Set Streamlit page configuration (optional)
st.set_page_config(page_title="FFB Research", page_icon="📊", layout="wide")

# App Title
st.title("Welcome to FFB Research Streamlit App")

st.write("Use the sidebar to navigate between pages.")



if "scoring_formats" not in st.session_state:
    st.session_state.scoring_formats = [StandardScoringFormat(), PPRScoringFormat()]

if "selected_scoring_format" not in st.session_state:
    st.session_state.selected_scoring_format = st.session_state.scoring_formats[0] #Default to Standard

if "selected_year" not in st.session_state:
    st.session_state.selected_year = 2024

if "selected_player" not in st.session_state:
    st.session_state.selected_player = "Aaron Rodgers"

if "selected_weeks" not in st.session_state:
    st.session_state.selected_weeks = (0, 16)

if "tables" not in st.session_state:
    # Load the full data first
    full_data = data_loader.load_data(st.session_state.selected_year)

    # Create the dictionary without self-referencing st.session_state["tables"]
    tables = {
        "full_data": full_data,
        "positional_data": None,
        "position_ranks_totals": None,
        "position_ranks_averages": None,
        "player_data": None,
        "player_stat_totals": None,
        "player_stat_averages": None,
        "player_points_by_stat": None
    }
    st.session_state["tables"] = tables
    data_loader.update_tables()

else:
    data_loader.update_tables()