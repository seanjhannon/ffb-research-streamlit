import streamlit as st
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

comparison_columns = st.columns(2)

with comparison_columns[0]:

    selectas.player_selector("player_comparison", 0)

    player_data = st.session_state.player_comparison["players"][0]["tables"]["player_data"]
    player_comp_header = st.container(border=True)
    with player_comp_header:
        player_comp_header_cols = st.columns([1,3])
        with player_comp_header_cols[0]:
            st.image(player_data["headshot_url"].iloc[0])
        with player_comp_header_cols[1]:
            with st.container():
                st.write(player_data["position"].iloc[0])
            with st.container():
                st.write(player_data["player_display_name"].iloc[0])


with comparison_columns[1]:
    selectas.player_selector("player_comparison", 1)

    st.write(st.session_state.player_comparison["players"][1]["tables"]["player_data"])
