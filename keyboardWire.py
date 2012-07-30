import time, sys, msvcrt
from struct import *
from serial import *
from math import *
from xbee import XBee
from lib.dictionaries import *
from lib.command_interface import CommandInterface
from lib.telemetry_reader import TelemetryReader
from lib.network_coordinator import NetworkCoordinator
from lib.quaternion import *

class IncrementCounter(object):
    
    def __init__(self, start_value = 0, range = (-1.0, 1.0), increment = 0.1):
        self.val = start_value
        self.lower_bound = min(range)
        self.upper_bound = max(range)
        self.increment = increment
        
    def value(self):
        return self.val
        
    def increase(self):
        self.val = self.val + self.increment
        self.__enforceRange()
        
    def decrease(self):
        self.val = self.val - self.increment
        self.__enforceRange()
        
    def set(self, val):
        self.val = val
        self.__enforceRange()
        
    def __enforceRange(self):
        if self.val > self.upper_bound:
            self.val = self.upper_bound
        elif self.val < self.lower_bound:
            self.val = self.lower_bound
        
class KeyboardInterface(object):
    
    def __init__(self, comm_interface = None):
        self.comm = comm_interface
        # Attitude state
        self.yaw = IncrementCounter( start_value = 0.0, range = (180.0, -180.0), increment = 45.0 )
        self.pitch = IncrementCounter( start_value = 0.0, range = (90.0, -90.0), increment = 10.0 )    
        self.roll = IncrementCounter( start_value = 0.0, range = (180.0, -180.0), increment = 10.0)
        # Slew state
        self.yaw_rate = IncrementCounter( start_value = 0.0, range = (10.0, -10.0), increment = 0.25 )
        self.pitch_rate = IncrementCounter( start_value = 0.0, range = (10.0, -10.0), increment = 0.25 )
        self.roll_rate = IncrementCounter( start_value = 0.0, range = (10.0, -10.0), increment = 0.25 )    
        # Actuator state
        self.elevator = IncrementCounter( start_value = 0.0, range = (1.0, -1.0), increment = 0.2 )
        self.thrust = IncrementCounter( start_value = 0.0, range = (1.0, 0.0), increment = 0.025 )
        self.steer = IncrementCounter( start_value = 0.0, range = (1.0, -1.0), increment = 0.05 )        
        # PID constants        
        self.yaw_coeffs = [ 0.0,    0.0,    -2.0,   -0.8,    -0.4,    1.0,    1.0] # For steer Ki 0.8
        self.pitch_coeffs = [ 0.0,    0.0,    3.0,   0.0,    0.2,    1.0,    1.0] # For elevator
        self.roll_coeffs = [ 0.0,    0.0,    -0.2,   0.0,    0.0,    1.0,    1.0] # For thrust 
        self.yaw_filter_coeffs = [ 3, 0, 0.0007, 0.0021, 0.0021, 0.0007, 1.0, 2.6861573965, -2.419655111, 0.7301653453]
        # self.yaw_filter_coeffs = [ 3, 0, 56.0701e-6, 168.2103e-6, 168.2103e-6, 56.0701e-6, 1, -2.8430, 2.6980, -0.8546]
        # State                               
        self.streaming = False
        self.rate_control = False
        self.rc_changed = False
        self.offsets_changed = False
        self.ref_changed = False
        self.rate_changed = False    
        self.pinging = False        
        
    def process(self, c):
    
        if c != None:
            self.__handleKey(c)
            
        if self.pinging:
            self.comm.sendPing();                
            
    def __handleKey(self, c):
            
        # Reference commands
        if c == 'w':
            self.pitch.increase()
            # self.comm.rotateRefLocal(quatGenerate(radians(10), (0,1,0)))
            self.ref_changed = True
        elif c == 's':
            self.pitch.decrease()
            # self.comm.rotateRefLocal(quatGenerate(radians(-10), (0,1,0)))
            self.ref_changed = True
        elif c == 'a':
            # self.yaw.decrease()
            # self.ref_changed = True
            # self.comm.rotateRefGlobal(quatGenerate(radians(-10), (0,0,1)))
            self.yaw_rate.decrease()                
            self.rate_changed = True
        elif c == 'd':
            # self.yaw.increase()
            # self.ref_changed = True
            # self.comm.rotateRefGlobal(quatGenerate(radians(10), (0,0,1)))
            self.yaw_rate.increase()            
            self.rate_changed = True
        elif c == 'q':
            self.roll.increase()
            self.ref_changed = True
        elif c == 'e':
            self.roll.decrease()
            self.ref_changed = True
        # Telemetry commands        
        elif c == 'r':                
            self.comm.startSensorDump(1)          
        elif c == 'f':                
            self.comm.startSensorDump(0)
        elif c == 'v':
            self.comm.requestDumpData(0x80 + 0, 0x80 + 600, 66)            
        elif c == 't':
            self.comm.requestTelemetry()        
        elif c == 'y':
            self.streaming = not self.streaming
            #telem.writeLine("-> Toggle Streaming\n")                
        # Regulator Modes
        elif c == '1':                
            self.comm.setRegulatorMode(RegulatorStates['Off'])
        elif c == '2':                
            self.comm.setRegulatorMode(RegulatorStates['Stabilize'])
        elif c == '3':                
            self.comm.setRegulatorMode(RegulatorStates['Remote Control'])                    
        elif c == '4':
            self.rate_control = not self.rate_control           
            self.comm.setRateMode(self.rate_control)                        
        elif c == '0':
            #self.pinging = not self.pinging
            self.comm.setRegulatorRef((1.0, 0.0, 0.0, 0.0))
            
        # Attitude
        elif c == 'c':
            self.comm.runGyroCalib(1000);            
        elif c == 'z':
            self.comm.zeroEstimate()                                  
        # Configuration
        elif c == 'p':                
            self.comm.setRegulatorPid( self.yaw_coeffs + self.pitch_coeffs + self.roll_coeffs )                                
            self.comm.setRegulatorRateFilter( self.yaw_filter_coeffs )
            self.comm.setTelemetrySubsample(1)
        elif c == ']':
            self.thrust.increase()
            self.offsets_changed = True                        
        elif c == '[':
            self.thrust.decrease()
            self.offsets_changed = True            
        elif c == '\x1b': #Esc key
            #break
            raise Exception('Exit')
        
        if self.rc_changed:        
            self.comm.setRemoteControlValues( self.thrust.value(), self.steer.value(), self.elevator.value() );             
            self.rc_changed = False
            
        if self.offsets_changed:
            self.comm.setRegulatorOffsets((self.steer.value(), self.elevator.value(), self.thrust.value()))
            self.offsets_changed = False
            
        if self.rate_changed:
            self.comm.setGlobalRateSlew( ( self.yaw_rate.value(), self.pitch_rate.value(), self.roll_rate.value() ) )
            self.rate_changed = False
        
        if self.ref_changed:                    
            print   "Yaw, Pitch, Roll: " + str(self.yaw.value()) + " " + \
                    str(self.pitch.value()) + " " + str(self.roll.value())
            self.comm.setRegulatorRef( eulerToQuaternionDeg( self.yaw.value(), self.pitch.value(), self.roll.value() ) )        
            self.ref_changed = False
            
    

