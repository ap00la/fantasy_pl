import requests
import json
import time


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


#%% main()

def main():
    data = get_data()
    print(type(data))
    #print(x)


#%% If name main
if __name__ == '__main__':
    main()

