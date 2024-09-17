## UNIVERSITY OF MINNESOTA CANSAT 2023-2024
# Ground Station Software

# WebServer
# serves as telemetry GUI

# Python imports
import os
import time
import datetime

# Dash/Plotly/Pandas imports
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots

# Global variables
#Receiver = None
simActivated = False
simEnabled = False
TelemHandler = None

# Disable unnecessary POST messages
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# ======================
# APP STYLING AND LAYOUT
# ======================

dir_path = os.path.dirname(os.path.realpath(__file__))
css_path = os.path.join(dir_path, 'web', 'css', 'custom.css')
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, css_path])

# Creates and styles top row buttons
app.layout = html.Div([
    dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand("MinneSat 2024", className="ml-2", style={'fontSize': '20px', 'fontWeight': 'bold', 'fontFamily': 'Lato, sans-serif'}),
                dbc.Nav(
                    [
                        dbc.Button("TELEMETRY ON", id="cx_button", n_clicks=0, className="nav-button", style={'margin': '5px'}),
                        dbc.Button("SYNC TIME RTC", id="st_gps_button", className="nav-button", style={'margin': '5px'}),
                        dbc.Button("ENABLE SIM MODE", id="sim_enable", n_clicks=0, className="nav-button", style={'margin': '5px'}),
                        dbc.Button("ACTIVATE SIM MODE", id="sim_activate", className="nav-button", disabled=True, style={'margin': '5px'}),
                        dbc.Button("CALIBRATE ALTITUDE", id="calibrate_alt", className="nav-button", style={'margin': '5px'}),
                        dbc.Button("DETACH", id="detach", className="nav-button", style={'margin': '5px'}), ## Added for possible heat sheild feature
                        dbc.Button("BEACON", id="beacon", className="nav-button", style={'margin': '5px'}),
                        dbc.Button('RESET FSW', id="reset_fsw", className="nav-button", style={'margin': '5px'}, color="danger"),
                        dbc.Button("SAVE CSV", id="save_csv", className="nav-button", style={'margin': '5px'}, color="success"),
                        dbc.Button('CLEAR TELEMETRY', id="clear_telem", className="nav-button", style={'margin': '5px'}, color="danger"),
                    ],
                    navbar=True,
                ),
                html.Div(id="current-time", className="ml-auto", style={'margin': '10px'}),
            ],
            fluid=True,
            className="d-flex justify-content-between align-items-center",
        ),
        color="dark",
        dark=True,
    ),
    html.Div(id='live-update-text', style={'height': '7vh', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center', 'fontFamily': 'Courier'}),
    dcc.Graph(id='live-update-graph', style={'height': '80vh'}),
    dcc.Interval(
        id='interval-component',
        interval=1000, # in milliseconds
        n_intervals=0
    )
])

# Callback for updating time
@app.callback(
    Output("current-time", "children"),
    [Input("interval-component", "n_intervals")]
)
def update_current_time(n):
    current_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"{current_time}"

# ===============
# BUTTON COMMANDS
# ===============

# ENABLE TELEMETRY
@app.callback(
    Output('cx_button', 'children'),
    Input('cx_button', 'n_clicks' )
)
def toggle_telemetry(n_clicks):
    if (n_clicks % 2 == 1):                 # Odd number of clicks necessarily means turning on telemetry, if telemtry starts off
        Receiver.issueCommand('CX', 'ON,')  # need the extra space after 'ON' to make it work because padding issues
        return 'TELEMETRY OFF'              # Change the button to read 'Telemetry Off' as next button press with toggle it off
    else:
        Receiver.issueCommand('CX', 'OFF,')
        return 'TELEMETRY ON' # Change button text
        
# SET RTC TIME (syncs rtc with GSC)
@app.callback(
    Output('st_gps_button', 'children'),
    Input('st_gps_button', 'n_clicks')
)
def set_time_rtc(unused):
    # fetches current time
    current_time = datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S,')

    # sends out command & UTC time string
    Receiver.issueCommand('ST', current_time)

    # triggers app callback
    return "SYNC TIME RTC"
    
