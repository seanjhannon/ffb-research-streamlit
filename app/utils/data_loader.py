import pandas as pd
import streamlit as st
import nfl_data_py as nfl
import utils.scoring as scoring
from utils.scoring import StandardScoringFormat, PPRScoringFormat
import copy


@st.cache_data(show_spinner="Loading weekly data ...")
def load_data(years):
    if years is None:
        print('No year(s) selected!?')
        return
    elif isinstance(years, list):
        year_range = years
    else:
        year_range = [years]

    return nfl.import_weekly_data(year_range, downcast=True)


@st.cache_data(show_spinner="Loading play-by-play data ...")
def load_play_by_play_data(years):
    """
    Load play-by-play data for XFP calculations.
    
    Args:
        years: Single year or list of years
        
    Returns:
        DataFrame with play-by-play data
    """
    if years is None:
        print('No year(s) selected!?')
        return pd.DataFrame()
    elif isinstance(years, list):
        year_range = years
    else:
        year_range = [years]

    try:
        # Load play-by-play data
        pbp_data = nfl.import_pbp_data(year_range, downcast=True)
        
        # Check what columns are actually available
        available_cols = pbp_data.columns.tolist()
        
        # Filter for relevant plays (plays where players can score fantasy points)
        # Use more flexible column checking
        filter_conditions = []
        
        if 'rush_attempt' in available_cols:
            filter_conditions.append(pbp_data['rush_attempt'] == 1)
        if 'pass_attempt' in available_cols:
            filter_conditions.append(pbp_data['pass_attempt'] == 1)
        if 'target' in available_cols:
            filter_conditions.append(pbp_data['target'] == 1)
        elif 'pass_target' in available_cols:
            filter_conditions.append(pbp_data['pass_target'] == 1)
        if 'scramble' in available_cols:
            filter_conditions.append(pbp_data['scramble'] == 1)
        
        if filter_conditions:
            # Combine conditions with OR
            combined_condition = filter_conditions[0]
            for condition in filter_conditions[1:]:
                combined_condition = combined_condition | condition
            
            fantasy_relevant_plays = pbp_data[combined_condition].copy()
        else:
            # Fallback: return all data if we can't identify fantasy-relevant plays
            fantasy_relevant_plays = pbp_data.copy()
        
        # Add some derived columns that might be useful
        if 'ydstogo' in fantasy_relevant_plays.columns and 'yardline_100' in fantasy_relevant_plays.columns:
            fantasy_relevant_plays['goal_to_go'] = (
                fantasy_relevant_plays['ydstogo'] <= fantasy_relevant_plays['yardline_100']
            ).astype(int)
        
        return fantasy_relevant_plays
        
    except Exception as e:
        st.error(f"Error loading play-by-play data: {str(e)}")
        return pd.DataFrame()

@st.cache_resource
def load_xfp_model():
    """Load XFP model with caching."""
    try:
        from xfp.xfp_deployment import load_xfp_model as load_xfp
        return load_xfp()
    except Exception as e:
        st.error(f"Failed to load XFP model: {str(e)}")
        return None


def setup_state_main():
    """
    Sets up global state by populating the default list of scoring formats.
    Adding of new scoring formats is handled within custom_scoring.py
    :return:
    """
    if "scoring_formats" not in st.session_state:
        st.session_state.scoring_formats = [StandardScoringFormat(), PPRScoringFormat()]
    if "selected_scoring_format" not in st.session_state:
        st.session_state["selected_scoring_format"] = st.session_state.scoring_formats[0]


def enable_xfp(page_key: str):
    """Enable XFP calculations for a page."""
    state = getattr(st.session_state, page_key)
    state["xfp_enabled"] = True
    setattr(st.session_state, page_key, state)
    update_full_data(page_key)


def disable_xfp(page_key: str):
    """Disable XFP calculations for a page."""
    state = getattr(st.session_state, page_key)
    state["xfp_enabled"] = False
    setattr(st.session_state, page_key, state)
    update_player_tables(page_key)


