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
                "selected_player": "Justin Jefferson",
                "selected_player_position": "WR",
                "selected_weeks": (0, 16)
            },
            "tables": {}
        }

def build_tables_player_details():
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
        update_tables_player_details()

    else:
        update_tables_player_details()



def initialize_state():
    if "scoring_formats" not in st.session_state:
        st.session_state.scoring_formats = [StandardScoringFormat(), PPRScoringFormat()]

    if "selected_scoring_format" not in st.session_state:
        st.session_state.selected_scoring_format = st.session_state.scoring_formats[0]  # Default to Standard

    if "selected_year" not in st.session_state:
        st.session_state.selected_year = 2024

    if "selected_player" not in st.session_state:
        st.session_state.selected_player = "Aaron Rodgers"

    if "selected_weeks" not in st.session_state:
        st.session_state.selected_weeks = (0, 16)

    if "tables" not in st.session_state:
        # Load the full data first
        full_data = load_data(st.session_state.selected_year)

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
        st.session_state["tables"] = tables
        update_tables()

    else:
        update_tables()



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
        update_tables()



def update_tables():
    tables = st.session_state["tables"]  # Retrieve existing tables

    selected_weeks = st.session_state.selected_weeks
    selected_weeks_range = range(selected_weeks[0], selected_weeks[1]+1)

    # Calculate Fantasy Points
    full_data = load_data(st.session_state.selected_year)
    full_data["calc_fantasy_points"] = full_data.apply(
        lambda row: scoring.calculate_fantasy_points(row, st.session_state.selected_scoring_format, STAT_MAPPING),
        axis=1
    )
    tables['full_data'] = full_data

    # Ensure player data is found before extracting the position
    player_data = full_data.query("player_display_name == @st.session_state.selected_player")
    if player_data.empty:
        st.warning(f"No data found for player: {st.session_state.selected_player}")
        return

    player_data = player_data.query("week in @selected_weeks_range")
    # Update player-related tables
    tables["player_data"] = player_data

    tables["player_stat_totals"] = player_data.sum()
    tables["player_stat_averages"] = player_data.mean(numeric_only=True)
    tables["player_points_by_stat"] = scoring.calculate_fantasy_points_by_category(
        player_data, scoring_format=st.session_state.selected_scoring_format, stat_mapping=STAT_MAPPING
    )

    st.session_state.selected_player_position = tables["player_data"]["position"].iloc[0]


    # Ensure positional data is found before updating tables
    positional_data = full_data.query("position == @st.session_state.selected_player_position")
    if positional_data.empty:
        st.warning(f"No positional data found for position: {st.session_state.selected_player_position}")
        return

    positional_data = positional_data.query("week in @selected_weeks_range")
    # Update positional-related tables
    tables["positional_data"] = positional_data

    positional_totals = scoring.calculate_total_stats(positional_data)
    tables["position_ranks_totals"] = scoring.make_position_ranks(positional_totals)

    positional_averages = scoring.calculate_avg_stats(positional_data)
    tables["position_ranks_averages"] = scoring.make_position_ranks(positional_averages)

    # Store back to session state
    st.session_state["tables"] = tables

def update_tables_player_details():
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

    # Filter for the selected player
    player_data = full_data.query("player_display_name == @user_input['selected_player']")
    if player_data.empty:
        st.warning(f"No data found for player: {user_input['selected_player']}")
        return

    tables = state["tables"]
    tables.update({
        "player_data": player_data,
        "player_stat_totals": player_data.sum(),
        "player_stat_averages": player_data.mean(numeric_only=True),
        "player_points_by_stat": scoring.calculate_fantasy_points_by_category(
            player_data, scoring_format=st.session_state.selected_scoring_format, stat_mapping=state["stat_mapping"]
        )
    })

    # Filter for positional data
    player_position = tables["player_data"]["position"].iloc[0]

    week_range = range(user_input['selected_weeks'][0], user_input['selected_weeks'][1] + 1)
    positional_data = full_data.query(
        "position == @player_position and week in @week_range")
    if positional_data.empty:
        st.warning(f"No positional data found for position: {player_position}")
        return

    # Update positional tables
    tables.update({
        "positional_data": positional_data,
        "position_ranks_totals": scoring.make_position_ranks(scoring.calculate_total_stats(positional_data)),
        "position_ranks_averages": scoring.make_position_ranks(scoring.calculate_avg_stats(positional_data))
    })

    state["tables"] = tables




