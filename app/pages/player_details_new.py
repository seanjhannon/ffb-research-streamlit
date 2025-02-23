# On year select, load in that year's data - must cache
import streamlit as st

import utils.data_loader as data_loader
import utils.scoring as scoring
import components.visualizations_new as viz


STAT_MAPPING = scoring.stat_mapping_nfl_py


if "player_details" not in st.session_state:
    data_loader.setup_state_player_details()
    data_loader.build_tables_player_details()

# st.write(st.session_state.player_details)
header_container = st.container(border=True)
with header_container:
    viz.Header(st.session_state.player_details)

scoring_kpis_container = st.container(border=True)
with scoring_kpis_container:
    viz.ScoringKPIs(st.session_state.player_details)

charts_container = st.container()
with charts_container:
    col1, col2 = st.columns(2)

    with col1:
        radar_container = st.container()
        with radar_container:
            viz.Radar(st.session_state.player_details)
            # st.markdown("""
            #     <style>
            #         [data-testid="column"]:nth-child(2){
            #             background-color: lightgrey;
            #         }
            #     </style>
            #     """, unsafe_allow_html=True
            #             )

    with col2:
        viz.CustomBar(st.session_state.player_details)



