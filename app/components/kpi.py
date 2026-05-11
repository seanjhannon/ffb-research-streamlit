import numpy as np
import streamlit as st

import numpy as np
import streamlit as st


def xfp_kpi_card(player_name: str, xfp_metrics: dict, comp_metrics: dict = None):
    """Specialized KPI card for XFP metrics."""
    unique_id = player_name + "xfp"
    
    with st.container(border=True):
        st.markdown("**Expected Fantasy Points**")
        
        # Expected FP
        expected_fp = xfp_metrics.get('expected_fp', 0.0)
        actual_fp = xfp_metrics.get('actual_fp', 0.0)
        efficiency = xfp_metrics.get('efficiency', 0.0)
        over_under = xfp_metrics.get('over_under', 0.0)
        
        if comp_metrics:
            comp_expected = comp_metrics.get('expected_fp', 0.0)
            comp_actual = comp_metrics.get('actual_fp', 0.0)
            comp_efficiency = comp_metrics.get('efficiency', 0.0)
            
            delta_expected = round(expected_fp - comp_expected, 1)
            delta_actual = round(actual_fp - comp_actual, 1)
            delta_efficiency = round(efficiency - comp_efficiency, 3)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Expected FP", f"{expected_fp:.1f}", delta=f"{delta_expected:+.1f}")
            with col2:
                st.metric("Actual FP", f"{actual_fp:.1f}", delta=f"{delta_actual:+.1f}")
            
            st.metric("Efficiency", f"{efficiency:.3f}", delta=f"{delta_efficiency:+.3f}")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Expected FP", f"{expected_fp:.1f}")
            with col2:
                st.metric("Actual FP", f"{actual_fp:.1f}")
            
            # Color-code efficiency
            if efficiency > 1.1:
                delta_color = "normal"  # Green for overperforming
            elif efficiency < 0.9:
                delta_color = "inverse"  # Red for underperforming
            else:
                delta_color = "off"  # Gray for neutral
            
            st.metric("Efficiency", f"{efficiency:.3f}", 
                     delta=f"{over_under:+.1f}", 
                     delta_color=delta_color)


def display_xfp_section(player, comp_player=None):
    """Display XFP section if available."""
    tables = player["tables"]
    
    if not tables.get("xfp_enabled", False):
        return
    
    xfp_metrics = tables.get("xfp_metrics", {})
    comp_xfp_metrics = comp_player["tables"].get("xfp_metrics", {}) if comp_player else None
    
    st.subheader("Expected Fantasy Points Analysis")
    
    if comp_player:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{player['name']}**")
            xfp_kpi_card(player['name'], xfp_metrics, comp_xfp_metrics)
        with col2:
            st.markdown(f"**{comp_player['name']}**")
            xfp_kpi_card(comp_player['name'], comp_xfp_metrics, xfp_metrics)
    else:
        xfp_kpi_card(player['name'], xfp_metrics)


def _get_xfp_kpis():
    """Get XFP-related KPI definitions."""
    return {
        'xfp_expected_fp': ('Expected FP', 'total'),
        'xfp_actual_fp': ('Actual FP', 'total'), 
        'xfp_efficiency': ('Efficiency', 'avg'),
        'xfp_over_under': ('Over/Under', 'total')
    }


def _render_xfp_kpi_card(col, player, key, label, display_mode, comp_player=None):
    """Render XFP KPI card with special handling."""
    tables = player["tables"]
    
    # Debug output
    print(f"🔍 XFP Card Debug for {player['name']}:")
    print(f"  - xfp_enabled: {tables.get('xfp_enabled', False)}")
    print(f"  - xfp_metrics: {tables.get('xfp_metrics', {})}")
    
    # Only show XFP metrics if XFP is enabled
    if not tables.get("xfp_enabled", False):
        with col:
            st.metric(label, "N/A", delta="XFP disabled")
        return
    
    xfp_metrics = tables.get("xfp_metrics", {})
    
    if comp_player:
        comp_xfp_metrics = comp_player["tables"].get("xfp_metrics", {})
    else:
        comp_xfp_metrics = None
    
    with col:
        if key == 'xfp_expected_fp':
            value = xfp_metrics.get('expected_fp', 0.0)
            delta = None
            if comp_xfp_metrics:
                delta = f"{value - comp_xfp_metrics.get('expected_fp', 0.0):+.1f}"
            st.metric(label, f"{value:.1f}", delta=delta)
            
        elif key == 'xfp_actual_fp':
            value = xfp_metrics.get('actual_fp', 0.0)
            delta = None
            if comp_xfp_metrics:
                delta = f"{value - comp_xfp_metrics.get('actual_fp', 0.0):+.1f}"
            st.metric(label, f"{value:.1f}", delta=delta)
            
        elif key == 'xfp_efficiency':
            value = xfp_metrics.get('efficiency', 0.0)
            delta = None
            if comp_xfp_metrics:
                delta = f"{value - comp_xfp_metrics.get('efficiency', 0.0):+.3f}"
            
            # Color-code efficiency
            if value > 1.1:
                delta_color = "normal"  # Green for overperforming
            elif value < 0.9:
                delta_color = "inverse"  # Red for underperforming
            else:
                delta_color = "off"  # Gray for neutral
                
            st.metric(label, f"{value:.3f}", delta=delta, delta_color=delta_color)
            
        elif key == 'xfp_over_under':
            value = xfp_metrics.get('over_under', 0.0)
            delta = None
            if comp_xfp_metrics:
                delta = f"{value - comp_xfp_metrics.get('over_under', 0.0):+.1f}"
            
            # Color-code over/under performance
            if value > 0:
                delta_color = "normal"  # Green for overperforming
            elif value < 0:
                delta_color = "inverse"  # Red for underperforming
            else:
                delta_color = "off"  # Gray for neutral
                
            st.metric(label, f"{value:+.1f}", delta=delta, delta_color=delta_color)


