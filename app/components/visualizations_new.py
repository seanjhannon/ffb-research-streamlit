import pandas as pd
import streamlit as st
import utils.data_loader as data_loader
import numpy as np
import plotly.graph_objects as go


def FormatSelector():
    st.selectbox(
        'Select scoring format',
        options=st.session_state.scoring_formats,
        format_func=lambda x: x.name,
        key="selected_scoring_format",  # Flat key in st.session_state
        on_change=data_loader.generic_on_change,
        args=(
            "selected_scoring_format",    # Flat key to look up the new value
            None,                         # No nested remapping needed
            [data_loader.update_all_tables_player_details]  # Extra update functions
        )
    )



def Header(page_state):

    headshot_col, name_col, selectors_col = st.columns(3)

    with selectors_col:
        FormatSelector()

        st.number_input(
            'Choose a year',
            min_value=1999,
            value=page_state["user_input"]["selected_year"],
            step=1,
            key="selected_year",  # flat key
            on_change=data_loader.generic_on_change,
            args=(
                "selected_year",                # flat key
                ["user_input", "selected_year"],  # nested path
                [data_loader.update_all_tables_player_details]
            )
        )

        display_names = page_state["tables"]["full_data"]['player_display_name'].unique().tolist()


        st.selectbox(
            "Choose a player",
            options=display_names,
            key="player_select",  # This is the flat key where Streamlit stores the value
            on_change=data_loader.generic_on_change,
            args=(
                "player_select",  # flat key
                ["user_input", "selected_player", "name"],  # nested path inside player_details
                [data_loader.refresh_child_tables_player_details,
                 ]  # any extra functions to run
            )
        )

        st.write(st.session_state.player_details["user_input"]["selected_player"]["name"])
        WeekSelector(page_state)


    selected_player_firstname = page_state["user_input"]["selected_player"]["name"].split(' ')[0]
    selected_player_lastname = ' '.join(page_state["user_input"]["selected_player"]["name"].split(' ')[1:]) # Handles juniors

    selected_player_headshot = page_state["tables"]["player_data"]['headshot_url'].iloc[0]
    selected_player_position = page_state["tables"]["player_data"]['position'].iloc[0]
    selected_player_team = page_state["tables"]["player_data"]['recent_team'].iloc[-1] #gets most recent value in case of a trade


    with headshot_col:
        st.image(selected_player_headshot)

    with name_col:
        st.subheader(selected_player_firstname)
        st.header(selected_player_lastname)
        st.write(f"{selected_player_team}, {selected_player_position} ")


    return



def WeekSelector(page_state):
    current_weeks = page_state["user_input"]["selected_weeks"]
    all_weeks = page_state["tables"]["full_data"]['week'].unique().tolist()
    if len(all_weeks) == 1:
        return
    else:
        st.slider(
            "Select a range of weeks",
            min_value=min(all_weeks),
            max_value=max(all_weeks),
            value=current_weeks,
            step=1,
            key="selected_weeks",  # flat key for the slider widget
            on_change=data_loader.generic_on_change,
            args=(
                "selected_weeks",
                ["user_input", "selected_weeks"],
                [data_loader.refresh_child_tables_player_details]  # assuming update_state refreshes your tables for the new week range
            )
        )
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
            'passing_air_yards': 'Air Yards',
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

    rank_color = "green" if (rank <= 10 and value > 0) else "white"

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

    if nonzero_points_series.sum() == 0:
        st.write("This dude didn't score any points in this time period!")
        return

    # Extract categories and values programmatically
    categories = nonzero_points_series.index.tolist()  # List of categories
    values = nonzero_points_series.values.tolist()
    # List of corresponding values

    st.subheader(f"How {st.session_state.selected_player} Scores")
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Fantasy Scoring',
        hovertemplate='<b>Stat</b>: %{theta} <br>'
                      '<b>Points Scored</b>: %{r}<br>'
                      '<extra></extra>'
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
        # title="Fantasy Football Scoring Breakdown",
        template='plotly_dark'  # Optional: adds a dark theme to the chart
    )
    st.write(fig)


def CustomBar(player_data):
    # Title
    st.subheader("Self-Service Bar Chart")

    player_data_numeric = (player_data.drop(columns=[
        "season", "week", "fantasy_points", "fantasy_points_ppr"
    ]).rename(columns={"calc_fantasy_points": "fantasy_points"}).select_dtypes(include=np.number))

    valid_cols = (player_data_numeric != 0).any() & player_data_numeric.notna().any()
    df_non_zero = player_data_numeric.loc[:, valid_cols]

    # Dropdown to select y-axis column
    y_column = st.selectbox(
        "Select a column to graph (y-axis):",
        options=df_non_zero.columns,
        format_func=lambda col: col.replace("_", " ").title(),
    )

    # Ensure we're plotting from df_non_zero
    st.bar_chart(data=df_non_zero.set_index(player_data["week"])[[y_column]])







