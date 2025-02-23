# On year select, load in that year's data - must cache
import streamlit as st

import utils.data_loader as data_loader
import utils.scoring as scoring
import components.visualizations_new as viz


STAT_MAPPING = scoring.stat_mapping_nfl_py


if "player_details" not in st.session_state:
    data_loader.setup_state_player_details()
    data_loader.build_tables_player_details()

st.write(st.session_state.player_details)

viz.Header(st.session_state.player_details)

viz.FormatSelector(page="player_details")



