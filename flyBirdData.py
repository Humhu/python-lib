import time, sys, math
from struct import *
from serial import *
from xbee import XBee
from lib.payload import Payload
from lib.commandinterface import CommandInterface
from lib.telemetryreader import TelemetryReader

def txCallback(dest, packet):
    global xb
    xb.tx(dest_addr = dest, data = packet)
    time.sleep(0.2)
    
def processPacket(packet):
    global coord, reader
    
    coord.processPacket(packet)
    reader.processPacket(packet)
    
def body():    
    global coord, reader, ser, xb
    
    DEFAULT_COM_PORT = 'COM7'
    DEFAULT_BAUD_RATE = 57600
    DEFAULT_ADDRESS = '\x10\x21'
    DEFAULT_PAN = 0x1001
    DEFAULT_DATAPOINTS = 300
    
    if len(sys.argv) == 1:
        com = DEFAULT_COM_PORT
        baud = DEFAULT_BAUD_RATE
        addr = DEFAULT_ADDRESS
        datapoints = DEFAULT_DATAPOINTS
    elif len(sys.argv) == 5:
        com = sys.argv[1]
        baud = int(sys.argv[2])
        addr = pack('>H', int(sys.argv[3], 16))
        datapoints = int(sys.argv[4])
    else:
        print "Incorrect number of arguments. Must be: COM, BAUD, DEST_ADDR, NUM_DATAPOINTS"
        sys.exit(1)
        
    thrust = 80
    steer = 0
        
    coord = CommandInterface(addr, txCallback)
    coord.enableDebug()
    
    reader = TelemetryReader(addr, txCallback)
    reader.setFileMode(True)
    reader.setConsoleMode(True)
    
    ser = Serial(port = com, baudrate = baud)
    xb = XBee(ser, callback = reader.processPacket)
    print "Setting PAN ID to " + hex(DEFAULT_PAN)
    xb.at(command = 'ID', parameter = pack('>H', DEFAULT_PAN))
    
    raw_input("Press any key to begin initialization...")    
        
    coord.getGyroCalibParam()        
    coord.setRemoteControl(True)
    coord.setRemoteControlValues(0.0, 0.0)
    
    raw_input("Press any key to begin flight...")
    
    coord.setRemoteControlValues(thrust, steer)
    
    raw_input("Press any key to begin sensor dump...")
    coord.startSensorDump(datapoints)
    
    raw_input("Press any key to begin landing...")

    coord.setRemoteControlValues(45.0, 0.0)
    
    raw_input("Press any key to halt motors...")
    
    coord.setRemoteControlValues(0.0, 0.0)
    
    raw_input("Press any key to request data...")
    coord.requestDumpData(0x80, 0x80 + int(math.ceil(datapoints/12.0)), 22)
    
def cleanup():
    global reader, xb, ser
    
    raw_input("Press any key once data reception has completed.")
    reader.close()
    xb.halt()
    ser.close()
    sys.exit(0)

if __name__ == '__main__':

    #try:
    body()
    #finally:
    cleanup()
