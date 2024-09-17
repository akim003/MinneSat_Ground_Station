## UNIVERSITY OF MINNESOTA CANSAT 2023-2024
# Ground Station Software

# TelemetryHandler
# This class handles parsing .csv data
import datetime
import pandas as pd

class TelemetryHandler:
    def __init__(self) -> None:
        self.TelemDict = {
            'TEAM_ID': [],
            'MISSION_TIME': [],
            'MISSION_TIME_VALUE': [], ### might need to distinguish this from the other fields becuase its not required
            'PACKET_COUNT': [],
            'MODE': [],
            'STATE': [],
            'ALTITUDE': [],
            'AIR_SPEED' : [], ### new entry
            'HS_DEPLOYED': [],
            'PC_DEPLOYED': [],
            'TEMPERATURE': [],
            'PRESSURE': [],
            'VOLTAGE': [],
            'GPS_TIME': [],
            'GPS_ALTITUDE': [],
            'GPS_LATITUDE': [],
            'GPS_LONGITUDE': [],
            'GPS_SATS': [],
            'TILT_X': [],
            'TILT_Y': [],
            'ROT_Z' : [], ### new entry
            'CMD_ECHO': [],
        } ### removed a return statement
        
    ### replaced the clearData() method so both fields don't have to be updated every time an entry gets changed
    def clearData(self):
        for key in self.TelemDict.keys():
            self.TelemDict[key].clear()

    def __repr__(self) -> str:
        return('There are currently ' + str(len(self.TelemDict['PACKET_COUNT'])) + ' packets being stored.') # Not sure what else to print
    
    ### ADDED: Return Statement, Try & Except Blocks, and Comment
    # reads given CVS file and assigns its values to self.TelemDict
    def readFromCSV(self, filename) -> bool: 
        try:
            self.TelemDict = pd.read_csv(filename).to_dict(orient='list') #pandas read to csv to dict formatting elements as lists
            return True
        except Exception as e:
            print(f"Error reading file: {e}")
            return False

    ### ADDED: Try & Except Blocks, Return Statements, and Comment    
    # creates a CVS file and names it based on current mission time and date, populating it with TelemDict data. Used to transfer data
    def writeToCSV(self) -> bool:
        try:
            time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"flight_data_{time}.csv"
            filepath = f"Ground Station\\data\\{filename}"
            df = pd.DataFrame(self.TelemDict)
            df.to_csv(filepath, index=False)
            print(f"Saved to CSV: {filename}")
            return True
        except Exception as e:
            print(f"Error saving to CVS: {e}")
            return False

    ### ADDED: Comment
    # converts mission time into seconds
    def missionTimeToInt(self, missionTime):
         h,m,s = missionTime.split(":")
         return int(h) * 3600 + int(m) * 60 + int(s)
    
    ### ADDED: updated packet numbers and new data fields
    def pushData(self, packet) -> bool:
        """
        Push a single packet onto the container data dictionary

        Args:
            packet (str list): a list of strings representing a data packet

        Returns:
            bool: True or False if successfully pushed onto dictionary
        """
        packet = packet.split(",")

        self.TelemDict['TEAM_ID'].append(packet[0][1:])
        # Since time is a formatted string, we'll keep a second value for comparison reasons
        self.TelemDict['MISSION_TIME'].append(packet[1])
        self.TelemDict['MISSION_TIME_VALUE'].append(self.missionTimeToInt(packet[1]))
        # In case power cycles, add to last packet count
        # e.g. packet 5 was last received, then power cycles and packet 1 is received
        # appends packet 6 rather than 1 again
        lastPacket = self.TelemDict['PACKET_COUNT'][-1] if self.TelemDict['PACKET_COUNT'] else 0
        self.TelemDict['PACKET_COUNT'].append(int(packet[2]) + lastPacket if int(packet[2]) < lastPacket else int(packet[2]))

        self.TelemDict['MODE'].append(packet[3])
        self.TelemDict['STATE'].append(packet[4])
        self.TelemDict['ALTITUDE'].append(float(packet[5]))
        self.TelemDict['AIR_SPEED'].append(float(packet[6])) 
        self.TelemDict['HS_DEPLOYED'].append(packet[7]) 
        self.TelemDict['PC_DEPLOYED'].append(packet[8]) 
        self.TelemDict['TEMPERATURE'].append(float(packet[9]))
        self.TelemDict['PRESSURE'].append(float(packet[10]))
        self.TelemDict['VOLTAGE'].append(float(packet[11]))
        self.TelemDict['GPS_TIME'].append(datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")) # TODO: Format?
        self.TelemDict['GPS_ALTITUDE'].append(float(packet[13]))
        self.TelemDict['GPS_LATITUDE'].append(float(packet[14])/10000000)
        self.TelemDict['GPS_LONGITUDE'].append(float(packet[15])/10000000)
        self.TelemDict['GPS_SATS'].append(int(packet[16]))
        self.TelemDict['TILT_X'].append(float(packet[17]))
        self.TelemDict['TILT_Y'].append(float(packet[18]))
        self.TelemDict['ROT_Z'].append(float(packet[19]))
        self.TelemDict['CMD_ECHO'].append(packet[20][:-1])

        return True