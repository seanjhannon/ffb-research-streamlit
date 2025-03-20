import numpy as np
import streamlit as st


def kpi_card(name: str, total_value, avg_value, total_rank, avg_rank, display_mode: str):
    """KPI card showing either Total, Average, or a toggleable view."""
    unique_id = name

    # Ensure values are properly rounded
    if isinstance(total_value, np.float32):
        total_value = round(float(total_value), 2)
    if isinstance(avg_value, np.float32):
        avg_value = round(float(avg_value), 2)

    def top_10(rank):
        return "-" if rank <= 10 else ""

    with st.container(border=True):  # Ensures uniform spacing

        # Keep KPI metric inside the same container
        if display_mode == "total":
            st.metric(label=f"Total {name}", value=total_value, delta=f"Rank {int(total_rank)}", delta_color="off")
        else:
            st.metric(label=f"Avg {name}", value=avg_value, delta=f"Rank {int(avg_rank)}", delta_color="off")
        toggle_placeholder = st.empty()  # Ensures the toggle space is always reserved



        if display_mode == "both":
            show_total = toggle_placeholder.toggle("Show Total", value=True, key=f"toggle_{unique_id}")
        else:
            toggle_placeholder.markdown("⠀")
            show_total = display_mode == "total"



def make_cards_from_stats(player, stat_category: str, stat_dict):
    """Render KPIs in a compact grid with totals and averages side by side."""
    if not stat_dict:
        return

    # st.markdown(f"<h4 style='margin-bottom: 4px;'>{stat_category}</h4>", unsafe_allow_html=True)

    keys = list(stat_dict.keys())
    cols_per_row = 5  # Maintain dense layout

    rows = [keys[i:i + cols_per_row] for i in range(0, len(keys), cols_per_row)]

    tables = player["tables"]
    player_totals = tables["player_stat_totals"]
    player_totals_ranks = tables["position_ranks_totals"].query("player_display_name == @player['name']")
    player_averages = tables["player_stat_averages"]
    player_averages_ranks = tables["position_ranks_averages"].query("player_display_name == @player['name']")

    for row in rows:
        cols = st.columns(len(row))  # Keep the tight layout

        for col, key in zip(cols, row):
            label = stat_dict[key][0]
            display_mode = stat_dict[key][1]
            total_value = round(player_totals[key], 2)
            total_rank = player_totals_ranks[key].iloc[0]

            avg_value = round(player_averages[key], 2)
            avg_rank = player_averages_ranks[key].iloc[0]

            with col:
                kpi_card(label, total_value, avg_value, total_rank, avg_rank, display_mode)


def player_kpis(page_key, player_index=0):
    """Render all KPI sections in a dense layout with total & average values."""
    state = getattr(st.session_state, page_key)
    player = state["players"][player_index]
    scoring_stats, opportunity_stats, advanced_stats = get_position_kpis(player['position'])

    with st.container():
        make_cards_from_stats(player, 'Production', scoring_stats)

    with st.container():
        make_cards_from_stats(player, 'Opportunity', opportunity_stats)

    with st.container():
        make_cards_from_stats(player, 'Advanced', advanced_stats)


