# On year select, load in that year's data - must cache
import streamlit as st
from streamlit import session_state

import data_loader
import visualizations as viz
import scoring
from scoring import StandardScoringFormat, PPRScoringFormat

STAT_MAPPING = scoring.stat_mapping_nfl_py


st.set_page_config(layout="wide")


if "scoring_formats" not in session_state:
    st.session_state.scoring_formats = [StandardScoringFormat(), PPRScoringFormat()]

if "selected_scoring_format" not in session_state:
    st.session_state.selected_scoring_format = st.session_state.scoring_formats[0] #Default to Standard

if "selected_year" not in session_state:
    st.session_state.selected_year = 2024

if "selected_player" not in session_state:
    st.session_state.selected_player = "Aaron Rodgers"

if "selected_weeks" not in session_state:
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

scoring_format_container = st.container(border=True)
with scoring_format_container:

    st.selectbox('Select scoring format',
                 options=st.session_state.scoring_formats,

                 format_func=lambda x:x.name,
                 key="selected_scoring_format_input",
                 on_change=data_loader.update_state,
                 args=("selected_scoring_format",)
                 )


# Display the header - contains headshot, name, and week/player selectors
header_container = st.container(border=True)
with header_container:
   viz.Header()


# Display the week selector
week_selector_container = st.container(border=True)
with week_selector_container:
    viz.WeekSelector()


scoring_kpis_container = st.container()
with scoring_kpis_container:
    viz.ScoringKPIs()

charts_container = st.container()
with charts_container:
    col1, col2 = st.columns(2)

    with col1:
        radar_container = st.container()
        with radar_container:
            viz.Radar(st.session_state["tables"]["player_points_by_stat"])
            st.markdown("""
                <style>
                    [data-testid="column"]:nth-child(2){
                        background-color: lightgrey;
                    }
                </style>
                """, unsafe_allow_html=True
                        )

    with col2:
        viz.CustomBar(st.session_state["tables"]["player_data"])


