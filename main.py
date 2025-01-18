import streamlit as st
import nfl_data_py as nfl
import scoring
import plotly.graph_objects as go

import pandas as pd

st.set_page_config(layout="wide")

STAT_MAPPING = scoring.stat_mapping_nfl_py

col1, col2, col3 = st.columns([1, 2, 1])

with col3:
    # YEAR SELECTION
    chosen_year = int(st.text_input('Choose a year', '2024'))


    @st.cache_data(show_spinner="Loading data ...")  # Load year data with caching
    def load_data_one_year(year):
        """Loads a single year of data in a cached manner"""
        return nfl.import_weekly_data([year])


    # Pull in data for chosen years here to make names accessible
    weekly_data = load_data_one_year(chosen_year)
    names = weekly_data['player_display_name'].unique().tolist()

    selected_name = st.selectbox(
        "Search for a player:",
        options=names,
        placeholder="Start typing to search...",
    )

    scoring_formats = {
        "Standard": scoring.StandardScoringFormat(),
        "PPR": scoring.PPRScoringFormat()
    }

    # Sidebar functionality for scoring format
    with st.sidebar:
        st.header("Scoring Format")
        selected_scoring_format_name = st.selectbox(
            "Choose a scoring format",
            options=["Standard", "PPR", "Custom"]
        )

        if selected_scoring_format_name in scoring_formats:
            st.subheader(f"Selected Format: {selected_scoring_format_name}")
            st.header("Scoring Format Details")
            selected_scoring_format = scoring_formats[selected_scoring_format_name]
            st.markdown(selected_scoring_format.to_markdown())
        else:
            st.subheader("Custom Scoring Format")
            # Custom scoring inputs
            passing_td = st.number_input("Points per Passing TD", min_value=0, value=4)
            rushing_td = st.number_input("Points per Rushing TD", min_value=0, value=6)
            receiving_td = st.number_input("Points per Receiving TD", min_value=0, value=6)
            reception = st.number_input("Points per Reception", min_value=0, value=0)
            fumble = st.number_input("Points per Fumble", min_value=-10, value=-2)

            # Save custom scoring format as a dictionary
            custom_format = {
                "Passing TD": passing_td,
                "Rushing TD": rushing_td,
                "Receiving TD": receiving_td,
                "Reception": reception,
                "Fumble": fumble,
            }
            st.json(custom_format)  # Display custom scoring format as JSON


# Reset filtered data every time the player is selected
@st.cache_data(show_spinner="Loading player data ...")
def filter_player_data(weekly_data, selected_name):
    """Filters the data for the selected player"""
    return weekly_data.query(f"player_display_name == @selected_name")


# Filter the data for the selected player
filtered_data = filter_player_data(weekly_data, selected_name)
filtered_data["calc_fantasy_points"] = filtered_data.apply(
    lambda row: scoring.calculate_fantasy_points(row, selected_scoring_format, STAT_MAPPING),
    axis=1
)

# Player name and image
with col1:
    st.image(filtered_data['headshot_url'].iloc[0])

with col2:
    player_first_name, player_last_name = selected_name.split(' ')
    st.subheader(player_first_name)
    st.header(player_last_name)

# WEEK SELECTION
weeks = filtered_data['week'].unique().tolist()

start_num, end_num = st.slider(  # will eventually need to handle multiple years
    "Select a range of weeks",
    min_value=min(weeks),
    max_value=max(weeks),
    value=(min(weeks), max(weeks)),  # Default to full range
    step=1
)

# Get the selected slice of numbers
selected_weeks = weeks[start_num - 1:end_num + 1]  # inclusive of last week

# filter data by above conditions for use in graphs
filtered_data = filtered_data.query("week in @selected_weeks")

# Get points by category for radar chart
points_by_category = scoring.calculate_fantasy_points_by_category(filtered_data, selected_scoring_format, STAT_MAPPING)

# Filter the Series to non-zero values
nonzero_points_series = points_by_category[points_by_category != 0]

# Extract categories and values programmatically
categories = nonzero_points_series.index.tolist()  # List of categories
values = nonzero_points_series.values.tolist()  # List of corresponding values

# Create a radar chart with Plotly
fig = go.Figure()

fig.add_trace(go.Scatterpolar(
    r=values,
    theta=categories,
    fill='toself',
    name='Fantasy Scoring'
))

# Dynamically adjust the range based on the values
max_value = max(values)
fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, max_value * 1.1]  # Slightly expand the range for aesthetics
        )
    ),
    showlegend=False,
    title="Fantasy Football Scoring Breakdown",
    template='plotly_dark'  # Optional: adds a dark theme to the chart
)

# Display the radar chart in Streamlit
st.plotly_chart(fig)

# Optional: Display as a simple chart
st.bar_chart(selected_weeks)

st.write(filtered_data)
