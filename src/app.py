import dash
import pandas as pd
import numpy as np
import json
import seaborn as sns
import tools
import datetime
import pre_process as pp
import nest_asyncio
import matplotlib.pyplot as plt
import seaborn as sns
import dash
import logging
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output


#%% Logging set up
logger = logging.basicConfig(format='[%(levelname)s %(module)s] %(asctime)s - %(message)s', level = logging.INFO)
logger = logging.getLogger(__name__)

#%% Color Themes
player_categories = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
position_colors_list = ["red", "blue", "Orange", "Green"]
position_colors = {cat: color for cat, color in zip(player_categories, position_colors_list)}
team_names = ['Arsenal','Aston Villa','Brentford','Brighton and Hove Albion','Burnley','Chelsea','Crystal Palace','Everton',
        'Leeds','Leicester City','Liverpool','Manchester City','Manchester United','Newcastle United','Norwich City',
        'Southampton','Tottenham Hotspur','Watford','West Ham','Wolverhampton Wanderers']
teams = np.arange(1,21)

#%% Ingest and or Process
today = '_'.join(str(datetime.datetime.today()).split(' ')[0].split('-'))
try:
    logger.info(f"Looking for files dated - {today}")
    df = pd.read_pickle(".data/" + today + "_df")
    gw_df = pd.read_pickle(".data/" + today + "_gw_df")
    logger.info("Files found, skipping data download and procesing")
except FileNotFoundError:
    logger.info("Files not found. Attempting to download and process data now.")
    df, gw_df = pp.main(save_to_file=True)
    logger.info("Successfully downloaded and processed data.")

#%% Initialise APP
logger.info("Initialising Dash App")
app = dash.Dash(__name__)


