import streamlit as st
import nfl_data_py as nfl
import scoring
import pandas as pd

st.set_page_config(layout="wide")


col1, col2, col3 = st.columns([1, 2, 1])

with col3: # by defining cols out of order I can avoid referencing variables before assignment while preserving layout
    # YEAR SELECTION
    chosen_year = int(st.text_input('Choose a year', '2024'))
    @st.cache_data(show_spinner="Loading data ...")  # make this funny
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

# Filter Data here and apply scoring format before displaying
filtered_data = weekly_data.query(f"player_display_name == @selected_name")
filtered_data["calc_fantasy_points"] = filtered_data.apply(
    lambda row: scoring.calculate_fantasy_points(row, selected_scoring_format, scoring.stat_mapping_nfl_py),
    axis=1
)

# Player name and image
with col1:
    st.image(filtered_data['headshot_url'][0])

with col2:

    player_first_name, player_last_name = selected_name.split(' ')
    st.subheader(player_first_name)
    st.header(player_last_name)


# WEEK SELECTION
weeks = weekly_data['week'].unique().tolist()

start_num, end_num = st.slider( # will eventually need to handle multiple years
    "Select a range of weeks",
    min_value=min(weeks),
    max_value=max(weeks),
    value=(min(weeks), max(weeks)),  # Default to full range
    step=1
)
# Get the selected slice of numbers
selected_weeks = weeks[start_num-1:end_num]



# Optional: Display as a simple chart
st.bar_chart(selected_weeks)



st.write(filtered_data)