import time, sys
from struct import *
from serial import *
from xbee import XBee
from lib import network_const
from lib.dictionaries import *
from lib.command_interface import CommandInterface
from lib.network_coordinator import NetworkCoordinator

THRUST_INCREMENT = 0.05
YAW_INCREMENT = -0.5
ELEVATOR_INCREMENT = 0.2

THRUST_UPPER_LIMIT = 1.0
THRUST_LOWER_LIMIT = 0.0
YAW_UPPER_LIMIT = 1.0
YAW_LOWER_LIMIT = -1.0
ELEVATOR_UPPER_LIMIT = 1.0
ELEVATOR_LOWER_LIMIT = -1.0
        
def txCallback(dest, packet):
    global xb
    xb.tx(dest_addr = dest, data = packet)
    
def loop():

    DEFAULT_COM_PORT = 'COM7'
    DEFAULT_BAUD_RATE = 57600
    DEFAULT_ADDRESS = '\x10\x21'
    DEFAULT_PAN = '\x10\x01'
    
    
    if len(sys.argv) == 1:
        com = DEFAULT_COM_PORT
        baud = DEFAULT_BAUD_RATE
        addr = DEFAULT_ADDRESS
    elif len(sys.argv) == 4:
        com = sys.argv[1]
        baud = int(sys.argv[2])
        addr = pack('>H', int(sys.argv[3], 16))
    else:
        print "Wrong number of arguments. Must be: COM BAUD ADDR"
        sys.exit(1)
                
    coord = CommandInterface(addr, txCallback)
    coord.enableDebug()
    
    ser = Serial(port = com, baudrate = baud) 
    xb = XBee(ser)
    print "Setting PAN ID to " + hex(DEFAULT_PAN)
    xb.at(command = 'ID', parameter = pack('>H', DEFAULT_PAN))         
    
    thrust = 0.0
    yaw = 0.0
    elevator = 0.0
    
    while True:
        
        try:                    
            
            c = msvcrt.getch()
            
            if c == 'w':
                thrust = thrust + THRUST_INCREMENT
            elif c == 'a':
                yaw = yaw + YAW_INCREMENT                
            elif c == 's':
                thrust = thrust - THRUST_INCREMENT
            elif c == 'd':
                yaw = yaw - YAW_INCREMENT                
            elif c == 'r':
                elevator = elevator + ELEVATOR_INCREMENT
            elif c == 'f':
                elevator = elevator - ELEVATOR_INCREMENT
            elif c == 'q':
                thrust = 0.0
                yaw = 0.0
                elevator = 0.0
            elif c == 'e':
                break
            elif c == 't':
                coord.setRegulatorMode(RegulatorStates['Remote Control'])            
                
            if thrust > THRUST_UPPER_LIMIT:
                thrust = THRUST_UPPER_LIMIT
            elif thrust < THRUST_LOWER_LIMIT:
                thrust = THRUST_LOWER_LIMIT
                
            if yaw > YAW_UPPER_LIMIT:
                yaw = YAW_UPPER_LIMIT
            elif yaw < YAW_LOWER_LIMIT:
                yaw = YAW_LOWER_LIMIT
            
            if elevator > ELEVATOR_UPPER_LIMIT:
                elevator = ELEVATOR_UPPER_LIMIT
            elif elevator < ELEVATOR_LOWER_LIMIT:
                elevator = ELEVATOR_LOWER_LIMIT
            
            coord.setRemoteControlValues(thrust, yaw, elevator)
            
        except:
        
            print "Exception: ", sys.exc_info()[0]
            break
                    
    xb.halt()
    ser.close()

if __name__ == '__main__':

    try:
        loop()

    except:
        pass
        
