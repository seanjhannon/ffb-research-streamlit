import pandas as pd
import streamlit as st
from streamlit import session_state as STATE

import data_loader
import numpy as np
import plotly.graph_objects as go


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


    def update_state(at, val):
        st.session_state.at = val

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
        # selected_year = int(year_selector()) # change to allow range

        selected_year = st.number_input('Choose a year',
                        min_value=1999,
                        step=1,
                        # value=2024,
                      key="selected_year")


        # Check if the year has changed and reload data
        if "last_selected_year" not in st.session_state or st.session_state.last_selected_year != selected_year:
            st.session_state.last_selected_year = selected_year
            st.session_state["tables"]["full_data"] = data_loader.load_data(selected_year)  # Reload data
            data_loader.update_tables()

            # st.session_state["tables"]["full_data"] = data_loader.load_data(st.session_state.selected_year)
        display_names = st.session_state["tables"]["full_data"]['player_display_name'].unique().tolist()

        # selected_player_name = name_selector(display_names)

        st.selectbox('Choose a player',
                      options = display_names,
                      key="selected_player")


    # st.session_state["tables"]["player_data"] = st.session_state["tables"]["full_data"].query(f"player_display_name == @selected_player_name")

    # This part is all data source-specific, would need to change to accommodate a different API

    selected_player_firstname = st.session_state.selected_player.split(' ')[0]
    selected_player_lastname = ' '.join(st.session_state.selected_player.split(' ')[1:]) # Handles juniors


    selected_player_headshot = st.session_state["tables"]["player_data"]['headshot_url'].iloc[0]
    selected_player_position = st.session_state["tables"]["player_data"]['position'].iloc[0]
    selected_player_team = st.session_state["tables"]["player_data"]['recent_team'].iloc[-1] #gets most recent value in case of a trade


    with headshot_col:
        headshot(selected_player_headshot)

    with name_col:
        name(selected_player_firstname,
             selected_player_lastname,
             selected_player_position,
             selected_player_team
             )

    return


def WeekSelector():
    all_weeks = st.session_state["tables"]["full_data"]['week'].unique().tolist()
    if len(all_weeks) == 1:
        # Handle single week case
        return
    else:
        # Handle normal case with a range of weeks
        new_selected_weeks = st.slider(  # will eventually need to handle multiple years
            "Select a range of weeks",
            min_value=min(all_weeks),
            max_value=max(all_weeks),
            # value=(min(all_weeks), max(all_weeks)),  # Default to full range
            step=1,
            key="selected_weeks"
        )

    # filter data by above conditions for use in graphs
    if new_selected_weeks != st.session_state.selected_weeks:
        # selected_weeks = [num for num in all_weeks if new_selected_weeks[0] <= num <= new_selected_weeks[1]]
        # st.session_state.selected_weeks = (selected_weeks[0], selected_weeks[1])
        st.session_state.selected_weeks = new_selected_weeks
        data_loader.update_tables()


    return



def get_position_kpis(position:str):

    if position in [ 'WR', 'TE']:
        scoring_stats = {
            'calc_fantasy_points': 'Fantasy Points',
            'receiving_yards': 'Receiving Yards',
            'receiving_tds': 'Receiving TDs',
            'receptions': 'Receptions'
        }

        opportunity_stats = {
            'targets': 'Targets',
            'target_share': 'Average Target Share',
            'air_yards_share': 'Average Air Yards Share',
            'wopr': 'WOPR'
        }
        advanced_stats = {
            'receiving_epa': 'Receiving EPA',
            'racr': 'RACR'
        }

    elif position == 'RB':

        scoring_stats = {
            'calc_fantasy_points': 'Fantasy Points',
            'rushing_yards': 'Rushing Yards',
            'rushing_tds': 'Rushing TDs',
            'receiving_yards': 'Receiving Yards',
            'receiving_tds': 'Receiving TDs',
        }

        opportunity_stats = {
            'carries': 'Carries',
            'targets': 'Targets',
        }

        advanced_stats = {
            'rushing_epa': 'Average Rushing EPA',
        }

    else : #position is QB
        scoring_stats = {
            'calc_fantasy_points': 'Fantasy Points',
            'passing_yards': 'Passing Yards',
            'passing_tds': 'Passing TDs',
            'rushing_yards': 'Rushing Yards',
            'rushing_tds': 'Rushing TDs',
        }

        opportunity_stats = {
            'attempts': 'Attempts',
            'passing_air_yards': 'Targets',
            'carries': 'Carries'
        }

        advanced_stats = {
            'passing_epa': 'Average Passing EPA',
            'pacr': 'PACR'
        }

    return scoring_stats, opportunity_stats, advanced_stats
