#%% Imports
import json
import copy
import pandas as pd
from fuzzywuzzy import fuzz
from tools import timer
from preferences import columns_to_drop, understat_columns_to_drop, players_to_rename


#%% Get data function

@timer
def load_data():
    with open(".data/player_data.json", "r") as file:
        player_data = json.load(file)

    with open(".data/history.json", "r") as file:
        player_history = json.load(file)

    with open(".data/raw_understats.json", "r") as file:
        understat = json.load(file)

    return player_data, player_history, understat


#%% Process raw fpl data

@timer
def process_raw_fpl(player_data, columns_to_drop=columns_to_drop):
    player_data = pd.DataFrame.from_dict(player_data, orient='index').drop(columns=columns_to_drop)
    player_with_mins = player_data[player_data.minutes> 0]

    # Get names used for fuzzy matching
    full_names = player_with_mins[['first_name', 'second_name']].agg(' '.join, axis=1)
    web_names = player_with_mins['web_name']
    names =pd.concat([full_names, web_names], axis=1).rename({0:'player_name', 'web_name':'short_name'}, axis='columns')

    return player_with_mins.join(names['player_name']).drop(columns=['first_name','second_name','web_name']), names


#%% Proces understat data

@timer
def process_raw_understat(understat, understat_columns_to_drop=understat_columns_to_drop, 
                          players_to_rename=players_to_rename):
    
    # Move from dict object and drop unessesary columns
    understat = pd.DataFrame.from_dict(understat).drop(columns = understat_columns_to_drop)

    # Rename required players
    understat['player_name'] = understat['player_name'].replace(players_to_rename)

    return understat


#%% Matching names

@timer
def match_names(fpl_names, understat_names, save_to_file=True):

    # Copy the files ensuring they are not altered
    understat_names = list(copy.deepcopy(understat_names))
    fpl_names = copy.deepcopy(fpl_names)
    conf_score = 100
    best_match = {}
    confidence = {}
    while True:

        for understat_player in understat_names:
            if len(understat_player.split()) > 1 and conf_score > 70:
                # Players with multiple names
                ratings = {fuzz.partial_ratio(understat_player, player[1][0]):player[1][0] for player in fpl_names.iterrows()}
            else:

                # Player with one name
                # direct match tried as well as a fuzzy match. Direct match given confidence score of 150
                ratings = {150 if understat_player == player[1][1] else fuzz.partial_ratio(understat_player, player[1][1]):player[1][0] for player in fpl_names.iterrows()}
            
            if max(ratings) >= conf_score:
                best_match[understat_player] = ratings[max(ratings)]
                confidence[understat_player] = max(ratings)
                understat_names.remove(understat_player)
                fpl_names.drop(fpl_names.index[fpl_names['player_name'] == ratings[max(ratings)]], inplace=True)

        conf_score -= 2
        if not len(understat_names):
            break
    

    if save_to_file:
        with open('.data/player_matching.json', 'w') as outf:
            json.dump([best_match,confidence], outf)

    return best_match

#%% Change names

@timer
def change_names(understat_names, best_match, column_name='player_name'):
    understat_names[column_name] = understat_names[column_name].replace(best_match)
    return understat_names


#%% Run merge

def merge(fpl_players, understat_players, column_name='player_name'):
    return pd.merge(fpl_players.reset_index(), understat_players, how ='inner', on=[column_name, column_name])

#%% main()
@timer
def main():
    player_data, _, understat_data = load_data()
  
    player_data, names = process_raw_fpl(player_data)
    understat_data = process_raw_understat(understat_data)
    
    matches = match_names(names, understat_data)
    understat_data = change_names(understat_data, matches)
    
    data = merge(player_data, understat_data)
    # Returns player data by player ID

    with open('.data/joined_data.json','w') as file:
        json.dump(data.to_dict('records'), file)
 

#%% If name main
if __name__ == '__main__':
    main()