def kpi_card(player_name:str, stat_label: str, total_value, avg_value, total_rank, avg_rank, display_mode: str,
             comp_total=None, comp_avg=None):
    """KPI card showing either Total, Average, or a toggleable view."""
    unique_id = player_name + stat_label

    # Ensure values are properly rounded
    if isinstance(total_value, np.float32):
        total_value = round(float(total_value), 2)
    if isinstance(avg_value, np.float32):
        avg_value = round(float(avg_value), 2)

    with st.container(border=True):  # Ensures uniform spacing

        toggle_placeholder = st.empty()  # Ensures the toggle space is always reserved

        if display_mode == "both":
            show_total = toggle_placeholder.toggle("Show Total", value=True, key=f"toggle_{unique_id}")
        else:
            toggle_placeholder.markdown("⠀")
            show_total = display_mode == "total"

        if show_total: #TOTAL STATS
            # if comparison mode
            if comp_total:
                delta_val = np.round(total_value - comp_total, 2)
                st.metric(label=f"Total {stat_label}",
                          value=total_value,
                          delta=f"{delta_val} (Rank {int(total_rank)})",
                          delta_color= "normal")
            else:
                st.metric(label=f"Total {stat_label}", value=total_value, delta=f"Rank {int(total_rank)}", delta_color="off")
        else: #AVERAGE STATS
            if comp_avg:
                delta_val = np.round(avg_value - comp_avg)
                st.metric(label=f"Avg {stat_label}",
                          value=avg_value,
                          delta=f"{delta_val} (Rank {int(avg_rank)})",
                          delta_color="normal")
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
        comp_player_totals = comp_tables["player_stat_totals"]
        comp_player_averages = comp_tables["player_stat_averages"]

    for row in rows:
        cols = st.columns(len(row))

        for col, key in zip(cols, row):
            label = stat_dict[key][0]
            display_mode = stat_dict[key][1]
            
            # Handle XFP metrics specially
            if key.startswith('xfp_'):
                _render_xfp_kpi_card(col, player, key, label, display_mode, comp_player)
            else:
                # Regular KPI handling
                total_value = round(player_totals[key], 2)
                total_rank = player_totals_ranks[key].iloc[0]

                avg_value = round(player_averages[key], 2)
                avg_rank = player_averages_ranks[key].iloc[0]

                if comp_player:
                    comp_total = comp_player_totals[key]
                    comp_avg = comp_player_averages[key]
                else:
                    comp_total, comp_avg = None, None

                with col:
                    kpi_card(player['name'], label, total_value, avg_value, total_rank, avg_rank, display_mode,
                                                            comp_total, comp_avg)


def player_kpis(page_key, player_index=0, comp_player_index=None):
    """Render all KPI sections in a dense layout with total & average values."""
    state = getattr(st.session_state, page_key)

    player = state["players"][player_index]
    stat_dict = get_position_kpis(player['position'])

    comp_player = state["players"][comp_player_index] if comp_player_index is not None else None

    with st.container():
        # Display all KPIs including XFP metrics
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
        
        # Add XFP metrics if available
        stat_dict.update(_get_xfp_kpis())
        
        return stat_dict


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
        
        # Add XFP metrics if available
        stat_dict.update(_get_xfp_kpis())
        
        return stat_dict

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
        
        # Add XFP metrics if available
        stat_dict.update(_get_xfp_kpis())
        
        return stat_dict

    return stat_dict
