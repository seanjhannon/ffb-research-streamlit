def get_position_kpis(position:str):

    if position in ['WR', 'TE']:
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