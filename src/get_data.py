#%% Imports
import requests
import json
import time
import asyncio
import json
import aiohttp
from understat import Understat
import httpx


#%% Get data function

def get_data(url="https://fantasy.premierleague.com/api/bootstrap-static/"):
    """ 
    Retrieve the player data from FPL boostrap static
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Response was code " + str(response.status_code))
    return json.loads(response.text)


#%% Get player hist

async def get_player_hist(player_ids, url='https://fantasy.premierleague.com/api/element-summary/', save_to_file=True):
    ''''
    Retrive fixtures, season so far data, and historical data 
    '''

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

def get_understat(induvidual_stats=False):
    '''
    Understat data getter
    '''

    async def understat_getter(induvidual_stats):
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            players = await understat.get_league_players('epl', 2021)
            
            if induvidual_stats:
                for player in players:
                    with open('../.data/player_data/'+player['player_name']+'.json', 'w') as player_data:
                        json.dump(player, player_data)
                
            with open('../.data/raw_understats.json', 'w') as outf:
                json.dump(players, outf)

    # Running the getters
    loop = asyncio.get_event_loop()
    loop.run_until_complete(understat_getter(induvidual_stats))



#%% main()

def main():
    data = get_data()
    print(type(data))
    # print(x)
    get_understat(induvidual_stats=True)

#%% If name main
if __name__ == '__main__':
    main()