def _get_player_id_from_weekly_data(weekly_data: pd.DataFrame, player_name: str) -> str:
    """Get player ID from weekly data using player name."""
    player_data = weekly_data.query("player_display_name == @player_name")
    if not player_data.empty:
        # Try different possible ID columns
        for id_col in ['player_id', 'gsis_id', 'player_key']:
            if id_col in player_data.columns:
                player_id = player_data[id_col].iloc[0]
                if pd.notna(player_id):
                    return str(player_id)
    return None


def _get_player_pbp_data_by_id(pbp_data: pd.DataFrame, player_id: str) -> pd.DataFrame:
    """Get play-by-play data for a specific player using player ID."""
    if pbp_data.empty or not player_id:
        return pd.DataFrame()
    
    print(f"🔍 Looking for player ID: '{player_id}'")
    
    # List of player ID columns to check
    player_id_columns = [
        'rusher_player_id',
        'receiver_player_id', 
        'passer_player_id',
        'td_player_id',
        'fantasy_player_id'
    ]
    
    # Filter for columns that actually exist in the data
    existing_player_columns = [col for col in player_id_columns if col in pbp_data.columns]
    
    if not existing_player_columns:
        print("❌ No player ID columns found in play-by-play data")
        return pd.DataFrame()
    
    print(f"📋 Checking ID columns: {existing_player_columns}")
    
    # Create a condition that checks if the player ID appears in any of the relevant columns
    conditions = []
    for col in existing_player_columns:
        conditions.append(pbp_data[col] == player_id)
    
    # Combine conditions with OR
    combined_condition = conditions[0]
    for condition in conditions[1:]:
        combined_condition = combined_condition | condition
    
    result = pbp_data[combined_condition].copy()
    print(f"📊 Total plays found for ID {player_id}: {len(result)}")
    
    return result


def _get_player_pbp_data(pbp_data: pd.DataFrame, player_name: str) -> pd.DataFrame:
    """
    Get play-by-play data for a specific player by checking all relevant player columns.
    
    Args:
        pbp_data: Play-by-play DataFrame
        player_name: Name of the player to find
        
    Returns:
        DataFrame with plays involving the player
    """
    if pbp_data.empty:
        return pd.DataFrame()
    
    print(f"🔍 Looking for player: '{player_name}'")
    
    # List of player name columns to check
    player_name_columns = [
        'rusher_player_name',
        'receiver_player_name', 
        'passer_player_name',
        'td_player_name',
        'fantasy_player_name'
    ]
    
    # Filter for columns that actually exist in the data
    existing_player_columns = [col for col in player_name_columns if col in pbp_data.columns]
    
    if not existing_player_columns:
        print("❌ No player name columns found in play-by-play data")
        return pd.DataFrame()
    
    print(f"📋 Checking columns: {existing_player_columns}")
    
    # Debug: Show some sample player names from each column
    for col in existing_player_columns[:3]:  # Check first 3 columns
        unique_names = pbp_data[col].dropna().unique()
        print(f"📋 Sample names in {col}: {list(unique_names[:5])}")
        
        # Check for exact match
        exact_match = pbp_data[col] == player_name
        if exact_match.any():
            print(f"✅ Found exact match in {col}: {exact_match.sum()} plays")
    
    # Create a condition that checks if the player appears in any of the relevant columns
    conditions = []
    for col in existing_player_columns:
        conditions.append(pbp_data[col] == player_name)
    
    # Combine conditions with OR
    combined_condition = conditions[0]
    for condition in conditions[1:]:
        combined_condition = combined_condition | condition
    
    result = pbp_data[combined_condition].copy()
    print(f"📊 Total plays found: {len(result)}")
    
    return result

# Templates for a consistent state shape.
COMMON_STATE_TEMPLATE = {
    "selected_year": 2024,
    "selected_weeks": (0, 16),
    "selected_scoring_format": None,
    "stat_mapping": scoring.stat_mapping_nfl_py,
    "players": [],
    "full_data": None,  # Updated separately.
    "play_by_play_data": None,  # Play-by-play data for XFP calculations
    "xfp_enabled": False,  # Whether to load and calculate XFP metrics
}