def get_position_kpis(position:str):
    if position in [ 'WR', 'TE']:
        production_stats = {
            'calc_fantasy_points': ('Fantasy Points', 'both'), # continue for all
            'receiving_yards': ('Receiving Yards', 'both'),
            'targets': ('Targets', 'both'),
            'receiving_yards_after_catch': ('YAC', 'both'),
            'receiving_epa': ('Receiving EPA', 'avg'),

        }
        opportunity_stats = {
            'receiving_tds': ('Receiving TDs', 'both'),
            'receptions': ('Receptions', 'both'),
            'target_share': ('Target Share', 'avg'),
            'receiving_air_yards': ('Air Yards', 'both'),
            'wopr': ('WOPR', 'avg'),
            # 'air_yards_share': 'Air Yards Share',

        }
        advanced_stats = {

            # 'racr': 'RACR'
        }
    elif position == 'RB':
        production_stats = {
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
        production_stats = {
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

    return production_stats, opportunity_stats, advanced_stats

#
# def make_cards_from_stats(state,
#                           stat_category: str,
#                           stat_dict):
#
#     selected_player_name = state["user_input"]["selected_player"]["name"]
#     # Render the category header
#     st.markdown(f"<h2 style='text-align: center;'>{stat_category}</h2>", unsafe_allow_html=True)
#     # Return early if there are no stats to display
#     if not stat_dict:
#         return
#
#     # Convert the dictionary keys to a list for predictable ordering
#     keys = list(stat_dict.keys())
#
#     tables = state["tables"]
#     player_totals = tables["player_stat_totals"]
#     player_totals_ranks = tables["position_ranks_totals"].query("player_display_name == @selected_player_name")
#     player_averages = tables["player_stat_averages"]
#     player_averages_ranks = tables["position_ranks_averages"].query("player_display_name == @selected_player_name")
#
#     # Decide the number of cards per row:
#     # - If there are more than 3 stats, use 3 per row.
#     # - Otherwise, use all available stats in one row.
#     chunk_size = 3 if len(keys) > 3 else len(keys)
#
#     # Process the keys in chunks so that each chunk represents one row of cards
#     for i in range(0, len(keys), chunk_size):
#         chunk_keys = keys[i:i + chunk_size]
#         # Create columns based on the number of stats in this chunk
#         cols = st.columns(len(chunk_keys))
#
#         # Render each card in its corresponding column
#         for col, key in zip(cols, chunk_keys):
#             label = stat_dict[key]
#             # Choose the value based on whether the label starts with "Average"
#             if label.startswith("Average"):
#                 stat_value = round(player_averages[key], 2)
#                 rank = player_averages_ranks[key]
#             else:
#                 stat_value = round(player_totals[key], 2)
#                 rank = player_totals_ranks[key]
#
#             with col:
#                 kpi_card(
#                     label,
#                     value=stat_value,
#                     rank=rank.iloc[0]  # Adjust as needed if the data structure changes
#                 )
#
#
#
# def make_cards_from_stats(player,
#                           stat_category: str,
#                           stat_dict):
#
#     # Render the category header
#     st.markdown(f"<h2 style='text-align: center;'>{stat_category}</h2>", unsafe_allow_html=True)
#     # Return early if there are no stats to display
#     if not stat_dict:
#         return
#
#     # Convert the dictionary keys to a list for predictable ordering
#     keys = list(stat_dict.keys())
#
#     tables = player["tables"]
#     player_totals = tables["player_stat_totals"]
#     player_totals_ranks = tables["position_ranks_totals"].query("player_display_name == @player['name']")
#     player_averages = tables["player_stat_averages"]
#     player_averages_ranks = tables["position_ranks_averages"].query("player_display_name == @player['name']")
#
#     # Decide the number of cards per row:
#     # - If there are more than 3 stats, use 3 per row.
#     # - Otherwise, use all available stats in one row.
#     chunk_size = 3 if len(keys) > 3 else len(keys)
#
#     # Process the keys in chunks so that each chunk represents one row of cards
#     for i in range(0, len(keys), chunk_size):
#         chunk_keys = keys[i:i + chunk_size]
#         # Create columns based on the number of stats in this chunk
#         cols = st.columns(len(chunk_keys))
#
#         # Render each card in its corresponding column
#         for col, key in zip(cols, chunk_keys):
#             label = stat_dict[key]
#             # Choose the value based on whether the label starts with "Average"
#             if label.startswith("Average"):
#                 stat_value = round(player_averages[key], 2)
#                 rank = player_averages_ranks[key]
#             else:
#                 stat_value = round(player_totals[key], 2)
#                 rank = player_totals_ranks[key]
#
#             with col:
#                 kpi_card(
#                     label,
#                     value=stat_value,
#                     rank=rank.iloc[0]  # Adjust as needed if the data structure changes
#                 )
#
#
#
# def player_kpis(page_key,
#                 player_index=0):
#
#
#     state = getattr(st.session_state, page_key)
#     player = state["players"][player_index]
#     scoring_stats, opportunity_stats, advanced_stats = get_position_kpis(player['position'])
#
#     scoring_kpis_cols = st.columns(3)
#
#     with st.container():
#         make_cards_from_stats(player = player,
#                               stat_category='Production',
#                               stat_dict=scoring_stats)
#
#
#     with st.container():
#         make_cards_from_stats(player = player,
#                               stat_category='Opportunity',
#                               stat_dict=opportunity_stats)
#
#     with st.container():
#         make_cards_from_stats(player = player,
#                               stat_category='Advanced',
#                               stat_dict=advanced_stats)
#
#
#
#
# def kpi_card(name: str, value, rank: int):
#     """
#     Display a simple KPI card using plain Markdown.
#
#     Args:
#     - name (str): The name of the KPI.
#     - value (str): The value of the KPI.
#     - rank (str): The rank of the KPI relative to the competition.
#     """
#
#     if type(value) == np.float32:
#         value = round(float(value), 2)
#
#     rank_color = "green" if (rank <= 10 and value > 0) else "white"
#
#     st.markdown(
#         f"""
#         <div style="text-align: center;">
#             <strong>{name}</strong><br>
#             <span style="font-size: 2em;">{value}</span><br>
#             <em> Rank: <span style='color:{rank_color};'>{int(rank)}</span> </em>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )
