from digi.xbee.devices import XBeeDevice
from collections import deque
import time
import serial

class Receiver:
    RxBuff = bytearray()
    RxMessages = deque()

    def __init__(self,com='COM3',baud=921600) -> None:
        """
        Instantiates local receiver instance.

        Args:
            string (com) : string name of com port used, ex: "COM3"
            int (baud) : baud rate, ex: 9600
        """
        print("\nInitializing XBEE on %s at %s baud" %(com,baud))
        self.xbee = XBeeDevice(com,baud)
        self.serial = serial.Serial(port=com, baudrate=baud)
        #self.xbee.open()
        #self.xbee.refresh_device_info()
        print("Done initializing XBeeReceiver \n")


    def close(self):
        self.xbee.close()

    def __repr__(self) -> str:
        #TODO
        pass

    def read_data(self):
        """
        Reads and returns formatted data

        Returns:
            str: a formatted string of data, or None if no message was read
        """

        #TODO: multiple return styles?
        msg = self.Receive()

        if msg:
            return self.format_to_str(msg)
        
        return None

    def Validate(self, msg):
        """
        NOT WRITTEN BY ALEX
        Parses a byte or bytearray object to verify the contents are a
          properly formatted XBee message.

        Inputs: 
            msg: an incoming XBee message
        Outputs: 
            bool: indicating message validity
        """
        # 9 bytes is Minimum length to be a valid Rx frame
        #  LSB, MSB, Type, Source Address(2), RSSI,
        #  Options, 1 byte data, checksum
        if (len(msg) - msg.count(bytes(b'0x7D'))) < 9:
            return False

        # All bytes in message must be unescaped before validating content
        frame = self.Unescape(msg)

        if frame:
            LSB = frame[1]
        else:
            return False
        # Frame (minus checksum) must contain at least length equal to LSB
        if LSB > (len(frame[2:]) - 1):
            return False

        # Validate checksum
        if (sum(frame[2:3+LSB]) & 0xFF) != 0xFF:
            return False

        #print("Rx: " + self.format(bytearray(b'\x7E') + msg))
        self.RxMessages.append(frame)
        return True

    def Send(self, msg, addr=0x6502, options=0x01, frameid=0x01):
        '''
        NOT WRITTEN BY ETHAN
        Doing what Alex did and copied some code
        Need an address for the remote xbee though
        '''
        if not msg:
            return 0

        hexs = '7E 00 {:02X} 01 {:02X} {:02X} {:02X} {:02X}'.format(
            len(msg) + 5,           # LSB (length)
            frameid,
            (addr & 0xFF00) >> 8,   # Destination address high byte
            addr & 0xFF,            # Destination address low byte
            options
        )

        frame = bytearray.fromhex(hexs)
        #  Append message content
        frame.extend(msg)

        # Calculate checksum byte
        frame.append(0xFF - (sum(frame[3:]) & 0xFF))

        # Escape any bytes containing reserved characters
        frame = self.Escape(frame)

        print("Tx: " + self.format(frame))
        return self.serial.write(frame)

    def SendStr(self, msg, addr=0x6502, options=0x01, frameid=0x01):
        print(f"SENDING COMMAND: {msg}")
        return self.Send(msg.encode('utf-8'), addr, options, frameid)

    def Receive(self):
        """
        NOT WRITTEN BY ALEX
        note: needs to be dissected a little, I have no idea what this does
        """
        remaining = self.serial.inWaiting()
        while remaining:
            chunk = self.serial.read(remaining)
            remaining -= len(chunk)
            self.RxBuff.extend(chunk)

        msgs = self.RxBuff.split(bytes(b'\x7E'))
        for msg in msgs[:-1]:
            self.Validate(msg)

        self.RxBuff = (bytearray() if self.Validate(msgs[-1]) else msgs[-1])

        if self.RxMessages:
            return self.RxMessages.popleft()
        else:
            return None

    def Unescape(self, msg):
        """
        NOT WRITTEN BY ALEX
        Helper function to unescaped an XBee API message.

        Inputs:
          msg: An byte or bytearray object containing a raw XBee message
               minus the start delimeter
        Outputs:
          XBee message with original characters.
        """
        if msg[-1] == 0x7D:
            # Last byte indicates an escape, can't unescape that
            return None

        out = bytearray()
        skip = False
        for i in range(len(msg)):
            if skip:
                skip = False
                continue

            if msg[i] == 0x7D:
                out.append(msg[i+1] ^ 0x20)
                skip = True
            else:
                out.append(msg[i])

        return out

    def Escape(self, msg):
        """
        Escapes reserved characters before an XBee message is sent.
        Inputs:
          msg: A bytes or bytearray object containing an original message to
               be sent to an XBee
         Outputs:
           A bytearray object prepared to be sent to an XBee in API mode
         """
        escaped = bytearray()
        reserved = bytearray(b"\x7E\x7D\x11\x13")

        escaped.append(msg[0])
        for m in msg[1:]:
            if m in reserved:
                escaped.append(0x7D)
                escaped.append(m ^ 0x20)
            else:
                escaped.append(m)

        return escaped

    def format(self, msg):
        """
        NOT WRITTEN BY ALEX
        Formats a byte or bytearray object into a more human readable string
          where each bytes is represented by two ascii characters and a space

        Input:
          msg: A bytes or bytearray object
        Output:
          A string representation
        """
        return " ".join("{:02x}".format(b) for b in msg)

    def format_to_str(self,msg):
        """
        Formats a byte or bytearray object into a string representation of JUST the data.
        Currently assumes the header is 6 bytes, and the checksum is 1 byte - possibly faulty assumption?

        Args:
            msg: byte or bytearray object
        Returns:
            str: just the data field represented as a string (loses other packet information)
        """
        
        #TODO: validate/test faulty or lossy packets and catch them

        str = self.format(msg)
        splt = str.split(' ')
        #print(splt) # for error checking
        str = ''.join(list(map(lambda x:chr(int(x,16)),splt)))[6:-1] #be careful about the indexing here, ask Alex if this breaks
        return str.replace('\n','') #removes newline characters before returning

    def format_to_packet(self,msg):
        #TODO: returns a dictionary without losing packet information (like length and checksum)
        #not sure if this is needed yet
        pass

    def issueCommand(self, cmd, value) -> bool:
        if cmd == 'CX':
            self.SendStr('CMD,2056,CX,' + value)
            return True
        elif cmd == 'ST': # update time
            self.SendStr('CMD,2056,ST,' + value)
            return True
        elif cmd == 'SIM':
            self.SendStr('CMD,2056,SIM,' + value)
            return True
        elif cmd == 'SIMP':
            self.SendStr('CMD,2056,SIMP,' + value)
            return True
        elif cmd == 'CAL':
            self.SendStr('CMD,2056,CAL,' + value)
            return True
        elif cmd == 'BCN':
            self.SendStr('CMD,2056,BCN,' + value)
            return True
        elif cmd == 'DETACH':
            self.SendStr('CMD,2056,DETACH' + value)
        elif cmd == 'RESET':
            self.SendStr('CMD,2056,RESET' + value)
        else:
            print('Nonsupported command received, not issuing.')
            return False


def timeclock(t):
    """
    Simple formatting function for displaying time (used below)

    Args:
        t (int): the current time step

    Returns:
        str: a formatted string displaying the time
    """
    mm = int(t/60)
    ss = t % 60

    if mm < 10:
        clock_str = "[0"+str(mm)
    else:
        clock_str = "["+str(mm)
    if ss < 10:
        clock_str += ":0"+str(ss)+"]"
    else:
        clock_str += ":"+str(ss)+"]"

    return clock_str

if __name__ == "__main__":
    # THIS FILE IS NOT MEANT TO BE RAN DIRECTLY
    # this main function is only for testing

    #instantiate local device
    device = Receiver("COM3",9600)

    #read data
    t = 0
    while True:
        msg = device.read_data()
        # if msg:
        print(timeclock(t),":",msg)

        time.sleep(1)
        t += 1