PLAYER_STATE_TEMPLATE = {
    "name": "",
    "position": "",
    "tables": {},  # Holds derived tables.
}


def init_state(page_key: str, default_players: list = None):
    """
    Initialize the page's state as a top-level attribute in st.session_state.
    Only runs once per page_key, preserving existing user selections.

    Args:
        page_key (str): e.g. "player_details" or "player_comparison"
        default_players (list): A list of dicts with default player info.
    """
    if not hasattr(st.session_state, page_key):
        state = copy.deepcopy(COMMON_STATE_TEMPLATE)
        if default_players:
            for player_info in default_players:
                player = copy.deepcopy(PLAYER_STATE_TEMPLATE)
                player.update(player_info)
                state["players"].append(player)
        # set scoring format to the global value
        state.update({"selected_scoring_format":st.session_state["selected_scoring_format"]})
        setattr(st.session_state, page_key, state)



    update_full_data(page_key)


def update_full_data(page_key: str):
    """
    Update the 'full_data' for a given page. This operation can be triggered
    multiple times after initialization (e.g., after a year or scoring_format change).

    Args:
        page_key (str): The key to identify the page's state.
    """
    state = getattr(st.session_state, page_key)

    # Load weekly data (existing functionality)
    state["full_data"] = scoring.calculate_fantasy_points_vec(
        load_data(state["selected_year"]),
        state["selected_scoring_format"],
        state["stat_mapping"]
    )
    
    # Load play-by-play data if XFP is enabled
    if state.get("xfp_enabled", False):
        state["play_by_play_data"] = load_play_by_play_data(state["selected_year"])
    
    # Optional: reassign the updated state back to session_state for clarity.
    setattr(st.session_state, page_key, state)
    update_player_tables(page_key)


def update_player_tables(page_key:str):
    """
    Function to be run any time the tables relative to a specific player need to be initialized or overwritten.
    These tables include 'player' and 'positional' tables

    :param page_key:
    :return:
    """
    state = getattr(st.session_state, page_key)
    week_range = range(state["selected_weeks"][0], state["selected_weeks"][1] + 1)
    full_data = state["full_data"].loc[state["full_data"]["week"].isin(week_range)]
    for player in state["players"]:

        player_data = full_data.query(
            "player_display_name == @player['name']"
        )
        if player_data.empty:
            st.warning(f"No data found for player: {player['name']}")
            return

        positional_data = full_data.query(
            "position == @player['position']"
        )
        if positional_data.empty:
            st.warning(f"No positional data found for position: {player['position']}")
            return

        # Base tables (existing functionality)
        player_tables = {
            "player_data": player_data,
            "player_stat_totals": player_data.sum(numeric_only=True),
            "player_stat_averages": player_data.mean(numeric_only=True),
            "player_points_by_stat": scoring.calculate_fantasy_points_by_category(
                player_data, scoring_format=state["selected_scoring_format"], stat_mapping=state["stat_mapping"]
            ),
            "positional_data": positional_data,
            "position_ranks_totals": scoring.make_position_ranks(scoring.calculate_total_stats(positional_data)),
            "position_ranks_averages": scoring.make_position_ranks(scoring.calculate_avg_stats(positional_data))
        }
        
        # Add XFP calculations if play-by-play data is available
        print(f"🔍 XFP Debug for {player['name']}:")
        print(f"  - xfp_enabled: {state.get('xfp_enabled', False)}")
        print(f"  - play_by_play_data exists: {state.get('play_by_play_data') is not None}")
        
        if state.get("xfp_enabled", False) and state.get("play_by_play_data") is not None:
            print(f"  - Starting XFP calculation for {player['name']}")
            try:
                # Load XFP model (cached)
                xfp_calc = load_xfp_model()
                
                if xfp_calc is None:
                    raise Exception("XFP model failed to load")
                
                # Get player's play-by-play data using player ID
                player_id = _get_player_id_from_weekly_data(state["full_data"], player['name'])
                print(f"🔍 Player ID for {player['name']}: {player_id}")
                
                player_pbp_data = _get_player_pbp_data_by_id(
                    state["play_by_play_data"], 
                    player_id
                )
                
                print(f"📊 Found {len(player_pbp_data)} plays for {player['name']}")
                
                if not player_pbp_data.empty:
                    # Calculate XFP efficiency metrics
                    scoring_format_str = state["selected_scoring_format"].name.lower()
                    if scoring_format_str == "ppr":
                        scoring_format_str = "ppr"
                    elif scoring_format_str == "standard":
                        scoring_format_str = "standard"
                    else:
                        scoring_format_str = "ppr"  # Default fallback
                    
                    xfp_metrics = xfp_calc.calculate_player_efficiency(
                        player_pbp_data, 
                        player['name'], 
                        scoring_format_str
                    )
                    
                    print(f"✅ XFP calculated for {player['name']}: {xfp_metrics}")
                    
                    # Add XFP metrics to player tables
                    player_tables.update({
                        "xfp_metrics": xfp_metrics,
                        "player_pbp_data": player_pbp_data,
                        "xfp_enabled": True
                    })
                    
                    print(f"✅ Updated player tables for {player['name']}")
                else:
                    # No play-by-play data for this player
                    player_tables.update({
                        "xfp_metrics": {
                            'expected_fp': 0.0,
                            'actual_fp': 0.0,
                            'efficiency': 0.0,
                            'over_under': 0.0
                        },
                        "xfp_enabled": False
                    })
                    
            except Exception as e:
                print(f"❌ XFP calculation failed for {player['name']}: {str(e)}")
                import traceback
                traceback.print_exc()
                st.warning(f"XFP calculation failed for {player['name']}: {str(e)}")
                player_tables.update({
                    "xfp_metrics": {
                        'expected_fp': 0.0,
                        'actual_fp': 0.0,
                        'efficiency': 0.0,
                        'over_under': 0.0
                    },
                    "xfp_enabled": False
                })
        else:
            # XFP not enabled
            player_tables.update({
                "xfp_metrics": {
                    'expected_fp': 0.0,
                    'actual_fp': 0.0,
                    'efficiency': 0.0,
                    'over_under': 0.0
                },
                "xfp_enabled": False
            })
        
        player["tables"].update(player_tables)


