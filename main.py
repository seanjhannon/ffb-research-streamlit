import streamlit as st
import nfl_data_py as nfl
import pandas as pd

# YEAR SELECTION
chosen_year = int(st.text_input('Choose a year', '2024'))

@st.cache_data(show_spinner = "Loading data ...") # make this funny 
def load_data_one_year(year):
    """Loads a single year of data in a cached manner"""
    return nfl.import_weekly_data([year])

weekly_data = load_data_one_year(chosen_year)

print(weekly_data)


# PLAYER SELECTION
names = weekly_data['player_display_name'].unique().tolist()
selected_name = st.selectbox(
    "Search for a player:",
    options=names,
    placeholder="Start typing to search...",
)
if selected_name:
    st.write(f"You selected: {selected_name}")


# WEEK SELECTION
weeks = weekly_data['week'].unique().tolist()

# Create a slider that returns a tuple of (start, end) values
start_num, end_num = st.slider(
    "Select a range of numbers",
    min_value=min(weeks),
    max_value=max(weeks),
    value=(min(weeks), max(weeks)),  # Default to full range
    step=1
)
# Get the selected slice of numbers
selected_weeks = weeks[start_num-1:end_num]


filtered_data = weekly_data.query(f"player_display_name == @selected_name")


# Optional: Display as a simple chart
st.bar_chart(selected_weeks)



st.write(filtered_data)