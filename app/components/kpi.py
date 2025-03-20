import numpy as np
import streamlit as st

import numpy as np
import streamlit as st


def kpi_card(player_name:str, stat_label: str, total_value, avg_value, total_rank, avg_rank, display_mode: str,
             comp_total_rank=None, comp_avg_rank=None):
    """KPI card showing either Total, Average, or a toggleable view."""
    unique_id = player_name + stat_label

    # Ensure values are properly rounded
    if isinstance(total_value, np.float32):
        total_value = round(float(total_value), 2)
    if isinstance(avg_value, np.float32):
        avg_value = round(float(avg_value), 2)

    def top_10(rank):
        return "-" if rank <= 10 else ""

    with st.container(border=True):  # Ensures uniform spacing

        toggle_placeholder = st.empty()  # Ensures the toggle space is always reserved

        if display_mode == "both":
            show_total = toggle_placeholder.toggle("Show Total", value=True, key=f"toggle_{unique_id}")
        else:
            toggle_placeholder.markdown("⠀")
            show_total = display_mode == "total"

        # Keep KPI metric inside the same container
        if show_total:
            delta_val = total_rank - comp_total_rank if comp_total_rank is not None else None

            # if comparison mode
            if comp_total_rank:
                delta_val = total_rank - comp_total_rank
                st.metric(label=f"Total {stat_label}",
                          value=total_value,
                          delta=f"{int(delta_val)} (Rank {int(total_rank)})",
                          delta_color="inverse")
            else:
                st.metric(label=f"Total {stat_label}", value=total_value, delta=f"Rank {int(total_rank)}", delta_color="off")
        else:
            if comp_avg_rank:
                delta_val = total_rank - comp_avg_rank
                st.metric(label=f"Total {stat_label}",
                          value=total_value,
                          delta=f"{int(delta_val)}, (Rank {int(comp_avg_rank)})",
                          delta_color="inverse")
            else:
                st.metric(label=f"Avg {stat_label}", value=avg_value, delta=f"Rank {int(avg_rank)}", delta_color="off")



def make_cards_from_stats(player, stat_dict, comp_player=None):
    """Render KPIs in a compact grid with totals and averages side by side."""
    if not stat_dict:
        return

    keys = list(stat_dict.keys())
    cols_per_row = 5 if comp_player is None else 3 # Maintain dense layout

    rows = [keys[i:i + cols_per_row] for i in range(0, len(keys), cols_per_row)]

    tables = player["tables"]
    player_totals = tables["player_stat_totals"]
    player_totals_ranks = tables["position_ranks_totals"].query("player_display_name == @player['name']")
    player_averages = tables["player_stat_averages"]
    player_averages_ranks = tables["position_ranks_averages"].query("player_display_name == @player['name']")

    if comp_player: # get just the ranks for comparison
        comp_tables = comp_player["tables"]
        comp_player_totals_ranks = comp_tables["position_ranks_totals"].query("player_display_name == @comp_player['name']")
        comp_player_averages_ranks = comp_tables["position_ranks_averages"].query("player_display_name == @comp_player['name']")


    for row in rows:
        cols = st.columns(len(row))

        for col, key in zip(cols, row):
            label = stat_dict[key][0]
            display_mode = stat_dict[key][1]
            total_value = round(player_totals[key], 2)
            total_rank = player_totals_ranks[key].iloc[0]

            avg_value = round(player_averages[key], 2)
            avg_rank = player_averages_ranks[key].iloc[0]

            if comp_player:
                comp_total_rank = comp_player_totals_ranks[key].iloc[0]
                comp_avg_rank = comp_player_averages_ranks[key].iloc[0]
            else:
                comp_total_rank, comp_avg_rank = None, None

            with col:
                kpi_card(player['name'], label, total_value, avg_value, total_rank, avg_rank, display_mode,
                                                        comp_total_rank, comp_avg_rank)


def player_kpis(page_key, player_index=0, comp_player_index=None):
    """Render all KPI sections in a dense layout with total & average values."""
    state = getattr(st.session_state, page_key)

    player = state["players"][player_index]
    stat_dict = get_position_kpis(player['position'])

    comp_player = state["players"][comp_player_index] if comp_player_index is not None else None


    with st.container():
        make_cards_from_stats(player, stat_dict, comp_player)





def get_position_kpis(position:str):
    if position in [ 'WR', 'TE']:
        stat_dict = {
            'calc_fantasy_points': ('Fantasy Points', 'both'), # continue for all
            'receiving_yards': ('Receiving Yards', 'both'),
            'targets': ('Targets', 'both'),
            'receiving_yards_after_catch': ('YAC', 'both'),
            'receiving_epa': ('Receiving EPA', 'avg'),

            'receiving_tds': ('Receiving TDs', 'both'),
            'receptions': ('Receptions', 'both'),
            'target_share': ('Target Share', 'avg'),
            'receiving_air_yards': ('Air Yards', 'both'),
            'wopr': ('WOPR', 'avg'),
        }


    elif position == 'RB':
        stat_dict = {
            'calc_fantasy_points': ('Fantasy Points', 'both'), # continue for all
            'rushing_yards': ('Rushing Yards', 'both'),
            'receiving_yards': ('Receiving Yards', 'both'),
            'targets': ('Targets', 'both'),
            # 'receiving_yards_after_catch': ('YAC', 'both'),
            'rushing_epa': ('Rushing EPA', 'avg'),
            'rushing_tds': ('Rushing TDs', 'both'),
            'receiving_tds': ('Receiving TDs', 'both'),
            'carries': ('Carries', 'both'),
            'receptions': ('Receptions', 'both'),
        }

    else : #position is QB
        stat_dict = {
            'calc_fantasy_points': ('Fantasy Points', 'both'),
            'passing_yards': ('Passing Yards', 'both'),
            'passing_tds': ('Passing TDs', 'both'),
            'rushing_yards': ('Rushing Yards', 'both'),
            'rushing_tds': ('Rushing TDs', 'both'),
           'attempts': ('Attempts', 'both'),
            'passing_air_yards': ('Air Yards', 'both'),
            'carries': ('Carries', 'both'),
            'passing_epa': ('Average Passing EPA', 'avg'),
            'pacr': ('PACR', 'avg')
        }

    return stat_dict