###############

def make_cards_from_stats(stat_category: str, stat_dict):
    # Render the category header
    st.markdown(f"<h2 style='text-align: center;'>{stat_category}</h2>", unsafe_allow_html=True)
    # Return early if there are no stats to display
    if not stat_dict:
        return

    # Convert the dictionary keys to a list for predictable ordering
    keys = list(stat_dict.keys())

    selected_player = st.session_state.selected_player

    tables = st.session_state["tables"]
    player_totals = tables["player_stat_totals"]
    player_totals_ranks = tables["position_ranks_totals"].query("player_display_name == @selected_player")
    player_averages = tables["player_stat_averages"]
    player_averages_ranks = tables["position_ranks_averages"].query("player_display_name == @selected_player")

    # Decide the number of cards per row:
    # - If there are more than 3 stats, use 3 per row.
    # - Otherwise, use all available stats in one row.
    chunk_size = 3 if len(keys) > 3 else len(keys)

    # Process the keys in chunks so that each chunk represents one row of cards
    for i in range(0, len(keys), chunk_size):
        chunk_keys = keys[i:i + chunk_size]
        # Create columns based on the number of stats in this chunk
        cols = st.columns(len(chunk_keys))

        # Render each card in its corresponding column
        for col, key in zip(cols, chunk_keys):
            label = stat_dict[key]
            # Choose the value based on whether the label starts with "Average"
            if label.startswith("Average"):
                stat_value = round(player_averages[key], 2)
                rank = player_averages_ranks[key]
            else:
                stat_value = round(player_totals[key], 2)
                rank = player_totals_ranks[key]

            with col:
                kpi_card(
                    label,
                    value=stat_value,
                    rank=rank.iloc[0]  # Adjust as needed if the data structure changes
                )


def ScoringKPIs():

    selected_player_position = st.session_state["tables"]["player_data"]['position'].iloc[0]

    scoring_stats, opportunity_stats, advanced_stats = get_position_kpis(selected_player_position)

    scoring_kpis_cols = st.columns(3) # needs adjustment

    with scoring_kpis_cols[0]:
        make_cards_from_stats(stat_category='Production',
                              stat_dict=scoring_stats)


    with scoring_kpis_cols[1]:
        make_cards_from_stats(stat_category='Opportunity',
                              stat_dict=opportunity_stats)

    with scoring_kpis_cols[2]:
        make_cards_from_stats(stat_category='Advanced',
                              stat_dict=advanced_stats)




def kpi_card(name: str, value, rank: int):
    """
    Display a simple KPI card using plain Markdown.

    Args:
    - name (str): The name of the KPI.
    - value (str): The value of the KPI.
    - rank (str): The rank of the KPI relative to the competition.
    """

    if type(value) == np.float32:
        value = round(float(value), 2)

    rank_color = "green" if rank <= 10 else "white"

    st.markdown(
        f"""
        <div style="text-align: center;">
            <strong>{name}</strong><br>
            <span style="font-size: 2em;">{value}</span><br>
            <em> Rank: <span style='color:{rank_color};'>{int(rank)}</span> </em>
        </div>
        """,
        unsafe_allow_html=True,
    )




def Radar(points_by_stat:pd.DataFrame):
    nonzero_points_series = points_by_stat[points_by_stat != 0]

    # Extract categories and values programmatically
    categories = nonzero_points_series.index.tolist()  # List of categories
    values = nonzero_points_series.values.tolist()  # List of corresponding values

    # Create a radar chart with P
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
    st.write(fig)

def CustomBar(player_data):
    # Title
    st.title("Self-Service Bar Chart")

    non_zero_columns = player_data.any(axis=0)
    df_non_zero = player_data.loc[:, non_zero_columns]

    # Dropdown to select y-axis column
    y_column = st.selectbox("Select a column to graph (y-axis):", options=df_non_zero.columns.difference(["week"]))

    # Plotting with Streamlit native bar chart
    st.bar_chart(data=player_data.set_index("week")[[y_column]])