def txCallback(dest, packet):
    global xb
    xb.tx(dest_addr = dest, data = packet)    
    
def rxCallback(packet):
    global telem, coord
    telem.processPacket(packet)
    coord.processPacket(packet)
    
def loop():

    global xb, telem, coord

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
    else:
        print "Wrong number of arguments. Must be: COM BAUD ADDR"
        sys.exit(1)
    
    ser = Serial(port = com, baudrate = baud) 
    xb = XBee(ser, callback = rxCallback)
    print "Setting PAN ID to " + hex(DEFAULT_PAN)
    xb.at(command = 'ID', parameter = pack('>H', DEFAULT_PAN))                 
    
    comm = CommandInterface(addr, txCallback)
    telem = TelemetryReader(addr, txCallback)
    kbint = KeyboardInterface(comm)
    coord = NetworkCoordinator(txCallback)
    
    comm.enableDebug()
    telem.setConsoleMode(True)
    telem.setFileMode(True)
    telem.writeHeader()
    coord.resume()
    
    comm.setSlewLimit(3.0)
    
    while True:

        try:
            c = None
            if( msvcrt.kbhit() ):
               c = msvcrt.getch()
            kbint.process(c)
            time.sleep(0.01)
            #comm.sendPing()

        except:        
            break
            
    telem.close()                
    xb.halt()
    ser.close()
    

if __name__ == '__main__':
    
    try:        
        loop()
        
    except Exception as e:
        print e
        
    finally:
        #Add cleanup code!
        pass