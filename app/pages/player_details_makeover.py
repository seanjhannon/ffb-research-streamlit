# On year select, load in that year's data - must cache
import streamlit as st

import utils.scoring as scoring
import components.visualizations as viz
import utils.data_loader as data_loader
import components.selectas as selectas
import components.kpi as kpi





if "player_details" not in st.session_state:
    data_loader.init_state("player_details", default_players=[
        {"name": "Olamide Zaccheaus", "position": "WR"},
    ])

player_data = st.session_state.player_details["players"][0]["tables"]["player_data"]
team = player_data.sort_values("week", ascending=False)['recent_team'].iloc[0]

player_name = st.session_state.player_details["players"][0]["name"]
player_position = st.session_state.player_details["players"][0]["position"]
position_rank = st.session_state.player_details["players"][0]["tables"]['position_ranks_totals'].query(
                    "player_display_name == @player_name")['calc_fantasy_points'].iloc[0]

container1 = st.container(border=True)
with container1:
    container1_cols = st.columns([1,2,2])
    with container1_cols[0]:
        st.image(player_data["headshot_url"].iloc[0], use_container_width=True)
        st.subheader(f"{player_position}, {team}")
        selectas.player_selector("player_details", label_visibility='collapsed')


    with container1_cols[1]:
        viz.stat_radar_2("player_details")

    with container1_cols[2]:
        selectas.format_selector("player_details")
        selectas.year_selector("player_details")
        selectas.week_selector("player_details")

scoring_kpis_container = st.container(border=True)
with scoring_kpis_container:
    kpi.player_kpis("player_details")

viz.custom_bar("player_details")