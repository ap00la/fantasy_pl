#%% Imports
import json
import copy
import numpy as np
import pandas as pd
import asyncio
import logging
from fuzzywuzzy import fuzz
from tools import timer
from preferences import columns_to_drop, understat_columns_to_drop, players_to_rename
from get_data import get_data, get_player_hist, get_understat

logger = logging.basicConfig(format='[%(levelname)s %(module)s] %(asctime)s - %(message)s', level = logging.INFO)
logger = logging.getLogger(__name__)

#%% Get data function

@timer
def load_data():
    logger.info('Loading data.')
    try:
        filename = ".data/player_data.json"
        with open(filename, "r") as file:
            player_data = json.load(file)
    except FileNotFoundError:
        logger.info(f"{filename} not found.")
        player_data = get_data(save_to_file=False)

    try:
        filename = ".data/history.json"
        with open(filename, "r") as file:
            player_history = json.load(file)
    except FileNotFoundError:
        logger.info(f"{filename} not found.")
        loop = asyncio.get_event_loop()
        player_history = loop.run_until_complete(get_player_hist(player_ids = player_data.keys()))

    try:
        filename = ".data/raw_understats.json"
        with open(filename, "r") as file:
            understat = json.load(file)
    except FileNotFoundError:
            logger.info(f"{filename} not found.")
            loop = asyncio.get_event_loop()
            understat = loop.run_until_complete(get_understat(induvidual_stats = True))
    
    return player_data, player_history, understat


#%% Process raw fpl data

@timer
def process_raw_fpl(player_data, columns_to_drop=columns_to_drop):
    logger.info("Processing raw fpl player data.")
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
    
    logger.info("Processing raw understat data.")
    # Move from dict object and drop unessesary columns
    understat = pd.DataFrame.from_dict(understat).drop(columns = understat_columns_to_drop)

    # Rename required players
    understat['player_name'] = understat['player_name'].replace(players_to_rename)

    return understat


#%% Matching names

@timer
def match_names(fpl_names, understat_names, save_to_file=True):

    logger.info("Matching player names for fpl and understat data")
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
    
    logger.info(f"{len(best_match)} players matched with a mean confidence score of {np.mean(list(confidence.values())):.2f}.")
    logger.info(f"The least confident match has a confidence of {np.min(list(confidence.values()))}.")

    if save_to_file:
        logger.info(f"Saving matched and confidence scored to file.")
        with open('.data/player_matching.json', 'w') as outf:
            json.dump([best_match,confidence], outf)

    return best_match

#%% Change names

@timer
def change_names(understat_names, best_match, column_name='player_name'):
    logger.info("Changing names to match fpl data.")
    understat_names[column_name] = understat_names[column_name].replace(best_match)
    return understat_names


#%% Run merge

def merge(fpl_players, understat_players, column_name='player_name'):
    logger.info("Merging datasets")
    return pd.merge(fpl_players.reset_index(), understat_players, how ='inner', on=[column_name, column_name])

#%% main()
@timer
def main():
    player_data, _, understat_data = load_data()
 
    player_data, names = process_raw_fpl(player_data)
    understat_data = process_raw_understat(understat_data)
    
    matches = match_names(names, understat_data['player_name'])
    understat_data = change_names(understat_data, matches)
    
    data = merge(player_data, understat_data)
    # Returns player data by player ID

    with open('.data/joined_data.json','w') as file:
        logger.info(f"Saving joined data to file.")
        json.dump(data.to_dict('records'), file)
 

#%% If name main
if __name__ == '__main__':
    main()