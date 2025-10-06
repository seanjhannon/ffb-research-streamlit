"""
XFP Model Deployment Module
Lightweight module for loading and using the expected fantasy points model in production.
"""

import pickle
import pandas as pd
import numpy as np
import os
from typing import Union, Dict, Any


class XFPCalculator:
    """Main class for calculating expected fantasy points."""
    
    def __init__(self, model_path: str = None):
        """
        Initialize the XFP calculator.
        
        Args:
            model_path: Path to the pickled model file. If None, uses default path.
        """
        if model_path is None:
            # Default to the model in the same directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, 'xfp_model.pkl')
        
        self.model_path = model_path
        self.model = None
        self.model_info = None
        self._load_model()
    
    def _load_model(self):
        """Load the pickled model and extract metadata."""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # Handle the actual structure from the pickle file
            if isinstance(model_data, dict) and 'expected_outcomes' in model_data:
                # This is the lookup-based model structure
                self.model = model_data
                self.model_info = {
                    'training_years': model_data.get('training_info', {}).get('years', '2015-2024'),
                    'total_plays': model_data.get('training_info', {}).get('total_plays', '483,605'),
                    'context_groups': len(model_data.get('expected_outcomes', {})),
                    'correlation': '0.966+',
                    'model_type': 'lookup_based'
                }
            elif isinstance(model_data, dict):
                # Expected structure with model and metadata
                self.model = model_data.get('model')
                self.model_info = model_data.get('model_info', {})
            else:
                # Direct model object
                self.model = model_data
                self.model_info = {
                    'training_years': '2015-2024',
                    'total_plays': '483,605',
                    'context_groups': '34,940',
                    'correlation': '0.966+'
                }
            
            if self.model is None:
                raise ValueError("Model not found in pickle file")
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Model file not found at {self.model_path}")
        except Exception as e:
            raise RuntimeError(f"Error loading model: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            'status': 'loaded' if self.model is not None else 'error',
            'model_path': self.model_path,
            'training_years': self.model_info.get('training_years', 'Unknown'),
            'total_plays': self.model_info.get('total_plays', 'Unknown'),
            'context_groups': self.model_info.get('context_groups', 'Unknown'),
            'correlation': self.model_info.get('correlation', 'Unknown')
        }
    
    def get_available_scoring_formats(self) -> list:
        """Get list of available scoring formats."""
        return ['standard', 'ppr', 'half_ppr']
    
    def calculate_play_xfp(self, play_row: Union[pd.Series, Dict], scoring_format: str = 'ppr') -> float:
        """
        Calculate expected fantasy points for a single play using lookup-based model.
        
        Args:
            play_row: Play data as pandas Series or dict
            scoring_format: 'standard', 'ppr', or 'half_ppr'
            
        Returns:
            Expected fantasy points for the play
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        if scoring_format not in self.get_available_scoring_formats():
            raise ValueError(f"Invalid scoring format: {scoring_format}")
        
        try:
            # Convert to pandas Series if needed
            if isinstance(play_row, dict):
                play_row = pd.Series(play_row)
            
            # Determine opportunity type and create context key
            opportunity_type = self._determine_opportunity_type(play_row)
            context_key = self._create_context_key(play_row, opportunity_type)
            
            # Look up expected outcome
            expected_outcomes = self.model.get('expected_outcomes', {})
            opportunity_data = expected_outcomes.get(opportunity_type, {})
            
            if context_key in opportunity_data:
                outcome = opportunity_data[context_key]
                expected_fp = self._calculate_expected_fp_from_outcome(outcome, scoring_format)
                return round(expected_fp, 2)
            else:
                # Fallback: use simple heuristic if context not found
                return self._fallback_xfp_calculation(play_row, opportunity_type, scoring_format)
            
        except Exception as e:
            print(f"Error calculating XFP for play: {str(e)}")
            return 0.0
    
    def _determine_opportunity_type(self, play_row: pd.Series) -> str:
        """Determine the type of opportunity for a play."""
        if play_row.get('rush_attempt', 0):
            return 'rush'
        elif play_row.get('target', play_row.get('pass_target', 0)):
            return 'target'
        elif play_row.get('pass_attempt', 0):
            return 'pass'
        elif play_row.get('scramble', 0):
            return 'scramble'
        else:
            return 'rush'  # Default fallback
    
    def _create_context_key(self, play_row: pd.Series, opportunity_type: str) -> str:
        """Create context key for lookup based on play characteristics."""
        # Helper function to safely convert to int, handling NaN values
        def safe_int(value, default):
            if pd.isna(value):
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        
        yardline = safe_int(play_row.get('yardline_100', 50), 50)
        down = safe_int(play_row.get('down', 1), 1)
        ydstogo = safe_int(play_row.get('ydstogo', 10), 10)
        
        if opportunity_type == 'rush':
            # Format: rush_yardline_down_distance_direction_goal_to_go
            direction = play_row.get('run_location', 'middle')
            goal_to_go = safe_int(play_row.get('goal_to_go', 0), 0)
            return f"rush_{yardline}_{down}_{ydstogo}_{direction}_{goal_to_go}"
        
        elif opportunity_type == 'target':
            # Format: target_yardline_down_distance_direction_depth_goal_to_go
            direction = play_row.get('pass_location', 'middle')
            depth = play_row.get('pass_length', 'short')
            goal_to_go = safe_int(play_row.get('goal_to_go', 0), 0)
            return f"target_{yardline}_{down}_{ydstogo}_{direction}_{depth}_{goal_to_go}"
        
        elif opportunity_type == 'pass':
            # Format: pass_yardline_down_distance_direction_depth_goal_to_go
            direction = play_row.get('pass_location', 'middle')
            depth = play_row.get('pass_length', 'short')
            goal_to_go = safe_int(play_row.get('goal_to_go', 0), 0)
            return f"pass_{yardline}_{down}_{ydstogo}_{direction}_{depth}_{goal_to_go}"
        
        elif opportunity_type == 'scramble':
            # Format: scramble_yardline_down_distance_goal_to_go
            goal_to_go = safe_int(play_row.get('goal_to_go', 0), 0)
            return f"scramble_{yardline}_{down}_{ydstogo}_{goal_to_go}"
        
        else:
            return f"rush_{yardline}_{down}_{ydstogo}_middle_0"
    
    def _calculate_expected_fp_from_outcome(self, outcome, scoring_format: str) -> float:
        """Calculate expected fantasy points from an ExpectedOutcome object."""
        try:
            # Get base values from outcome
            yards = getattr(outcome, 'yards', 0)
            touchdown_prob = getattr(outcome, 'touchdown_prob', 0)
            fumble_prob = getattr(outcome, 'fumble_prob', 0)
            reception_prob = getattr(outcome, 'reception_prob', 0)
            
            # Calculate expected fantasy points
            expected_fp = 0.0
            
            # Yards (0.1 per yard for rush/rec, 0.04 for pass)
            expected_fp += yards * 0.1
            
            # Touchdowns (6 points)
            expected_fp += touchdown_prob * 6
            
            # Fumbles (-2 points)
            expected_fp += fumble_prob * -2
            
            # Receptions (based on scoring format)
            if scoring_format == 'ppr':
                expected_fp += reception_prob * 1.0
            elif scoring_format == 'half_ppr':
                expected_fp += reception_prob * 0.5
            
            return expected_fp
            
        except Exception as e:
            print(f"Error calculating FP from outcome: {str(e)}")
            return 0.0
    
    def _fallback_xfp_calculation(self, play_row: pd.Series, opportunity_type: str, scoring_format: str) -> float:
        """Fallback calculation when context key is not found."""
        # Simple heuristic-based calculation
        yardline = play_row.get('yardline_100', 50)
        down = play_row.get('down', 1)
        ydstogo = play_row.get('ydstogo', 10)
        
        # Base expected yards (simplified)
        if opportunity_type == 'rush':
            base_yards = 4.0
        elif opportunity_type == 'target':
            base_yards = 8.0
        elif opportunity_type == 'pass':
            base_yards = 6.0
        else:
            base_yards = 3.0
        
        # Adjust for field position and down
        if yardline < 20:  # Red zone
            base_yards *= 0.8
        elif yardline > 80:  # Own territory
            base_yards *= 1.2
        
        if down == 1:
            base_yards *= 1.1
        elif down == 3:
            base_yards *= 0.9
        
        # Calculate expected FP
        expected_fp = base_yards * 0.1  # Yards to points
        
        # Add reception points if applicable
        if opportunity_type == 'target':
            if scoring_format == 'ppr':
                expected_fp += 0.7  # ~70% catch rate
            elif scoring_format == 'half_ppr':
                expected_fp += 0.35
        
        return round(expected_fp, 2)
    
    
    def calculate_player_efficiency(self, player_data: pd.DataFrame, player_name: str, scoring_format: str = 'ppr') -> Dict[str, float]:
        """
        Calculate efficiency metrics for a player.
        
        Args:
            player_data: DataFrame of player's plays
            player_name: Name of the player
            scoring_format: Scoring format to use
            
        Returns:
            Dictionary with efficiency metrics
        """
        if player_data.empty:
            return {
                'expected_fp': 0.0,
                'actual_fp': 0.0,
                'efficiency': 0.0,
                'over_under': 0.0
            }
        
        # Calculate expected FP for all plays
        expected_fp_total = 0.0
        actual_fp_total = 0.0
        play_count = 0
        
        for _, play in player_data.iterrows():
            expected_fp = self.calculate_play_xfp(play, scoring_format)
            expected_fp_total += expected_fp
            
            # Calculate actual FP (you'll need to implement this based on your scoring system)
            try:
                actual_fp = self._calculate_actual_fp(play, scoring_format)
                actual_fp_total += actual_fp
                play_count += 1
            except Exception as e:
                print(f"Error calculating actual FP for play: {str(e)}")
                continue
        
        # Calculate efficiency metrics
        efficiency = actual_fp_total / expected_fp_total if expected_fp_total > 0 else 0.0
        over_under = actual_fp_total - expected_fp_total
        
        print(f"📊 XFP Calculation Summary:")
        print(f"  - Plays processed: {play_count}")
        print(f"  - Expected FP: {expected_fp_total:.2f}")
        print(f"  - Actual FP: {actual_fp_total:.2f}")
        print(f"  - Efficiency: {efficiency:.3f}")
        
        return {
            'expected_fp': round(expected_fp_total, 2),
            'actual_fp': round(actual_fp_total, 2),
            'efficiency': round(efficiency, 3),
            'over_under': round(over_under, 2)
        }
    
    def _calculate_actual_fp(self, play_row: pd.Series, scoring_format: str) -> float:
        """
        Calculate actual fantasy points for a play.
        This is a simplified implementation - you'll want to enhance this.
        
        Args:
            play_row: Play data
            scoring_format: Scoring format
            
        Returns:
            Actual fantasy points
        """
        fp = 0.0
        
        # Helper function to safely get numeric values, defaulting to 0 for NaN
        def safe_get(key, default=0):
            value = play_row.get(key, default)
            return 0 if pd.isna(value) else value
        
        # Rushing
        if safe_get('rush_attempt', 0):
            fp += safe_get('rushing_yards', 0) * 0.1
            fp += safe_get('rushing_tds', 0) * 6
            fp += safe_get('rushing_fumbles_lost', 0) * -2
        
        # Receiving - check for both 'target' and 'pass_target' columns
        target_flag = safe_get('target', safe_get('pass_target', 0))
        if target_flag:
            fp += safe_get('receiving_yards', 0) * 0.1
            fp += safe_get('receiving_tds', 0) * 6
            fp += safe_get('receiving_fumbles_lost', 0) * -2
            
            # Reception points
            if scoring_format == 'ppr':
                fp += safe_get('receptions', 0) * 1.0
            elif scoring_format == 'half_ppr':
                fp += safe_get('receptions', 0) * 0.5
        
        # Passing
        if safe_get('pass_attempt', 0):
            fp += safe_get('passing_yards', 0) * 0.04
            fp += safe_get('passing_tds', 0) * 4
            fp += safe_get('interceptions', 0) * -2
        
        return round(fp, 2)


def load_xfp_model(model_path: str = None) -> XFPCalculator:
    """
    Load the XFP model for use in Streamlit.
    
    Args:
        model_path: Path to the model file. If None, uses default path.
        
    Returns:
        XFPCalculator instance
    """
    return XFPCalculator(model_path)


# Convenience functions for Streamlit integration
def calculate_season_xfp(season_data: pd.DataFrame, scoring_format: str = 'ppr') -> pd.DataFrame:
    """
    Calculate XFP for entire season efficiently.
    
    Args:
        season_data: DataFrame of play-by-play data
        scoring_format: Scoring format to use
        
    Returns:
        DataFrame with XFP calculations added
    """
    xfp_calc = load_xfp_model()
    
    # Process all plays
    season_data['expected_fp'] = season_data.apply(
        lambda row: xfp_calc.calculate_play_xfp(row, scoring_format), 
        axis=1
    )
    
    # Calculate efficiency
    season_data['actual_fp'] = season_data.apply(
        lambda row: xfp_calc._calculate_actual_fp(row, scoring_format),
        axis=1
    )
    
    season_data['efficiency'] = season_data['actual_fp'] / season_data['expected_fp']
    season_data['efficiency'] = season_data['efficiency'].replace([np.inf, -np.inf], 0)
    
    return season_data


def get_player_xfp_breakdown(player_id: str, season_data: pd.DataFrame, scoring_format: str = 'ppr') -> pd.DataFrame:
    """
    Get detailed XFP breakdown for a player.
    
    Args:
        player_id: Player identifier
        season_data: DataFrame of play-by-play data
        scoring_format: Scoring format to use
        
    Returns:
        DataFrame with player's XFP breakdown
    """
    xfp_calc = load_xfp_model()
    
    # Filter player's plays
    player_plays = season_data[season_data['player_id'] == player_id].copy()
    
    if player_plays.empty:
        return pd.DataFrame()
    
    results = []
    for _, play in player_plays.iterrows():
        expected_fp = xfp_calc.calculate_play_xfp(play, scoring_format)
        actual_fp = xfp_calc._calculate_actual_fp(play, scoring_format)
        
        results.append({
            'play_id': play.get('play_id', ''),
            'expected_fp': expected_fp,
            'actual_fp': actual_fp,
            'efficiency': actual_fp / expected_fp if expected_fp > 0 else 0,
            'opportunity_type': _determine_opportunity_type(play),
            'context': f"{play.get('yardline_100', 50)} yd line, {play.get('down', 1)} & {play.get('ydstogo', 10)}"
        })
    
    return pd.DataFrame(results)


def _determine_opportunity_type(play_row: pd.Series) -> str:
    """Determine the type of opportunity for a play."""
    if play_row.get('rush_attempt', 0):
        return 'Rush'
    elif play_row.get('target', 0):
        return 'Target'
    elif play_row.get('pass_attempt', 0):
        return 'Pass'
    elif play_row.get('scramble', 0):
        return 'Scramble'
    else:
        return 'Other'
