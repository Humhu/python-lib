import time, sys, math
from struct import *
from serial import *
from xbee import XBee
from lib.payload import Payload
from lib.commandinterface import CommandInterface
from lib.telemetryreader import TelemetryReader
from lib.dictionaries import *

xb = None
coord = None
reader = None
ser = None

def txCallback(dest, packet):
    global xb
    xb.tx(dest_addr = dest, data = packet)
    
def processPacket(packet):
    global coord, reader
    
    coord.processPacket(packet)
    reader.processPacket(packet)

def body():

    global xb, ser

    DEFAULT_COM_PORT = 'COM7'
    DEFAULT_BAUD_RATE = 57600
    DEFAULT_ADDRESS = '\x10\x21'
    DEFAULT_PAN = 0x1001
            
    if len(sys.argv) == 1:
        com = DEFAULT_COM_PORT
        baud = DEFAULT_BAUD_RATE
        addr = DEFAULT_ADDRESS
    elif len(sys.argv) == 4:
        com = sys.argv[1]
        baud = int(sys.argv[2])
        addr = pack('>H', int(sys.argv[3], 16))

    coord = CommandInterface(addr, txCallback)
    coord.enableDebug()
    
    reader = TelemetryReader(addr, txCallback)
    reader.setConsoleMode(True)
        
    ser = Serial(port = com, baudrate = baud)
    xb = XBee(ser, callback = reader.processPacket)
    print "Setting PAN ID to " + hex(DEFAULT_PAN)
    xb.at(command = 'ID', parameter = pack('>H', DEFAULT_PAN))
    
    raw_input("Press any key to begin initialization.")
    
    yaw_coeffs = [YawPIDParams['Ref'], YawPIDParams['Offset'], YawPIDParams['Kp'],\
                YawPIDParams['Ki'], YawPIDParams['Kd'], YawPIDParams['Beta'],\
                YawPIDParams['Gamma']]
        
    pitch_coeffs = [PitchPIDParams['Ref'], PitchPIDParams['Offset'], PitchPIDParams['Kp'],\
                PitchPIDParams['Ki'], PitchPIDParams['Kd'], PitchPIDParams['Beta'],\
                PitchPIDParams['Gamma']]
    
    roll_coeffs = [RollPIDParams['Ref'], RollPIDParams['Offset'], RollPIDParams['Kp'],\
                RollPIDParams['Ki'], RollPIDParams['Kd'], RollPIDParams['Beta'],\
                RollPIDParams['Gamma']]
    
    #coord.setRegulatorPid(yaw_coeffs + pitch_coeffs + roll_coeffs)
    #coord.setEstimateRunning(True)

    raw_input("Press any key to begin flight.")
        
    #coord.setRegulatorState(RegulatorStates['Stabilize'])
    coord.setRegulatorState(RegulatorStates['Remote Control'])
    coord.setRemoteControlValues(85.0, -0.0, -0.5)
    
    raw_input("Press any key to begin landing.")
    
    coord.setRegulatorState(RegulatorStates['Remote Control'])
    coord.setRemoteControlValues(40.0, -0.0, -1.0)
    
    raw_input("Press any key to halt motors.")
    
    coord.setRemoteControlValues(0.0, 0.0, 0.0)
    
    
def cleanup():
    
    global xb, ser
    
    if xb != None:
        xb.halt()
    if ser != None:
        ser.close()
        
if __name__ == '__main__':

    try:
        body()
    finally:
        cleanup()
