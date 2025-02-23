import streamlit as st
import nfl_data_py as nfl
import utils.scoring as scoring
from utils.scoring import StandardScoringFormat, PPRScoringFormat

STAT_MAPPING = scoring.stat_mapping_nfl_py


def setup_state_main():
    st.session_state.scoring_formats = [StandardScoringFormat(), PPRScoringFormat()]
    st.session_state["selected_scoring_format"] = st.session_state.scoring_formats[0]


def setup_state_player_details():
    if "player_details" not in st.session_state:
        st.session_state.player_details = {
            "page": "player_details",
            "stat_mapping": scoring.stat_mapping_nfl_py,
            "user_input": {
                "selected_scoring_format": StandardScoringFormat(),
                "selected_year": 2024,
                "selected_weeks": (0, 16),
                "selected_player": {
                    "name": "Justin Jefferson",
                    "position": "WR"
                }
            },
            "tables": {}
        }

def build_tables_player_details():
    """
    Populates the 'tables' dictionary initially. Should only be run once on page setup.
    """
    st.write("running")
    if "tables" not in st.session_state.player_details:
        # Load the full data first
        full_data = load_data(st.session_state.player_details["user_input"]["selected_year"])

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
        st.session_state.player_details["tables"] = tables
        update_all_tables_player_details()

    else:
        update_all_tables_player_details()



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


def update_state(var_name):
    if st.session_state[var_name] != st.session_state[f"{var_name}_input"]:
        st.session_state[var_name] = st.session_state[f"{var_name}_input"]
    if var_name in ["selected_year", "selected_scoring_format"]:
        update_all_tables_player_details()



def update_all_tables_player_details():
    """
    Rebuilds all tables in the 'tables' dict of the player_details state.
    Should only be run when the year or scoring format changes.
    Changes in player and week are processed as filters on the full_data table and its child tables.
    """
    state = st.session_state.player_details
    user_input = state["user_input"]

    # Load full season data and calculate fantasy points
    full_data = scoring.calculate_fantasy_points_vec(
        load_data(user_input["selected_year"]),
        user_input["selected_scoring_format"],
        state["stat_mapping"]
    )
    state["tables"]["full_data"] = full_data

    build_player_data_from_full(state, full_data)
    build_positional_tables_from_full(state, full_data)

    # st.session_state.player_details["tables"] = state["tables"]

def refresh_child_tables_player_details():
    """
    Refreshes just the player-specific tables, preventing a call to API.
    Should be run when selected player and weeks change.
    """
    st.write('running refresh')
    state = st.session_state.player_details
    full_data = state["tables"]["full_data"]

    build_player_data_from_full(state, full_data)
    build_positional_tables_from_full(state, full_data)

    # st.session_state.player_details["tables"] = state["tables"]
    st.write('running refresh')

def build_positional_tables_from_full(state, full_data):

    player_position = state["user_input"]["selected_player"]['position']
    week_range = range(state["user_input"]['selected_weeks'][0], state["user_input"]['selected_weeks'][1] + 1)
    positional_data = full_data.query(
        "position == @player_position and week in @week_range")
    if positional_data.empty:
        st.warning(f"No positional data found for position: {player_position}")
        return

    # Update positional tables
    state["tables"].update({
        "positional_data": positional_data,
        "position_ranks_totals": scoring.make_position_ranks(scoring.calculate_total_stats(positional_data)),
        "position_ranks_averages": scoring.make_position_ranks(scoring.calculate_avg_stats(positional_data))
    })




def build_player_data_from_full(state, full_data):
    player_data = full_data.query("player_display_name == @state['user_input']['selected_player']['name']")
    if player_data.empty:
        st.warning(f"No data found for player: {state['user_input']['selected_player']['name']}")
        return


    state["tables"].update({
        "player_data": player_data,
        "player_stat_totals": player_data.sum(),
        "player_stat_averages": player_data.mean(numeric_only=True),
        "player_points_by_stat": scoring.calculate_fantasy_points_by_category(
            player_data, scoring_format=st.session_state.selected_scoring_format, stat_mapping=state["stat_mapping"]
        )
    })


def update_nested_state(nested_keys, new_value):
    """
    Given a list of nested keys (e.g. ["user_input", "selected_player", "name"]),
    updates st.session_state["player_details"] at that nested location with new_value.
    """
    d = st.session_state["player_details"]
    for key in nested_keys[:-1]:
        d = d[key]
    d[nested_keys[-1]] = new_value


def generic_on_change(flat_key, nested_keys, update_funcs=None):
    """
    A generic on_change callback that:
      1. Reads the new value from st.session_state[flat_key]
      2. Updates st.session_state["player_details"] at the location specified by nested_keys
      3. Calls any extra update functions.

    Args:
      flat_key (str): The key used by the widget (a flat key).
      nested_keys (list): The path to the value in the nested state structure.
      update_funcs (list): Optional list of functions to run after updating state.
    """
    new_value = st.session_state.get(flat_key)
    update_nested_state(nested_keys, new_value)
    # Optionally, run additional update functions
    if update_funcs:
        for func in update_funcs:
            func()





