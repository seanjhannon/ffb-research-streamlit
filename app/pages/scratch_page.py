import streamlit as st


page = "tables"
st.write(st.session_state[f"{page}"])

# st.session_state.player_details = {
#     user_input: {
#         selected_scoring_format
#         selected_year
#         selected_player
#         selected_weeks
#     },
#     tables: {
#     player: {
#         player_data
#         player_stat_totals
#     player_stat_averages
#     }
#
# }
#
#
# }




def update_tables_player_details():
    """
    Rebuilds all tables in the 'tables' dict of the player_details state.
    Should only be run when the year or scoring format changes.
    Changes in player and week are processed as filters on the full_data table and its child tables.
    """
    # define useful variables in a smaller namespace
    state = st.session_state.player_details
    tables = state["tables"]
    stat_mapping = state["stat_mapping"]
    selected_weeks = state["user_input"]["selected_weeks"]
    selected_weeks_range = range(selected_weeks[0], selected_weeks[1] + 1)
    selected_year = state["user_input"]["selected_year"]
    scoring_format = state["user_input"]["selected_scoring_format"]
    selected_player = state["user_input"]["selected_player"]

    # Pull in full years' data, calculate Fantasy Points, and save it in state
    full_data = load_data(selected_year)
    full_data = scoring.calculate_fantasy_points_vec(full_data,
                                                     scoring_format,
                                                     stat_mapping
                                                     )
    tables["full_data"] = full_data

    # Update player-related tables
    player_data = full_data.query("player_display_name == @selected_player")
    if player_data.empty:
        st.warning(f"No data found for player: {selected_player}")
        return
    tables["player_stat_totals"] = player_data.sum()
    tables["player_stat_averages"] = player_data.mean(numeric_only=True)
    tables["player_points_by_stat"] = scoring.calculate_fantasy_points_by_category(
        player_data, scoring_format=st.session_state.selected_scoring_format, stat_mapping=stat_mapping
    )
    player_position = tables["player_data"]["position"].iloc[0]

    # Ensure positional data is found before updating tables
    positional_data = full_data.query("position == @player_position")
    if positional_data.empty:
        st.warning(f"No positional data found for position: {player_position}")
        return

    positional_data = positional_data.query("week in @selected_weeks_range")
    # Update positional-related tables
    tables["positional_data"] = positional_data
    positional_totals = scoring.calculate_total_stats(positional_data)
    tables["position_ranks_totals"] = scoring.make_position_ranks(positional_totals)
    positional_averages = scoring.calculate_avg_stats(positional_data)
    tables["position_ranks_averages"] = scoring.make_position_ranks(positional_averages)

    # Store back to session state
    state["tables"] = tables







