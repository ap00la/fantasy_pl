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
    responseStr = response.text
    data = json.loads(responseStr)
    return data


#%% main()

def main():
    x = get_data()
    print(type(x))
    #print(x)


#%% If name main
if __name__ == '__main__':
    main()

