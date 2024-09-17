# UNIVERSITY OF MINNESOTA CANSAT 2023-2024
# Ground Station Software

#Main.py
#Driver Class for the ground station

#XCTaU --> for xbee testing

# Import code we wrote
from TelemetryHandler import TelemetryHandler
from XBeeReceiver import Receiver
import WebServer

# Import Python libs
import pandas as pd
from pandas import read_csv
import time
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import threading

class CanSat:
    def __init__(self, com, baud, simpdata = None) -> None:
        """
        Initialize CanSat groundstation
        """
        # Initialize TelemetryHandler instance
        self.TelemetryHandler = TelemetryHandler()

        # Initialize XBeeReceiver Instance
        self.XBeeReceiver = Receiver(com,baud)
        WebServer.Receiver = self.XBeeReceiver

        # Save simulated pressure file
        self.simpData = simpData

    def run(self):    
        # Setting up multithreading so web page logic and telemetry logic can run side by side
        WebServer.TelemHandler = self.TelemetryHandler
        server_thread = threading.Thread(target=WebServer.run_server, args=(WebServer.app,))
        server_thread.daemon = True # Thread will terminate along with main program
        server_thread.start()

        WebServer.TelemHandler.readFromCSV(f"data\\sampleTestPackets.csv")
        WebServer.TelemHandler.readFromCSV(f"~/Documents/GitHub/cansat2024/Ground Station/data/sampleTestPackets.csv")
        WebServer.TelemHandler.writeToCSV()

        while True:
            try:
                if WebServer.simEnabled and WebServer.simActivated:
                    try:
                        # print("Sim mode activated")
                        pressure = self.simpData.pop()
                        print(pressure)
                        MinneSat.XBeeReceiver.issueCommand('SIMP', str(pressure) + ",") # send cansat simulated pressure data if in sim mode
                    except IndexError:
                        print("No more simulation data")
                        self.TelemetryHandler.writeToCSV()
                        break
                data = MinneSat.getData()
                MinneSat.handleData(data)
            except ValueError:
                # pass
                print("No data received")
            time.sleep(1)

    def handleData(self, data) -> bool:
        """
        Perform one cycle of updating data to relevant servers, in this order:
        1. TelemetryHandler for .csv
        2. WebServer

        Returns:
            bool: True on successful upload, False if there was an error
        """        
        print(f"GOT: {data}")

        if not self.TelemetryHandler.pushData(data):
            print("[ERROR]: Bad data type, not pushing data to dictionaries")
            return False

        #TODO: writetoweb function error checking
        if data:
            self.writeToWeb(data)
        else:
            # need to add some condition if no data was received?
            pass

        return True
    
    def writeToWeb(self, data):
        """
        Write to web server

        Args:
            data (dict): telemetry  as a dictionary, see TelemetryHandler.py for
                         more information
        """
        # needs error checking
        WebServer.df = pd.DataFrame(self.TelemetryHandler.TelemDict)
        return

    def getData(self) -> str:
        """
        Get data from XBee, if it's there or None if it's not

        Returns:
            data (str): formatted data packet or None
        """
        #TODO: error checking on return value
        data = self.XBeeReceiver.read_data()
        if not data:
            raise ValueError("Got None for data")
        return data

# Main methods

# Handles Invalid Responses to Preset Prompts
def userLogin() -> str:
    # Ensures user input is either 'y' or 'n'
    user_login  = (input("User Preset [y/n]? ").lower())
    while(user_login != 'y' and user_login != 'n'):
        print("Error: Invalid Input")
        user_login  = (input("User Preset [y/n]? ").lower())
        
    # Handles return value
    if user_login == 'n':
        return 'n'
        
    else:
        # Ensures user input is either 'alex' or 'ethan'
        user_data = (input("Enter User [Ethan, Alex] ").lower())
        while(user_data != 'alex' and user_data != 'ethan'):
            print("Error: Invalid Input")
            user_data = (input("Enter User [Ethan, Alex] ").lower())

        # Handles return value
        if user_data == 'alex':
            return 'alex'
        elif user_data == 'ethan':
            return 'ethan'

if __name__ == "__main__":
    """
    This should be the main function you're running when performing mission ops
    """
    print("\n[MINNESAT GROUNDSTATION]\n")

    # Allows easy access to presets
    userPresetResponse = userLogin()
    if userPresetResponse == "ethan":
        port = "COM4"
        baud = 921600
    elif userPresetResponse == "alex":
        port = "/dev/tty.usbserial-DN01A3YA"
        baud = 921600
    elif userPresetResponse == 'n':
        port = "COM4"
        baud = 921600

    # radio initialization
    initializeRadio = (input("Initialize Radio [y/n]? (default 'y')").lower() or "y")
    if initializeRadio == "y":
        port = input(f"Enter COM port (default '{port}'): ") or port
        baud = int(input(f"Enter baud rate (default '{baud}'): ") or baud)

    # load simulation mode data
    simp = (input("Load in .csv of simulated pressure data [y/n]? (default 'y'): ") or "y")== "y"
    if simp:
        simpFile = (input("Input filename, ensure file is in data directory (default `simpData.csv`): ") or "simpData.csv")
        if userPresetResponse == "alex":
            simpData = pd.read_csv(f'~/Documents/GitHub/cansat2024/Ground Station/data/{simpFile}', header=None)[3].tolist()
        else:
            simpData = pd.read_csv(f'~\\Documents\\GitHub\\cansat2024\\Ground Station\\data\\{simpFile}', header=None)[3].tolist()
        simpData.reverse()
    
    # initialize CanSat and run
    MinneSat = CanSat(port, baud, simpData)
    MinneSat.run()