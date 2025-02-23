import streamlit as st
import nfl_data_py as nfl
import utils.scoring as scoring
from utils.scoring import StandardScoringFormat, PPRScoringFormat

STAT_MAPPING = scoring.stat_mapping_nfl_py


def setup_state_main():
    if "scoring_formats" not in st.session_state:
        st.session_state.scoring_formats = [StandardScoringFormat(), PPRScoringFormat()]
    if "selected_scoring_format" not in st.session_state:
        st.session_state["selected_scoring_format"] = st.session_state.scoring_formats[0]


def setup_state_player_details():
    if "player_details" not in st.session_state:
        st.session_state.player_details = {
            "page": "player_details",
            "stat_mapping": scoring.stat_mapping_nfl_py,
            "user_input": {
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
        st.session_state["selected_scoring_format"],
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
    # Do this here because I can't think of a better solution lol
    state["user_input"]["selected_player"]["position"] =  player_data['position'].iloc[0]


def update_nested_state(nested_dict, key_path, new_value):
    """
    Recursively updates a nested dictionary given a key path.

    Args:
      nested_dict (dict): The dictionary to update (e.g. st.session_state["player_details"]).
      key_path (list): A list of keys representing the nested path.
      new_value: The new value to set.
    """
    d = nested_dict
    for key in key_path[:-1]:
        if key not in d or not isinstance(d[key], dict):
            d[key] = {}
        d = d[key]
    d[key_path[-1]] = new_value


def generic_on_change(flat_key, nested_keys=None, update_funcs=None):
    """
    Generic on_change callback that updates either a top-level key or a nested key
    in st.session_state and then runs additional functions.

    Args:
      flat_key (str): The key in st.session_state where the widget writes its value.
      nested_keys (list or None): If provided, the nested path inside st.session_state["player_details"] to update.
                                   If None, the value remains at the top level.
      update_funcs (list): Optional list of functions to call after updating.
    """
    new_value = st.session_state.get(flat_key)

    if nested_keys is not None:
        update_nested_state(st.session_state["player_details"], nested_keys, new_value)
        print(f"Updated nested key {' -> '.join(nested_keys)} to {new_value}")
    else:
        print(f"Updated top-level key {flat_key} to {new_value}")

    if update_funcs:
        for func in update_funcs:
            func()