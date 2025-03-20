import streamlit as st
from pandas.core.ops import comparison_op

import components.visualizations as viz
import utils.data_loader as data_loader_experimental
import components.selectas as selectas

if "player_comparison" not in st.session_state:
    data_loader_experimental.init_state("player_comparison", default_players=[
    {"name": "Aaron Rodgers", "position": "QB"},
    {"name": "Sam Darnold", "position": "QB"}
])

selector_container = st.container()
with selector_container:
    selector_cols = st.columns(3)
    with selector_cols[0]:
        selectas.format_selector("player_comparison")

    with selector_cols[1]:
        selectas.week_selector("player_comparison")

    with selector_cols[2]:
        selectas.year_selector("player_comparison")

comparison_columns = st.columns([1,2,1])


def make_player_comp_header(player_index):
    player_data = st.session_state.player_comparison["players"][player_index]["tables"]["player_data"]
    player_comp_header = st.container(border=True)
    with player_comp_header:

        st.image(player_data["headshot_url"].iloc[0], use_container_width=True)
        player_position = st.session_state.player_comparison["players"][player_index]["position"]
        team = player_data.sort_values("week", ascending=False)['recent_team'].iloc[0]

        selectas.player_selector("player_comparison", player_index, label_visibility='collapsed')
        st.subheader(f"{player_position}, {team}")


with comparison_columns[0]:
    make_player_comp_header(0)


with comparison_columns[2]:
    make_player_comp_header(1)




with comparison_columns[1]:
    viz.stat_radar_comparison("player_comparison")

kpi_comparison_columns = st.columns([3,1,3])
with kpi_comparison_columns[0]:
    st.container(border=True)

with kpi_comparison_columns[1]:
    st.container(border=True)

with kpi_comparison_columns[2]:
    st.container(border=True)