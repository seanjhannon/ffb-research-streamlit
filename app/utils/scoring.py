import pandas as pd

class ScoringFormat:
    """Stores a set of scoring rules with flexibility for custom formats."""

    DEFAULT_VALUES = {
        "pass_yards_value": 0.04,
        "pass_tds_value": 4,
        "pass_ints_value": -2,
        "rush_yards_value": 0.1,
        "rush_tds_value": 6,
        "receptions_value": 0,  # 1 for PPR
        "rec_yards_value": 0.1,
        "rec_tds_value": 6,
        "two_point_conversions_value": 2,
        "fumble_recovery_td_value": 6,
        "fumble_lost_value": -2
    }

    def __init__(self, name: str, **kwargs):
        """
        Initializes a ScoringFormat with a name and user-defined values.
        Any missing values will default to standard scoring values.
        """
        self.name = name
        self.values = {**self.DEFAULT_VALUES, **kwargs}  # Merge defaults with user input

    def __repr__(self):
        return f"ScoringFormat(name={self.name}, values={self.values})"

    def to_markdown(self):
        """
        Returns a markdown-friendly string representation of the scoring format.
        """
        markdown_str = f"**Scoring Format: {self.name}**\n\n"
        for key, value in self.values.items():
            readable_key = key.replace("_value", "").replace("_", " ").title()
            markdown_str += f"**{readable_key}**: {value} pts\n\n"
        return markdown_str

    def validate(self):
        """
        Ensures all required fields are present in the scoring format.
        """
        missing_keys = [key for key in self.DEFAULT_VALUES if key not in self.values]
        if missing_keys:
            raise ValueError(f"Missing scoring fields: {missing_keys}")

    def get_value(self, key: str):
        """
        Retrieves the value for a given scoring attribute, ensuring the key exists.
        """
        return self.values.get(key, 0)


# **Predefined Scoring Formats**
class StandardScoringFormat(ScoringFormat):
    """Standard scoring format with default values."""
    def __init__(self):
        super().__init__(name="Standard")


class PPRScoringFormat(ScoringFormat):
    """PPR scoring format with default values (adds points per reception)."""
    def __init__(self):
        super().__init__(name="PPR", receptions_value=1)

# **Custom Scoring Format Example**
def create_custom_scoring_format(name: str, custom_values: dict) -> ScoringFormat:
    """
    Creates a custom scoring format, ensuring all necessary fields are included.
    """
    scoring_format = ScoringFormat(name, **custom_values)
    scoring_format.validate()  # Ensure all required keys are present
    return scoring_format



# Dict of {column_name: attr_name} for use with the nfl-data-py library
stat_mapping_nfl_py = {
    # PASSING
    'passing_yards': 'pass_yards_value',
    'passing_tds': 'pass_tds_value',
    'interceptions': 'pass_ints_value',
    # RUSHING
    'rushing_yards': 'rush_yards_value',
    'rushing_tds': 'rush_tds_value',
    # RECEIVING
    'receptions': 'receptions_value',
    'receiving_yards': 'rec_yards_value',
    'receiving_tds': 'rec_tds_value',
    # MISC
    'sack_fumbles_lost': 'fumble_lost_value',  # This data source distinguishes between different kinds of fumbles
    'rushing_fumbles_lost': 'fumble_lost_value',
    'receiving_fumbles_lost': 'fumble_lost_value',
    'passing_2pt_conversions': 'two_point_conversions_value',  # Same for 2pt conversions
    'rushing_2pt_conversions': 'two_point_conversions_value',
    'receiving_2pt_conversions': 'two_point_conversions_value',
}



def calculate_total_stats(stats_df: pd.DataFrame) -> pd.DataFrame:

    # Select numeric columns
    numeric_df = stats_df.select_dtypes(include='number')
    numeric_df['player_display_name'] = stats_df['player_display_name']

    grouped = numeric_df.groupby('player_display_name',as_index=False).sum()

    return grouped

def calculate_avg_stats(stats_df: pd.DataFrame) -> pd.DataFrame:

    # Select numeric columns
    numeric_df = stats_df.select_dtypes(include='number')
    numeric_df['player_display_name'] = stats_df['player_display_name']

    grouped = numeric_df.groupby('player_display_name',as_index=False).mean()

    return grouped


def calculate_fantasy_points(stats_row: pd.Series, scoring_format: ScoringFormat, stat_mapping: dict, debug=False) -> float:
    """Calculates the total fantasy points for a given player's stat row using the provided scoring format."""
    total_points = 0.0
    for column, scoring_attribute in stat_mapping.items():
        if column in stats_row:
            stat_value = stats_row[column]
            score_value = scoring_format.get_value(scoring_attribute)
            total_points += stat_value * score_value
            if debug:
                print(f"{column}: {stat_value}, {scoring_attribute}: {score_value}")

    return round(total_points, 2)


def calculate_fantasy_points_vec(df: pd.DataFrame, scoring_format: ScoringFormat, stat_mapping: dict,
                             debug=False) -> pd.DataFrame:
    """Calculates and adds a 'fantasy_points' column to the DataFrame based on the provided scoring format."""
    # Create a series for scoring values based on the stat_mapping
    score_values = {column: scoring_format.get_value(scoring_attribute) for column, scoring_attribute in
                    stat_mapping.items()}

    # Calculate fantasy points using vectorized operations
    fantasy_points = sum(df[column] * score_values[column] for column in stat_mapping if column in df)

    if debug:
        for column, scoring_attribute in stat_mapping.items():
            if column in df:
                print(f"{column}: {df[column].head()}, {scoring_attribute}: {score_values[column]}")

    # Add the calculated fantasy points as a new column
    df['fantasy_points'] = fantasy_points.round(2)
    return df


def calculate_fantasy_points_by_category(
        stats_df: pd.DataFrame,
        scoring_format: ScoringFormat,
        stat_mapping: dict) -> pd.Series:
    """Calculates the total points scored across all players for each category, returning a Series with summed points per category."""

    # Initialize a dictionary to hold the points values for each category
    total_points_by_category = {}

    # Loop through stat_mapping and calculate the total points for each category
    for column, scoring_attribute in stat_mapping.items():
        if column in stats_df.columns:
            # Multiply the relevant column by the scoring format value and sum the result
            total_points_by_category[scoring_attribute] = (
                        stats_df[column] * scoring_format.get_value(scoring_attribute)).sum()

    # Create a cleaner output with readable category names
    readable_category_names = {
        'pass_yards_value': 'Passing Yards',
        'pass_tds_value': 'Passing TDs',
        'pass_ints_value': 'Passing INTs',
        'rush_yards_value': 'Rushing Yards',
        'rush_tds_value': 'Rushing TDs',
        'receptions_value': 'Receptions',
        'rec_yards_value': 'Receiving Yards',
        'rec_tds_value': 'Receiving TDs',
        'two_point_conversions_value': 'Two-Point Conversions',
        'fumble_recovery_td_value': 'Fumble Recovery TDs',
        'fumble_lost_value': 'Fumbles Lost'
    }

    # Map the points categories to more readable names
    readable_total_points_by_category = {
        readable_category_names.get(key, key): value
        for key, value in total_points_by_category.items()
    }

    # Convert to pandas Series for better readability
    total_points_series = pd.Series(readable_total_points_by_category)

    return total_points_series



def make_position_ranks(totals_df):
    # Rank each stat column among athletes
    ranked_df = totals_df.copy()
    for column in totals_df.columns:
        if column != 'player_display_name':  # Assuming there's a column 'athlete' for athlete names
            ranked_df[column] = totals_df[column].rank(ascending=False, method='dense')
    return ranked_df