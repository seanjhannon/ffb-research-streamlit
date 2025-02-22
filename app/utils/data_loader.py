import streamlit as st
import nfl_data_py as nfl
import utils.scoring as scoring

STAT_MAPPING = scoring.stat_mapping_nfl_py



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



