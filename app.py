# On year select, load in that year's data - must cache
import streamlit as st
import visualizations as viz
import scoring

STAT_MAPPING = scoring.stat_mapping_nfl_py
SCORING_FORMAT = scoring.PPRScoringFormat()

st.set_page_config(layout="wide")

# Display the header - contains headshot, name, and week/player selectors
header_container = st.container(border=True)
with header_container:
    selected_player_data = viz.Header()

# Display the week selector
week_selector_container = st.container(border=True)
with week_selector_container:
    selected_player_and_range = viz.WeekSelector(selected_player_data)


st.write(selected_player_and_range)
# Once we have the weekly data, we compute fantasy points per week, total stats, total points by stat, and position ranks

# Week-by-week stats, with scoring determined by selected format
selected_player_and_range["calc_fantasy_points"] = selected_player_and_range.apply(
    lambda row: scoring.calculate_fantasy_points(row, SCORING_FORMAT, STAT_MAPPING),
    axis=1
)

#total stats
stat_totals = scoring.calculate_total_stats(selected_player_and_range)

points_by_stat = scoring.calculate_fantasy_points_by_category(selected_player_and_range, SCORING_FORMAT, STAT_MAPPING)