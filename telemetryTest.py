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
    
if __name__ == '__main__':

    DEFAULT_COM_PORT = 'COM21'
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
    telem = TelemetryReader(addr, txCallback)
    
    telem.setConsoleMode(True)
    #telem.setFileMode(True)
    #telem.writeHeader();
    
    ser = Serial(port = com, baudrate = baud)
    xb = XBee(ser, callback = telem.processPacket)
    
    print "Setting PAN ID to " + hex(DEFAULT_PAN)
    xb.at(command = 'ID', parameter = pack('>H', DEFAULT_PAN))
    
    coord.setEstimateRunning(True)
    
    while(True):
        try:
            time.sleep(0.1)
            coord.requestTelemetry()
        except KeyboardInterrupt:
            break
    
    xb.halt()
    telem.close()
    ser.close()