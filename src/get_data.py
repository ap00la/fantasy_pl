#%% Imports
import requests
import json
import asyncio
import json
import aiohttp
from understat import Understat
import httpx
from tools import timer


#%% Get data function

@timer
def get_data(url="https://fantasy.premierleague.com/api/bootstrap-static/", save_to_file=True):
    """ 
    Retrieve the player data from FPL boostrap static
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Response was code " + str(response.status_code))
    
    players = response.json()['elements']
    players = {player.pop('id'):player for player in players}

    if save_to_file:
        with open('.data/player_data.json', 'w') as outf:
            json.dump(players, outf)

    return players


#%% Get player hist

@timer
async def get_player_hist(player_ids, url='https://fantasy.premierleague.com/api/element-summary/', save_to_file=True):
    ''''
    Retrive fixtures, season so far data, and historical data 
    '''
    [TypeError("Player ID's must be ints") for id in player_ids if not isinstance(id, int)]          

    async with httpx.AsyncClient() as client:
        tasks = (client.get(url + str(player_id) + '/') for player_id in player_ids)
        responses = await asyncio.gather(*tasks)

    # dict of dicts with player ID as key
    data = {int((str(response.url)).split('/')[-2]):response.json() for response in responses}

    if save_to_file:
        with open('.data/history.json', 'w') as outf:
            json.dump(data, outf)

    return data


#%% understat data

@timer
async def get_understat(induvidual_stats=True, save_to_file=True):
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        players = await understat.get_league_players('epl', 2021)

        if induvidual_stats:
            for player in players:
                with open('.data/player_data/'+player['player_name']+'.json', 'w') as player_data:
                    json.dump(player, player_data)

        if save_to_file:    
            with open('.data/raw_understats.json', 'w') as outf:
                json.dump(players, outf)
        
    return players


#%% main()
@timer
def main():
    # Returns player data by player ID
    data = get_data()

    # Asynchrinous data I/O for understat and player hist
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_understat(induvidual_stats = True))
    loop.run_until_complete(get_player_hist(player_ids = data.keys()))


#%% If name main
if __name__ == '__main__':
    main()

