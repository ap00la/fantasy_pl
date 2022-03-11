#%% Imports
import json
import copy
import numpy as np
import pandas as pd
import asyncio
import datetime
import logging
from fuzzywuzzy import fuzz
from tools import timer
from preferences import columns_to_drop, understat_columns_to_drop, players_to_rename
from get_data import get_data, get_player_hist, get_understat

logger = logging.basicConfig(format='[%(levelname)s %(module)s] %(asctime)s - %(message)s', level = logging.INFO)
logger = logging.getLogger(__name__)
today = '_'.join(str(datetime.datetime.today()).split(' ')[0].split('-'))
#%% Get data function

@timer
def load_data():
    logger.info('Loading data.')
    logger.info(f"Looking for files starting {today}")
    try:
        filename = ".data/" + today + "_player_data.json"
        with open(filename, "r") as file:
            player_data = json.load(file)
    except FileNotFoundError:
        logger.info(f"{filename} not found.")
        player_data = get_data()

    try:
        filename = ".data/" + today + "_history.json"
        with open(filename, "r") as file:
            player_history = json.load(file)
    except FileNotFoundError:
        logger.info(f"{filename} not found.")
        loop = asyncio.get_event_loop()
        player_history = loop.run_until_complete(get_player_hist(player_ids = player_data.keys()))

    try:
        filename = ".data/" + today + "_raw_understats.json"
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
    '''
    Finds the best match
    '''

    try:
        logger.info("Searching for a current best match file")
        filename = ".data/" + today + "_player_matching.json"
        with open(filename, "r") as file:
            best_match =  json.load(file)
        logger.info("File found, matching will be skipped.")
        return best_match

    except FileNotFoundError:
        logger.info("File not found. Matching will begin")
    
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
        with open('.data/' + today + '_player_matching.json', 'w') as outf:
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

#%% Prune data
@timer
def type_converter(df):
    '''
    Convert columns to numeric
    '''
    logger.info("Converting Dataframe columns to numeric.")
    for column in df.columns:
        if column not in ['element_type','in_dreamteam','player_name','index']:
            df[column] = pd.to_numeric(df[column])
    return df


@timer
def prune_data(df, min_minutes=90, remove_injured=False):
    #Drop players with less than 90 minutes
    logger.info(f"Dropping players who have plaved less than {min_minutes} this season.")
    df = df[df['minutes'] >= min_minutes]

    # Find players with Null chance of playing
    logger.info("Finding player with Null chance of playing.")
    df_left = df[df['chance_of_playing_next_round'] == df['chance_of_playing_next_round'].isna()]

    # Of the players who are null chance of playing find the injuries and remove them from rows to drop
    injuries = []
    if not remove_injured:
        logger.info("Keeping players with an expected return date.")
        for player in df_left.iterrows():
            if ('injury' in player[1]['news'].lower() or 'suspended' in player[1]['news'].lower()) and 'unknown ' not in player[1]['news'].lower():
                injuries.append(player[0])

    # drop the players who are not injured or suspended eg. have left the club...
    df = df.drop(index= df_left.drop(index=injuries).index,
                columns=['chance_of_playing_next_round', 'chance_of_playing_this_round','news', 'news_added','status',
                        'corners_and_indirect_freekicks_order', 'direct_freekicks_order', 'penalties_order'])

    df['element_type'] = df['element_type'].map({1:'Goalkeeper',2:'Defender',3:'Midfielder',4:'Forward'})

    
    df = type_converter(df)
    #
    logger.info("Returning dataframe.")
    return df


#%% Process GW data
def process_gw_data(df, hist_data):
    '''
    This function processes gameweek by gameweek data for each of the players in the main dataframe.
    The output is a large dataframe containing the week by week statistics for each player.

    '''
    detailed_df = pd.DataFrame()
    df = df.set_index('index')

    for id in df.index:

        history = pd.DataFrame(hist_data[id]['history'])

        # Goals for and against
        history['goals_for'] = history['team_h_score'].where(history['was_home'], history['team_a_score'])
        history['goals_against'] = history['team_a_score'].where(history['was_home'], history['team_h_score'])

        # Drop irrelevant columns
        history = history.drop(columns=['team_h_score','team_a_score','element','fixture','kickoff_time','opponent_team'])

        # groupBY sum gameweeks
        mean_cols =['value', 'transfers_balance', 'selected', 'transfers_in','transfers_out']
        history = pd.concat([history.groupby('round').sum().drop(columns=mean_cols), history.groupby('round')[mean_cols].mean()], axis=1)

        # Finding empty gameweeks
        for empty_gw in np.arange(1,max(history.index)):
            if empty_gw not in history.index:
                history.loc[empty_gw] = None
        history = history.sort_index()

        # filling interpolated transfer data or zeros for gw data
        history[['value', 'transfers_balance', 'selected','transfers_in', 'transfers_out']] = \
            history[['value', 'transfers_balance', 'selected', 'transfers_in', 'transfers_out']].interpolate(method='linear')
        history = history.fillna(0)

        # Adding a cumulative sum of points
        history['points_cumsum'] = history['total_points'].cumsum()

        # Adding player ID to df
        history['id'] = id

        # Adding general player data 
        player_df = pd.merge(history, df[['team', 'element_type', 'player_name']], left_on='id', right_index=True,)

        detailed_df = pd.concat([detailed_df, player_df], axis=0)

    return detailed_df


