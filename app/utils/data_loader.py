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
    st.session_state.player_details = {
        "page": "player_details",
        "stat_mapping": scoring.stat_mapping_nfl_py,
        "user_input": {
            "selected_year": 2024,
            "selected_weeks": (0, 16),
            "selected_player": {
                "name": "Aaron Rodgers",
                "position": "QB"
            }
        },
        "tables": {}
    }

def setup_state_player_comparison():
    if "player_comparison" not in st.session_state:
        st.session_state.player_comparison = {
            "user_input": {
                "page": "player_comparison",
                "selected_year": 2024,
                "selected_weeks": (0, 16),
                "stat_mapping": scoring.stat_mapping_nfl_py,
            },
            "tables": {},
            "player_a": {
                "user_input": {
                    "selected_player": {
                        "name": "Aaron Rodgers",
                        "position": "QB"
                    }
                },
                "tables": {}
        },
            "player_b": {
                "user_input": {
                    "selected_player": {
                        "name": "Sam Darnold",
                        "position": "QB"
                    }
                },
                "tables": {}
            },
        }



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


def update_all_tables_player_comparison(state):
    """
    Puts full_data in the top level of the page state then triggers all child tables to be built for comparison.
    Should run when initializing the page and whenever user changes scoring format or year.
    """
    user_input = state["user_input"]
    full_data = scoring.calculate_fantasy_points_vec(
        load_data(user_input["selected_year"]),
        st.session_state["selected_scoring_format"],
        state["stat_mapping"]
    )
    state["tables"].update({"full_data": full_data})
    # Call helpers to rebuild tables for player a and b

def update_player_tables_comparison():
    """
    Creates the following tables for a given player in the comparison based off of the values in state:
        - player_data
        - player_stat_totals
        - player_stat_averages
        - player_points_by_stat

    """
    # Get full data


def update_all_tables_player_details(state):
    """
    Rebuilds all tables in the 'tables' dict of the player_details state.
    Should only be run when the year or scoring format changes.
    Changes in player and week are processed as filters on the full_data table and its child tables.
    """
    if "user_input" in state:
        user_input = state["user_input"]
        # Load full season data and calculate fantasy points
        full_data = scoring.calculate_fantasy_points_vec(
            load_data(user_input["selected_year"]),
            st.session_state["selected_scoring_format"],
            state["stat_mapping"]
        )
        state["tables"].update({"full_data": full_data})
        build_player_data_from_full(state, full_data)
        build_positional_tables_from_full(state, full_data)


def refresh_child_tables_player_details():
    """
    Refreshes just the player-specific tables, preventing a call to API.
    Should be run when selected player and weeks change.
    """
    state = st.session_state.player_details
    full_data = state["tables"]["full_data"]

    build_player_data_from_full(state, full_data)
    build_positional_tables_from_full(state, full_data)


def build_positional_tables_from_full(state, full_data):
    """
    Refreshes the positional_data table to use the latest full_data and range of weeks.
    """

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
    """
    Refreshes the player_data table to use the latest full_data and range of weeks.
    """
    week_range = range(state["user_input"]['selected_weeks'][0], state["user_input"]['selected_weeks'][1] + 1)
    player_data = full_data.query("player_display_name == @state['user_input']['selected_player']['name']")
    player_data = player_data.query("week in @week_range")
    if player_data.empty:
        st.warning(f"No data found for player: {state['user_input']['selected_player']['name']}")
        return

    state["tables"].update({
        "player_data": player_data,
        "player_stat_totals": player_data.sum(numeric_only=True),
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
        for func_item in update_funcs:
            if isinstance(func_item, tuple):  # Handle functions with arguments
                func, *args = func_item
                func(*args)
            else:
                func_item()  # Call function normally if no arguments are provided