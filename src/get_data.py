#%% Imports
import requests
import json
import time
import asyncio
import json
import aiohttp
from understat import Understat


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

def get_player_hist(i, url='https://fantasy.premierleague.com/api/element-summary/'):
    ''''
    Retrive fixtures, season so far data, and historical data 
    '''
    response = requests.get(url+str(i)+'/')
    if response.status_code != 200:
        raise Exception('Respone was code ' + str(response.status_code))
    return json.loads(response.text)



#%% Unistat data

async def unistat(ind_stats):
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        players = await understat.get_league_players(
            'epl', 2021
        )
        #name = [player['player_name'] for player in players]
        #print(name[:25])
        if ind_stats:
            for player in players:
                with open('../.data/player_data/'+player['player_name']+'.json', 'w') as player_data:
                    json.dump(player, player_data)
            
        with open('../.data/raw_unistats.json', 'w') as outf:
            json.dump(players, outf)


def get_unistat(ind_stats=False):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(unistat(ind_stats))



#%% main()

def main():
    data = get_data()
    print(type(data))
    #print(x)
    get_unistat(ind_stats=True)

#%% If name main
if __name__ == '__main__':
    main()