#%% Create slices for machine learning
# this function is not called in main but is called in the ML notebook

def create_ml_df(gw_df, weeks=3):
    '''
    This function uses the gameweek dataframe to create data points for the machine learning notebook.
    The data is slices up into chunks and then flattened out into a singular data point before being compiled back into a df for ML.

    '''
    gw = max(gw_df.index)
    slices = [np.arange(i-(weeks-1),i+1) for i in range(weeks, gw)]
    logger.info(f"{len(slices)} slices for each player will be made up to gameweek {gw}")
    logger.info(f"There are {len(gw_df['id'].unique())} players in the dataframe")
    logger.info(f"There will be {len(gw_df['id'].unique())*len(slices)} datapoints in returned dataframe.")

    df = pd.DataFrame()
    logger.info("Slicing data")
    for id in gw_df['id'].unique(): # [7, 413]:
        player_df = gw_df[gw_df['id'] == id]

        for slice in slices:
            df_slice = player_df.loc[slice,:].iloc[::-1].reset_index(drop=True)
            
            unstacked = df_slice.drop(columns=['element_type', 'player_name', 'team', 'id']).unstack().to_frame().T
            unstacked.columns = unstacked.columns.map(lambda x: x[0] + '_' + str(1+x[1])+'_weeks_ago')

            unstacked['target'] = player_df.loc[max(slice)+1,:]['total_points']
            unstacked['player_name'] = player_df.loc[1,'player_name']
            unstacked['id'] = player_df.loc[1,'id']
            unstacked['team'] = player_df.loc[1,'team']
            unstacked['element_type'] = player_df.loc[1,'element_type']
            df = pd.concat([df, unstacked], axis=0)
            
    return df.reset_index(drop=True)


#%% main()
@timer
def main(save_to_file=True, min_minutes=90, remove_injured=False):
    '''
    Main function that loads data if it needs to be loaded.

    It then processes and matches understat and FPL data.

    Data it then filtered and pruned.

    Historical gameweek data is then processed to provide further insight.
    '''
    # Load the data.
    # Download the data if it is not present
    logger.info(f"Loading data.")
    player_data, hist_data, understat_data = load_data()
    
    # Process the raw fpl and understat data
    logger.info(f"Processing data.")
    player_data, names = process_raw_fpl(player_data)
    understat_data = process_raw_understat(understat_data)
    
    # Match the names using fuzzy logic
    logger.info(f"Matching data using fuzzy logic.")
    matches = match_names(names, understat_data['player_name'])
    understat_data = change_names(understat_data, matches)
    
    # Merge the dataframes
    logger.info(f"Merging data sources.")
    data = merge(player_data, understat_data)

    # Dataframe is pruned to ensure only active players are in the DF
    logger.info(f"Pruning merged data.")
    data = prune_data(data, min_minutes, remove_injured)

    # Process gameweek data
    logger.info(f"Processing gameweek data.")
    gw_data = process_gw_data(data, hist_data)
  
    # Save files
    if save_to_file:
        filename = ".data/" + today + "_joined_data.json"
    
        with open(filename,'w') as file:
            logger.info(f"Saving joined data to file - {filename}.")
            json.dump(data.to_dict('records'), file)

        filename = ".data/" + today + "_gw_data.json"
        with open(filename,'w') as file:
            logger.info(f"Saving gameweek data to file - {filename}.")
            json.dump(gw_data.to_dict('records'), file)

        data.set_index('index').to_pickle(".data/" + today + "_df")
        gw_data.to_pickle(".data/" + today + "_gw_df")

    # Returns player data by player ID
    return data.set_index('index'), gw_data


#%% If name main
if __name__ == '__main__':
    main()