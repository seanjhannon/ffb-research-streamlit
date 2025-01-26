import pandas as pd


class ScoringFormat:
    """Stores a set of scoring rules."""

    def __init__(self,
                 pass_yards_value: float,
                 pass_tds_value: int,
                 pass_ints_value: int,
                 rush_yards_value: float,
                 rush_tds_value: int,
                 receptions_value: float,
                 rec_yards_value: float,
                 rec_tds_value: int,
                 two_point_conversions_value: int,
                 fumble_recovery_td_value: int,
                 fumble_lost_value: int,
                 name: str):
        self.pass_yards_value = pass_yards_value
        self.pass_tds_value = pass_tds_value
        self.pass_ints_value = pass_ints_value
        self.rush_yards_value = rush_yards_value
        self.rush_tds_value = rush_tds_value
        self.receptions_value = receptions_value
        self.rec_yards_value = rec_yards_value
        self.rec_tds_value = rec_tds_value
        self.two_point_conversions_value = two_point_conversions_value
        self.fumble_recovery_td_value = fumble_recovery_td_value
        self.fumble_lost_value = fumble_lost_value
        self.name = name

    def __repr__(self):
        return (
            f"ScoringFormat(name={self.name}, "
            f"pass_yards_value={self.pass_yards_value}, "
            f"pass_tds_value={self.pass_tds_value}, "
            f"pass_ints_value={self.pass_ints_value}, "
            f"rush_yards_value={self.rush_yards_value}, "
            f"rush_tds_value={self.rush_tds_value}, "
            f"receptions_value={self.receptions_value}, "
            f"rec_yards_value={self.rec_yards_value}, "
            f"rec_tds_value={self.rec_tds_value}, "
            f"two_point_conversions_value={self.two_point_conversions_value}, "
            f"fumble_recovery_td_value={self.fumble_recovery_td_value}, "
            f"fumble_lost_value={self.fumble_lost_value})"
        )

    def to_markdown(self):
        return (
            f"**Scoring Format: {self.name}**\n\n"
            f"**Passing Yards**: {self.pass_yards_value} pts per yard\n\n"
            f"**Passing TDs**: {self.pass_tds_value} pts each\n\n"
            f"**Passing INTs**: {self.pass_ints_value} pts each\n\n"
            f"**Rushing Yards**: {self.rush_yards_value} pts per yard\n\n"
            f"**Rushing TDs**: {self.rush_tds_value} pts each\n\n"
            f"**Receptions**: {self.receptions_value} pts each\n\n"
            f"**Receiving Yards**: {self.rec_yards_value} pts per yard\n\n"
            f"**Receiving TDs**: {self.rec_tds_value} pts each\n\n"
            f"**Two-Point Conversions**: {self.two_point_conversions_value} pts each\n\n"
            f"**Fumble Recovery TDs**: {self.fumble_recovery_td_value} pts each\n\n"
            f"**Fumbles Lost**: {self.fumble_lost_value} pts each\n"
        )

class StandardScoringFormat(ScoringFormat):
    """Standard scoring format with default values."""

    def __init__(self):
        super().__init__(
            pass_yards_value=0.04,
            pass_tds_value=4,
            pass_ints_value=-2,
            rush_yards_value=0.1,
            rush_tds_value=6,
            receptions_value=0,
            rec_yards_value=0.1,
            rec_tds_value=6,
            two_point_conversions_value=2,
            fumble_recovery_td_value=6,
            fumble_lost_value=-2,
            name="Standard"
        )


class PPRScoringFormat(ScoringFormat):
    """PPR scoring format with default values."""

    def __init__(self):
        super().__init__(
            pass_yards_value=0.04,
            pass_tds_value=4,
            pass_ints_value=-2,
            rush_yards_value=0.1,
            rush_tds_value=6,
            receptions_value=1,
            rec_yards_value=0.1,
            rec_tds_value=6,
            two_point_conversions_value=2,
            fumble_recovery_td_value=6,
            fumble_lost_value=-2,
            name="PPR"
        )


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

    # Compute the total for each numeric column
    totals = numeric_df.sum()

    # Rename the columns to include the 'total_' prefix
    totals.index = ['total_' + col for col in totals.index]

    # Convert the Series back into a DataFrame with one row
    result_df = totals.to_frame().T

    return result_df

def calculate_fantasy_points(
        stats_row: pd.Series,
        scoring_format: ScoringFormat,
        stat_mapping: dict,
        debug=False) -> float:
    """Calculates the total points scored by one row of stats. """
    total_points = 0.0
    for column, scoring_attribute in stat_mapping.items():
        if column in stats_row and hasattr(scoring_format, scoring_attribute):
            total_points += stats_row[column] * getattr(scoring_format, scoring_attribute)
            if debug:
                print(
                    f"{column} : {stats_row[column]}, {scoring_attribute} : {getattr(scoring_format, scoring_attribute)}")
    return total_points


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
                        stats_df[column] * getattr(scoring_format, scoring_attribute)).sum()

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