# ENABLE SIMULATION MODE * (allows sim mode to be activated - fail safe for the competition) (no XBEE commands sent using this)
@app.callback(
    Output('sim_enable', 'children'),
    Input('sim_enable', 'n_clicks')
)
def sim_enable(n_clicks):
    # allows global to be modified
    global simEnabled

    # determines action based off of number of clicks
    if (n_clicks % 2 == 1):
        simEnabled = True
        Receiver.issueCommand('SIM', 'ENABLE,')
        return 'DISABLE SIM MODE'
    else:
        simEnabled = False
        Receiver.issueCommand('SIM', 'DISABLE,')
        return 'ENABLE SIM MODE'
        
# DISABLE ACTIVATE BUTTON * (i.e. can't be clicked until enable button above is)
@app.callback(
    Output('sim_activate', 'disabled'),
    Input('sim_enable', 'n_clicks')
)
def toggle_activate_button(n):
    if n % 2 == 0:  # this means 'sim_enable' button has not been clicked yet, so 'sim_activate' should be disabled
        return True
    else:
        return False
    
# ACTIVATE SIMULATION MODE * (toggles sim mode)
@app.callback(
    Output('sim_activate', 'children'),
    Input('sim_activate', 'n_clicks')
)
def sim_activate(unused):
    # cannot be deactivated
    global simActivated

    # sends out XBee command to CanSat
    Receiver.issueCommand('SIM', 'ACTIVATE,')

    # updates website and global variable
    simActivated = True
    return "ACTIVATE SIM MODE"
    
# CALIBRATE ALTITUDE (calibrates altitude to 0)
@app.callback(
    Output('calibrate_alt', 'children'),
    Input('calibrate_alt', 'n_clicks')
)
def calibrate_altitude(unused):
    Receiver.issueCommand('CAL','')
    return "CALIBRATE ALTITUDE"

# DETACH (detaches the heat shield)
# IMPLEMENT THE DETACH FUNCTIONALITY (IMPLEMENT RESPONSE IN FLIGHT SOFTWARE)
@app.callback(
    Output('detach', 'children'),
    Input('detach', 'n_clicks')
)
def detach_heat_shield(n_clicks):
    # can only be detached once
    if n_clicks is None:
        return 'DETACH'
    elif n_clicks % 2 == 1: 
        return 'ARE YOU SURE?' 
    else:
        Receiver.issueCommand('DETACH', ',')
        print('Detaching Heat Shield')
        return 'HEAT SHIELD DETACHED'

# SAVE CSV * (saves CVS file with data)
@app.callback(
    Output('save_csv', 'children'),
    Input('save_csv', 'n_clicks')
)
def save_csv(unused):
    TelemHandler.writeToCSV()
    return "SAVE CSV"

# BEACON (toggles the audio beacon)
# IMPLEMENT THE BEACON FUNCTIONALITY
@app.callback(
    Output('beacon', 'children'),
    Input('beacon', 'n_clicks')
)
def toggle_beacon(n_clicks):
    if n_clicks is None:
        return 'BEACON OFF'
    elif n_clicks % 2 == 1: 
        Receiver.issueCommand('BCN', 'ON,')
        return 'BEACON OFF' 
    else:
        Receiver.issueCommand('BCN', 'OFF,')
        return 'BEACON ON'
        
# RESET FSW (resets FSW)
@app.callback(
    Output('reset_fsw', 'children'),
    Input('reset_fsw', 'n_clicks')
)
def clear_telem(n_clicks):
    if n_clicks is None:
        return 'RESET FSW'
    if n_clicks % 2 == 0:
        print("Clearing Telemetry")
        Receiver.issueCommand('RESET', ',')
        return "RESET FSW"
    else:
        return "ARE YOU SURE?"

# CLEAR TELEMETRY (clears telemetry data)
@app.callback(
    Output('clear_telem', 'children'),
    Input('clear_telem', 'n_clicks')
)
def clear_telem(n_clicks):
    if n_clicks is None:
        return 'CLEAR TELEMETRY'
    if n_clicks % 2 == 0:
        print("Clearing Telemetry")
        TelemHandler.clearData()
        return "CLEAR TELEMETRY"
    else:
        return "ARE YOU SURE?"

