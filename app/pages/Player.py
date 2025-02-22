# On year select, load in that year's data - must cache
import streamlit as st
from streamlit import session_state

import utils.data_loader as data_loader
import utils.scoring as scoring
import components.visualizations as viz
from utils.scoring import StandardScoringFormat, PPRScoringFormat

STAT_MAPPING = scoring.stat_mapping_nfl_py


st.set_page_config(layout="wide")


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


