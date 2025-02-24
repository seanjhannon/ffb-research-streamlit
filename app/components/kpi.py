import numpy as np
import streamlit as st

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


def make_cards_from_stats(state,
                          stat_category: str,
                          stat_dict):

    selected_player_name = state["user_input"]["selected_player"]["name"]
    # Render the category header
    st.markdown(f"<h2 style='text-align: center;'>{stat_category}</h2>", unsafe_allow_html=True)
    # Return early if there are no stats to display
    if not stat_dict:
        return

    # Convert the dictionary keys to a list for predictable ordering
    keys = list(stat_dict.keys())

    tables = state["tables"]
    player_totals = tables["player_stat_totals"]
    player_totals_ranks = tables["position_ranks_totals"].query("player_display_name == @selected_player_name")
    player_averages = tables["player_stat_averages"]
    player_averages_ranks = tables["position_ranks_averages"].query("player_display_name == @selected_player_name")

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



def make_cards_from_stats(player,
                          stat_category: str,
                          stat_dict):

    # Render the category header
    st.markdown(f"<h2 style='text-align: center;'>{stat_category}</h2>", unsafe_allow_html=True)
    # Return early if there are no stats to display
    if not stat_dict:
        return

    # Convert the dictionary keys to a list for predictable ordering
    keys = list(stat_dict.keys())

    tables = player["tables"]
    player_totals = tables["player_stat_totals"]
    player_totals_ranks = tables["position_ranks_totals"].query("player_display_name == @player['name']")
    player_averages = tables["player_stat_averages"]
    player_averages_ranks = tables["position_ranks_averages"].query("player_display_name == @player['name']")

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



def player_kpis(page_key,
                player_index=0):


    state = getattr(st.session_state, page_key)
    player = state["players"][player_index]
    scoring_stats, opportunity_stats, advanced_stats = get_position_kpis(player['position'])

    scoring_kpis_cols = st.columns(3)

    with scoring_kpis_cols[0]:
        make_cards_from_stats(player = player,
                              stat_category='Production',
                              stat_dict=scoring_stats)


    with scoring_kpis_cols[1]:
        make_cards_from_stats(player = player,
                              stat_category='Opportunity',
                              stat_dict=opportunity_stats)

    with scoring_kpis_cols[2]:
        make_cards_from_stats(player = player,
                              stat_category='Advanced',
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
