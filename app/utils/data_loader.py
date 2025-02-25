import pandas as pd
import streamlit as st
import nfl_data_py as nfl
import utils.scoring as scoring
from utils.scoring import StandardScoringFormat, PPRScoringFormat
import copy


@st.cache_data(show_spinner="Loading data ...")
def load_data(years):
    if years is None:
        print('No year(s) selected!?')
        return
    elif isinstance(years, list):
        year_range = years
    else:
        year_range = [years]

    return nfl.import_weekly_data(year_range, downcast=True)

def setup_state_main():
    """
    Sets up global state by populating the default list of scoring formats.
    Adding of new scoring formats is handled within custom_scoring.py
    :return:
    """
    if "scoring_formats" not in st.session_state:
        st.session_state.scoring_formats = [StandardScoringFormat(), PPRScoringFormat()]
    if "selected_scoring_format" not in st.session_state:
        st.session_state["selected_scoring_format"] = st.session_state.scoring_formats[0]

# Templates for a consistent state shape.
COMMON_STATE_TEMPLATE = {
    "selected_year": 2024,
    "selected_weeks": (0, 16),
    "selected_scoring_format": None,
    "stat_mapping": scoring.stat_mapping_nfl_py,
    "players": [],
    "full_data": None,  # Updated separately.
}

PLAYER_STATE_TEMPLATE = {
    "name": "",
    "position": "",
    "tables": {},  # Holds derived tables.
}


def init_state(page_key: str, default_players: list = None):
    """
    Initialize the page's state as a top-level attribute in st.session_state.
    Only runs once per page_key, preserving existing user selections.

    Args:
        page_key (str): e.g. "player_details" or "player_comparison"
        default_players (list): A list of dicts with default player info.
    """
    if not hasattr(st.session_state, page_key):
        state = copy.deepcopy(COMMON_STATE_TEMPLATE)
        if default_players:
            for player_info in default_players:
                player = copy.deepcopy(PLAYER_STATE_TEMPLATE)
                player.update(player_info)
                state["players"].append(player)
        # set scoring format to the global value
        state.update({"selected_scoring_format":st.session_state["selected_scoring_format"]})
        setattr(st.session_state, page_key, state)



    update_full_data(page_key)


def update_full_data(page_key: str):
    """
    Update the 'full_data' for a given page. This operation can be triggered
    multiple times after initialization (e.g., after a year or scoring_format change).

    Args:
        page_key (str): The key to identify the page's state.
    """
    st.write("updating full_data")
    state = getattr(st.session_state, page_key)

    st.write(state["selected_scoring_format"])

    state["full_data"] = scoring.calculate_fantasy_points_vec(
        load_data(state["selected_year"]),
        state["selected_scoring_format"],
        state["stat_mapping"]
    )
    # Optional: reassign the updated state back to session_state for clarity.
    setattr(st.session_state, page_key, state)
    update_player_tables(page_key)


def update_player_tables(page_key:str):
    """
    Function to be run any time the tables relative to a specific player need to be initialized or overwritten.
    These tables include 'player' and 'positional' tables

    :param page_key:
    :return:
    """
    st.write("updating player tables")
    state = getattr(st.session_state, page_key)
    week_range = range(state["selected_weeks"][0], state["selected_weeks"][1] + 1)
    full_data = state["full_data"].loc[state["full_data"]["week"].isin(week_range)]
    for player in state["players"]:

        player_data = full_data.query(
            "player_display_name == @player['name']"
        )
        if player_data.empty:
            st.warning(f"No data found for player: {player['name']}")
            return

        positional_data = full_data.query(
            "position == @player['position']"
        )
        if positional_data.empty:
            st.warning(f"No positional data found for position: {player['position']}")
            return

        player["tables"].update({
            "player_data": player_data,
            "player_stat_totals": player_data.sum(numeric_only=True),
            "player_stat_averages": player_data.mean(numeric_only=True),
            "player_points_by_stat": scoring.calculate_fantasy_points_by_category(
                player_data, scoring_format=state["selected_scoring_format"], stat_mapping=state["stat_mapping"]
            ),
            "positional_data": positional_data,
            "position_ranks_totals": scoring.make_position_ranks(scoring.calculate_total_stats(positional_data)),
            "position_ranks_averages": scoring.make_position_ranks(scoring.calculate_avg_stats(positional_data))
        })


# CALLBACKS

def handle_change(page_key: str,
                  attr_name:str,
                  func=None):
    """
    Generic function for handling the updating of an attribute in state
    :param page_key: top-level attribute for the page of the change
    :param attr_name: the attribute to be changed
    :param func: the table updating function to be called after the update is made
    :return: None
    """
    state = getattr(st.session_state, page_key)
    new_val = st.session_state[attr_name] #stash new value one level up as tmp
    if new_val != state[attr_name]:
        state["selected_scoring_format"] = new_val
        setattr(st.session_state, page_key, state)
        func(page_key)


def handle_year_change(page_key: str):
    """
    Callback function for when the user selects a new year.
    Updates the selected year in session state and refreshes the data.
    """
    state = getattr(st.session_state, page_key)
    new_year = st.session_state["selected_year"]

    if new_year != state["selected_year"]:  # Only update if the year actually changes
        state["selected_year"] = new_year
        update_full_data(page_key)  # Reload data and update tables

def handle_format_change(page_key: str):
    """
    Callback function for when the user selects a new format.
    Updates the selected scoring format in session state and refreshes the data.
    """
    handle_change(page_key, "selected_scoring_format", update_full_data)
    # update_full_data(page_key)  # Reload data and update tables


def handle_week_change(page_key: str):
    """
    Callback function for when the user selects a new format.
    Updates the selected scoring format in session state and refreshes the data.
    """
    state = getattr(st.session_state, page_key)
    new_weeks = st.session_state["selected_weeks"]

    if new_weeks != state["selected_weeks"]:  # Only update if the year actually changes
        state["selected_weeks"] = new_weeks
        update_player_tables(page_key)  # Reload data and update tables

def handle_player_change(page_key: str,
                         player_index:int=0):
    """
    Callback function for when the user selects a new format.
    Updates the selected scoring format in session state and refreshes the data.
    """
    state = getattr(st.session_state, page_key)
    new_player = st.session_state[f"selected_player_{player_index}"]

    if new_player != state["players"][player_index]['name']:  # Only update if the year actually changes
        state["players"][player_index]['name'] = new_player
        state["players"][player_index]['position'] = state["full_data"].query(
            "player_display_name == @new_player"
        )["position"].iloc[0]
        update_player_tables(page_key)  # Reload data and update tables

