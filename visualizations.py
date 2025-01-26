import pandas as pd
import streamlit as st
import data_loader

def Header():
    """ Displays header content and passes player down into subsequent components"""
    def year_selector():
        return st.text_input('Choose a year', '2024')

    def name_selector(name_options):
        return st.selectbox(
            'Search for a player:',
            options=name_options,
            placeholder='Start typing to search...'
        )

    def headshot(headshot_url: str):
        st.image(headshot_url)

    def name(
            player_fname,
            player_lname,
            player_pos,
            player_team
    ):
        st.subheader(player_fname)
        st.subheader(player_lname)
        st.write(f"{player_pos}, {player_team} ")

    headshot_col, name_col, selectors_col = st.columns(3)

    with selectors_col:
        selected_year = int(year_selector())
        year_data = data_loader.load_data_one_year(selected_year)
        display_names = year_data['player_display_name'].unique().tolist()
        selected_player_name = name_selector(display_names)

    selected_player_data = year_data.query(f"player_display_name == @selected_player_name")
    # This part is all data source-specific, would need to change to accommodate a different API
    selected_player_headshot = selected_player_data['headshot_url'].iloc[0]
    selected_player_firstname = selected_player_name.split(' ')[0]
    selected_player_lastname = ' '.join(selected_player_name.split(' ')[1:]) # Handles juniors
    selected_player_position = selected_player_data['position'].iloc[0]
    selected_player_team = selected_player_data['recent_team'].iloc[-1] #gets most recent value in case of a trade


    with headshot_col:
        headshot(selected_player_headshot)

    with name_col:
        name(selected_player_firstname,
             selected_player_lastname,
             selected_player_position,
             selected_player_team
             )

    return selected_player_data


def WeekSelector(selected_player_data: pd.DataFrame):
    all_weeks = selected_player_data['week'].unique().tolist()
    if len(all_weeks) == 1:
        # Handle single week case
        return selected_player_data
    else:
        # Handle normal case with a range of weeks
        start_num, end_num = st.slider(  # will eventually need to handle multiple years
            "Select a range of weeks",
            min_value=min(all_weeks),
            max_value=max(all_weeks),
            value=(min(all_weeks), max(all_weeks)),  # Default to full range
            step=1
        )
    selected_weeks = [num for num in all_weeks if start_num <= num <= end_num]
    # filter data by above conditions for use in graphs
    selected_player_and_range = selected_player_data.query("week in @selected_weeks")

    return selected_player_and_range