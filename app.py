# On year select, load in that year's data - must cache
import pandas as pd
import streamlit as st
import visualizations as viz
import scoring

STAT_MAPPING = scoring.stat_mapping_nfl_py
SCORING_FORMAT = scoring.PPRScoringFormat()

st.set_page_config(layout="wide")

# Display the header - contains headshot, name, and week/player selectors
header_container = st.container(border=True)
with header_container:
    st.session_state.position_ranks, st.session_state.weekly_player_stats = viz.Header()


# Display the week selector
week_selector_container = st.container(border=True)
with week_selector_container:
    week_boundaries, st.session_state.weekly_player_stats = viz.WeekSelector(st.session_state.weekly_player_stats)

week_range = range(week_boundaries[0], week_boundaries[1]+1)



# Week-by-week stats, with scoring determined by selected format
st.session_state.weekly_player_stats["calc_fantasy_points"] = st.session_state.weekly_player_stats.apply(
    lambda row: scoring.calculate_fantasy_points(row, SCORING_FORMAT, STAT_MAPPING),
    axis=1
)

# create player totals and averages as well as functional position ranks and points by stat for radar

st.session_state.player_totals = st.session_state.weekly_player_stats.sum()
st.session_state.player_averages = st.session_state.weekly_player_stats.mean()


st.session_state.position_ranks["calc_fantasy_points"] = st.session_state.position_ranks.apply(
    lambda row: scoring.calculate_fantasy_points(row, SCORING_FORMAT, STAT_MAPPING),
    axis=1
)


#points by stat
points_by_stat = scoring.calculate_fantasy_points_by_category(st.session_state.weekly_player_stats, SCORING_FORMAT, STAT_MAPPING)

#position ranks
positional_totals = scoring.calculate_total_stats(st.session_state.position_ranks.query('week in @week_range'))
st.session_state.position_ranks = scoring.make_position_ranks(positional_totals)


st.write(st.session_state.weekly_player_stats)

scoring_kpis_container = st.container()
with scoring_kpis_container:
    viz.ScoringKPIs(st.session_state.player_totals,
                    st.session_state.player_averages,
                    st.session_state.position_ranks,
                    st.session_state.weekly_player_stats)

charts_container = st.container()
with charts_container:
    col1, col2 = st.columns(2)

    with col1:
        radar_container = st.container()
        with radar_container:
            viz.Radar(points_by_stat)

    with col2:
        viz.CustomBar(st.session_state.weekly_player_stats)