# ===============================
# TELEMETRY INFORMATION & FIGURES
# ===============================

# Formats Header & Updates Header Values
@app.callback(
    Output('live-update-text', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_telemetry(n):
    # filters out desired info
    DATA = TelemHandler.TelemDict
    telem_keys = [
        'TEAM_ID', 
        'MISSION_TIME', 
        'PACKET_COUNT', 
        'MODE', 
        'STATE',
        'HS_DEPLOYED', 
        'PC_DEPLOYED',  
        'GPS_TIME', 
        'GPS_SATS', 
        'CMD_ECHO',
        'AIR_SPEED'
    ]
    
    # formatting
    style={'padding': '5px', 'height': '7vh', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center', 'fontFamily': 'Courier'}

    # rejects packet if team ID is not found
    if not DATA['TEAM_ID']:
        return [html.Span(f'{k} = \n[N/A]   ', style=style) for k in telem_keys]
    else:
        return [html.Span(f'{k} = \n[{DATA[k][-1]}]   ', style=style) for k in telem_keys]

#Formats Graphs & Updates Graph Values  
@app.callback(
    Output('live-update-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph_live(n):
    DATA = TelemHandler.TelemDict
    TIME_VAL = DATA['MISSION_TIME_VALUE']
    TIME_STR = DATA['MISSION_TIME']
    PACKETS = DATA['PACKET_COUNT']
    X_VALS = PACKETS # change this
    # print(TIME_VAL)

    # Create the graph with subplots & set titles
    fig = make_subplots(
        rows=2,
        cols=4,
        subplot_titles=(
            "ALTITUDE",
            "TEMPERATURE",
            "PRESSURE",
            "VOLTAGE",
            "GPS_ALTITUDE",
            "GPS_LONGITUDE VS. GPS_LATITUDE",
            "ROT_Z",
            "TILT_X/TILT_Y",
        )
    )
    # Handles individual graph layout
    fig['layout']['legend'] = {
        'x' : 0.5,
        'y' : 1.1,
        'xanchor' : 'center',
        'yanchor' : 'top',
        'orientation' : 'h'}
    fig.append_trace({
        'x': X_VALS,
        'y': DATA['ALTITUDE'],
        'name': 'ALTITUDE',
        'mode': 'lines+markers',
        'type': 'scatter',
        'line': {'color': 'black'}
    }, 1, 1)
    fig.append_trace({
        'x': X_VALS,
        'y': DATA['TEMPERATURE'],
        'name': 'TEMPERATURE',
        'mode': 'lines+markers',
        'type': 'scatter',
        'line': {'color': 'black'}
    }, 1, 2)
    fig.append_trace({
        'x': X_VALS,
        'y': DATA['PRESSURE'],
        'name': 'PRESSURE',
        'mode': 'lines+markers',
        'type': 'scatter',
        'line': {'color': 'black'}
    }, 1, 3)
    fig.append_trace({
        'x': X_VALS,
        'y': DATA['VOLTAGE'],
        'name': 'VOLTAGE',
        'mode': 'lines+markers',
        'type': 'scatter',
        'line': {'color': 'black'}
    }, 1, 4)
    fig.append_trace({
        'x': X_VALS,
        'y': DATA['GPS_ALTITUDE'],
        'name': 'GPS_ALTITUDE',
        'mode': 'lines+markers',
        'type': 'scatter',
        'line': {'color': 'black'}
    }, 2, 1)
    fig.append_trace({
        'x': DATA['GPS_LONGITUDE'],
        'y': DATA['GPS_LATITUDE'],
        'name': 'GPS_LONGITUDE VS. GPS_LATITUDE',
        'mode': 'lines+markers',
        'type': 'scatter',
        'line': {'color': 'black'}
    }, 2, 2)
    fig.append_trace({
        'x': X_VALS,
        'y': DATA['ROT_Z'],
        'name': 'ROTATION_Z',
        'mode': 'lines+markers',
        'type': 'scatter',
        'line': {'color': 'black'}
    }, 2, 3)
    fig.append_trace({
        'x': X_VALS,
        'y': DATA['TILT_X'],
        'name': 'TILT_X',
        'mode': 'lines+markers',
        'type': 'scatter',
        'line': {'color': 'black'}
    }, 2, 4)
    fig.append_trace({
        'x': X_VALS,
        'y': DATA['TILT_Y'],
        'name': 'TILT_Y',
        'mode': 'lines+markers',
        'type': 'scatter',
        'line': {'color': 'blue'}
    }, 2, 4)

    # Fine tunes web settings
    fig.update_layout(
        plot_bgcolor='white',  # Light blue background color
        paper_bgcolor='rgb(204,204,204)', # Light blue background color for subplot
        margin=dict(l=70, r=30, t=60, b=60), # Controls the margins around the graphs
        font=dict(
            family="Courier New, monospace",
            size=14,
            color="black"
        )
    )

    # Updates chart labels & grid line colors

    #ALTITUDE
    fig.update_xaxes(title_text="Time (s)", row=1, col=1)
    fig.update_yaxes(title_text="Altitude (m)", row=1, col=1)
    fig.update_xaxes(gridcolor='rgb(89,89,87)',row=1, col=1)
    fig.update_yaxes(gridcolor='rgb(89,89,87)',row=1, col=1)

    #TEMPERATURE
    fig.update_xaxes(title_text="Time (s)", row=1, col=2)
    fig.update_yaxes(title_text="Temperature (C)", row=1, col=2)
    fig.update_xaxes(gridcolor='rgb(89,89,87)',row=1, col=2)
    fig.update_yaxes(gridcolor='rgb(89,89,87)',row=1, col=2)

    #PRESSURE
    fig.update_xaxes(title_text="Time (s)", row=1, col=3)
    fig.update_yaxes(title_text="Pressure (kPa)", row=1, col=3)
    fig.update_xaxes(gridcolor='rgb(89,89,87)',row=1, col=3)
    fig.update_yaxes(gridcolor='rgb(89,89,87)',row=1, col=3)

    #VOLTAGE
    fig.update_xaxes(title_text="Time (s)", row=1, col=4)
    fig.update_yaxes(title_text="Voltage (v)", row=1, col=4)
    fig.update_xaxes(gridcolor='rgb(89,89,87)',row=1, col=4)
    fig.update_yaxes(gridcolor='rgb(89,89,87)',row=1, col=4)

    #GPS_ALTITUDE
    fig.update_xaxes(title_text="Time (s)", row=2, col=1)
    fig.update_yaxes(title_text="Altitude (m)", row=2, col=1)
    fig.update_xaxes(gridcolor='rgb(89,89,87)',row=2, col=1)
    fig.update_yaxes(gridcolor='rgb(89,89,87)',row=2, col=1)

    #GPS_LATITUDE/GPS_LONGITUDE
    fig.update_xaxes(title_text="Longitude (°West)", row=2, col=2)
    fig.update_yaxes(title_text="Latitude (°North)", row=2, col=2)
    fig.update_xaxes(gridcolor='rgb(89,89,87)',row=2, col=2)
    fig.update_yaxes(gridcolor='rgb(89,89,87)',row=2, col=2)

    #ROTATION_Z
    fig.update_xaxes(title_text="Time (s)", row=2, col=3)
    fig.update_yaxes(title_text="Rotation (°/s)", row=2, col=3)
    fig.update_xaxes(gridcolor='rgb(89,89,87)',row=2, col=3)
    fig.update_yaxes(gridcolor='rgb(89,89,87)',row=2, col=3)

    #TILT_X/TILT_Y
    fig.update_xaxes(title_text="Time (s)", row=2, col=4)
    fig.update_yaxes(title_text="Tilt (°)", row=2, col=4)
    fig.update_xaxes(gridcolor='rgb(89,89,87)',row=2, col=4)
    fig.update_yaxes(gridcolor='rgb(89,89,87)',row=2, col=4)

    return fig

# ===================
# RUN SERVER AND MAIN
# ===================
def run_server(app):
    app.run_server(debug=False)

if __name__ == "__main__":
    # avoid using this to debug, it's kinda whack
    from TelemetryHandler import TelemetryHandler
    TelemHandler = TelemetryHandler()
    app.run_server(debug=True)