# On year select, load in that year's data - must cache
import streamlit as st
from streamlit import session_state

import utils.data_loader as data_loader
import utils.scoring as scoring
import components.visualizations as viz


STAT_MAPPING = scoring.stat_mapping_nfl_py

data_loader.initialize_state()

# Display the header - contains headshot, name, and week/player selectors
header_container = st.container(border=True)
with header_container:
   viz.Header()


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