#%% Layout
app.layout= html.Div(children=[
    
    html.H1("Premier League Fantasy Football Dashboard", style={"text-align": "left"}),

    html.H2('Overall Statistic Breakdown'),

#%% Section 1
    html.Div(
        children=[
            html.H4("High Level Breakdown of players", className="container_title"),

            # Pie chart of number of players GK, DEF, MID, ATT
            dcc.Graph(id='Player_breakdown',
                  figure=px.pie(df.groupby(['element_type'])['player_name'].count().reset_index(),
                  names='element_type',
                  values='player_name',
                  color='element_type',
                  hole=.3,
                  color_discrete_map=position_colors,
                  title = "Number of Players in each Position"
                  ),
                  style={'display': 'inline-block'}
                  ),
            
            # Pie chart showing total points per category of player divided by number of players per miinute played
            dcc.Graph(id='Point won by each catogery',
                  figure=px.pie(df.groupby(['element_type'])['total_points'].mean().reset_index(),
                  names='element_type',
                  values='total_points',
                  color='element_type',
                  hole=.3,
                  color_discrete_map=position_colors,
                  title = "Average Number of Total Points per player in each Position"
                  ),
                  style={'display': 'inline-block'},
                  )
            ]
    ),

#%% Section 2
# Scatter Plot

    html.Div(
        children=[
            html.H2("Overall Player Breakdown", className="container_title"),


            html.Div(
                children=[
                    
                    dcc.Dropdown(id='x_axis',
                        options=[
                            {'label': 'Dreamteam Count', 'value': 'dreamteam_count'},
                            {'label': 'Form', 'value': 'form'},
                            {'label': 'Now Cost', 'value': 'now_cost'},
                            {'label': 'Points Per Game', 'value': 'points_per_game'},
                            {'label': 'Selected By Percent', 'value': 'selected_by_percent'},
                            {'label': 'Total Points', 'value': 'total_points'},
                            {'label': 'Transfers In', 'value': 'transfers_in'},
                            {'label': 'Transfers Out', 'value': 'transfers_out'},
                            {'label': 'Value Form', 'value': 'value_form'},
                            {'label': 'Value Season', 'value': 'value_season'},
                            {'label': 'Minutes', 'value': 'minutes'},
                            {'label': 'Goals Scored', 'value': 'goals_scored'},
                            {'label': 'Assists', 'value': 'assists'},
                            {'label': 'Clean Sheets', 'value': 'clean_sheets'},
                            {'label': 'Goals Conceded', 'value': 'goals_conceded'},
                            {'label': 'Own Goals', 'value': 'own_goals'},
                            {'label': 'Penalties Saved', 'value': 'penalties_saved'},
                            {'label': 'Penalties Missed', 'value': 'penalties_missed'},
                            {'label': 'Yellow Cards', 'value': 'yellow_cards'},
                            {'label': 'Red Cards', 'value': 'red_cards'},
                            {'label': 'Saves', 'value': 'saves'},
                            {'label': 'Bonus', 'value': 'bonus'},
                            {'label': 'Bps', 'value': 'bps'},
                            {'label': 'Influence', 'value': 'influence'},
                            {'label': 'Creativity', 'value': 'creativity'},
                            {'label': 'Threat', 'value': 'threat'},
                            {'label': 'Ict Index', 'value': 'ict_index'},
                            {'label': 'Games', 'value': 'games'},
                            {'label': 'xG', 'value': 'xG'},
                            {'label': 'xA', 'value': 'xA'},
                            {'label': 'Shots', 'value': 'shots'},
                            {'label': 'Key_passes', 'value': 'key_passes'},
                            {'label': 'npg', 'value': 'npg'},
                            {'label': 'npxG', 'value': 'npxG'},
                            {'label': 'xGChain', 'value': 'xGChain'},
                            {'label': 'xGBuildup', 'value': 'xGBuildup'}],
                            multi=False,
                            value='now_cost',
                            style={'display': 'inline-block', "width":"50%"}
                            ),

                    dcc.Dropdown(id='y_axis',
                        options=[
                            {'label': 'Dreamteam Count', 'value': 'dreamteam_count'},
                            {'label': 'Form', 'value': 'form'},
                            {'label': 'Now Cost', 'value': 'now_cost'},
                            {'label': 'Points Per Game', 'value': 'points_per_game'},
                            {'label': 'Selected By Percent', 'value': 'selected_by_percent'},
                            {'label': 'Total Points', 'value': 'total_points'},
                            {'label': 'Transfers In', 'value': 'transfers_in'},
                            {'label': 'Transfers Out', 'value': 'transfers_out'},
                            {'label': 'Value Form', 'value': 'value_form'},
                            {'label': 'Value Season', 'value': 'value_season'},
                            {'label': 'Minutes', 'value': 'minutes'},
                            {'label': 'Goals Scored', 'value': 'goals_scored'},
                            {'label': 'Assists', 'value': 'assists'},
                            {'label': 'Clean Sheets', 'value': 'clean_sheets'},
                            {'label': 'Goals Conceded', 'value': 'goals_conceded'},
                            {'label': 'Own Goals', 'value': 'own_goals'},
                            {'label': 'Penalties Saved', 'value': 'penalties_saved'},
                            {'label': 'Penalties Missed', 'value': 'penalties_missed'},
                            {'label': 'Yellow Cards', 'value': 'yellow_cards'},
                            {'label': 'Red Cards', 'value': 'red_cards'},
                            {'label': 'Saves', 'value': 'saves'},
                            {'label': 'Bonus', 'value': 'bonus'},
                            {'label': 'Bps', 'value': 'bps'},
                            {'label': 'Influence', 'value': 'influence'},
                            {'label': 'Creativity', 'value': 'creativity'},
                            {'label': 'Threat', 'value': 'threat'},
                            {'label': 'Ict Index', 'value': 'ict_index'},
                            {'label': 'Games', 'value': 'games'},
                            {'label': 'xG', 'value': 'xG'},
                            {'label': 'xA', 'value': 'xA'},
                            {'label': 'Shots', 'value': 'shots'},
                            {'label': 'Key_passes', 'value': 'key_passes'},
                            {'label': 'npg', 'value': 'npg'},
                            {'label': 'npxG', 'value': 'npxG'},
                            {'label': 'xGChain', 'value': 'xGChain'},
                            {'label': 'xGBuildup', 'value': 'xGBuildup'}],
                            multi=False,
                            value='total_points',
                            style={'display': 'inline-block', "width":"50%"}
                            ),



                    dcc.Dropdown(id='filter_by',
                        options=[
                            {'label': 'Goalkeeper', 'value': 'Goalkeeper'},
                            {'label': 'Defender', 'value': 'Defender'},
                            {'label': 'Midfielder', 'value': 'Midfielder'},
                            {'label': 'Forward', 'value': 'Forward'}],
                            multi=True,
                            value=player_categories,
                            style={'display': 'inline-block', "width":"50%"}
                            ),

                ]
            ),

            dcc.Dropdown(id='team',
                 options=[
                      {'label': 'Arsenal', 'value': 1},
                      {'label': 'Aston Villa', 'value': 2},
                      {'label': 'Brentford', 'value': 3},
                      {'label': 'Brighton and Hove Albion', 'value': 4},
                      {'label': 'Burnley', 'value': 5},
                      {'label': 'Chelsea', 'value': 6},
                      {'label': 'Crystal Palace', 'value': 7},
                      {'label': 'Everton', 'value': 8},
                      {'label': 'Leeds', 'value': 9},
                      {'label': 'Leicester City', 'value': 10},
                      {'label': 'Liverpool', 'value': 11},
                      {'label': 'Manchester City', 'value': 12},
                      {'label': 'Manchester United', 'value': 13},
                      {'label': 'Newcastle United', 'value': 14},
                      {'label': 'Norwich City', 'value': 15},
                      {'label': 'Southampton', 'value': 16},
                      {'label': 'Tottenham Hotspur', 'value': 17},
                      {'label': 'Watford', 'value': 18},
                      {'label': 'West Ham', 'value': 19},
                      {'label': 'Wolverhampton Wanderers', 'value': 20}
                      ],
                      multi=True,
                      value=teams,
                      style={"width":"100%"}
                      ),

            # Graph showing POINTS vs Cost
            # Line of best fit through the data
            dcc.Graph(id='scatter_plot',
                      figure={},
                      style={'width': '100%', 'height': '100vh'}),
            
            ]
         ),


]
)



#%% Callback
# connect the plotly graphs with dash components
@app.callback(
    [Output(component_id="scatter_plot", component_property="figure")],
    [Input(component_id="x_axis", component_property="value"),
     Input(component_id="y_axis", component_property="value"),
     Input(component_id="filter_by", component_property="value"),
     Input(component_id="team", component_property="value")]
)

def update_graph(x_axis, y_axis, filter_by, team): # option_slct can be equal to value
    logger.info(f"X-axis selected is {x_axis}")
    logger.info(f"Y-axis selected is {y_axis}")

    #copy original dataframe
    dfc = df.copy()
    logger.info(f"Filtering results by: {filter_by}")
    dfc = dfc[dfc['element_type'].isin(filter_by)]
    
    logger.info(f"Showing the following teams: {team}")
    dfc = dfc[dfc['team'].isin(team)]

    # Plotly express
    fig = [px.scatter(dfc, 
                    x=x_axis,
                    y=y_axis,
                    color='element_type',
                    color_discrete_map=position_colors,
                    hover_data= ['player_name'],
                    title=f"{y_axis} vs {x_axis}"
                        )]
    
        # Plotly express
    return fig

#%% If name main
if __name__ == "__main__":
    app.run_server(debug=True)