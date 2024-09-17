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
Receiver = None
simActivated = False
simEnabled = False
TelemHandler = None

# Disable unecessary POST messages
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# ======================
# APP STYLING AND LAYOUT
# ======================
# LOGO = "https://raw.github.umn.edu/MinneSat/umncansat22/master/GROUND_STATION/python/web/assets/MinneSat_2.png?token=GHSAT0AAAAAAAAAY6S4FY7ULUMAWXBMN3SWZEDYRFQ"

dir_path = os.path.dirname(os.path.realpath(__file__))
css_path = os.path.join(dir_path, 'web', 'css', 'custom.css')
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, css_path])
app.layout = html.Div([
    dbc.Navbar(
        dbc.Container(
            [
                # dbc.Col(html.Img(src=LOGO, height="50px"), width="auto", style={'margin': '15px'}),
                dbc.NavbarBrand("MinneSat 2024", className="ml-2", style={'fontSize': '20px', 'fontWeight': 'bold', 'fontFamily': 'Lato, sans-serif'}),
                dbc.Nav(
                    [
                        dbc.Button("TELEMETRY ON", id="cx_button", n_clicks=0, className="nav-button", style={'margin': '5px'}),
                        # dbc.Button("SET TIME UTC", id="st_utc_button", className="nav-button", style={'margin': '5px'}),
                        dbc.Button("SET TIME (GPS)", id="st_gps_button", className="nav-button", style={'margin': '5px'}),
                        dbc.Button("ENABLE SIM MODE", id="sim_enable", n_clicks=0, className="nav-button", style={'margin': '5px'}),
                        dbc.Button("ACTIVATE SIM MODE", id="sim_activate", className="nav-button", disabled=True, style={'margin': '5px'}),
                        dbc.Button("CALIBRATE ALTITUDE", id="calibrate_alt", className="nav-button", style={'margin': '5px'}),
                        dbc.Button("DEPLOY", id="deploy", className="nav-button", style={'margin': '5px'}),
                        dbc.Button("STOW", id="stow", className="nav-button", style={'margin': '5px'}),
                        dbc.Button("SAVE CSV", id="save_csv", className="nav-button", style={'margin': '5px'}, color="success"),
                        dbc.Button('CLEAR TELEMETRY', id="clear_telem", className="nav-button", style={'margin': '5px'}, color="danger"),
                        #     id='danger-danger',
                        # dcc.ConfirmDialogProvider(
                        #     dbc.Button('CLEAR TELEMETRY', id="clear_telem", className="nav-button", style={'margin': '5px'}, color="danger"),
                        #     id='danger-danger',
                        #     message='Are you sure you want to clear all Telemetry Data?'
                        # ),
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