# CALLBACKS

def handle_change(page_key: str,
                  attr_name:str,
                  func=None):
    """
    Generic function for handling the updating of an attribute in state
    :param page_key: top-level attribute for the page of the change
    :param attr_name: the attribute to be changed
    :param func: the table updating function to be called after the update is made
    :return: None
    """
    state = getattr(st.session_state, page_key)
    new_val = st.session_state[attr_name] #stash new value one level up as tmp
    if new_val != state[attr_name]:
        state[attr_name] = new_val
        setattr(st.session_state, page_key, state)
        func(page_key)


def handle_year_change(page_key: str):
    """
    Callback function for when the user selects a new year.
    Updates the selected year in session state and refreshes the data.
    """
    handle_change(page_key, "selected_year", update_full_data)

def handle_format_change(page_key: str):
    """
    Callback function for when the user selects a new format.
    Updates the selected scoring format in session state and refreshes the data.
    """
    handle_change(page_key, "selected_scoring_format", update_full_data)


def handle_week_change(page_key: str):
    """
    Callback function for when the user selects a new format.
    Updates the selected scoring format in session state and refreshes the data.
    """
    handle_change(page_key, "selected_weeks", update_player_tables)

def handle_player_change(page_key: str,
                         player_index:int=0):
    """
    Callback function for when the user selects a new format.
    Updates the selected scoring format in session state and refreshes the data.
    """
    state = getattr(st.session_state, page_key)
    new_player = st.session_state[f"selected_player_{player_index}"]

    if new_player != state["players"][player_index]['name']:  # Only update if the year actually changes
        state["players"][player_index]['name'] = new_player
        state["players"][player_index]['position'] = state["full_data"].query(
            "player_display_name == @new_player"
        )["position"].iloc[0] # update player position
        setattr(st.session_state, page_key, state)
        update_player_tables(page_key)  # Reload data and update tables

