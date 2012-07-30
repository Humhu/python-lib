import time, sys, math, datetime
from struct import *
from serial import *
from xbee import XBee
from payload import Payload
from dictionaries import *
from command_interface import CommandInterface
from quaternion import *
from bams import *

class TelemetryReader(object):

    def __init__(self, address, callback):
        
        # TX Callback for modular use
        self.tx_callback = callback;
        self.endpoint_addr = address;
        self.fprint = False;
        self.cprint = False;
        self.file = None;
        
        self.last_packet_time = time.time()
        self.packets_received = 0
            
    def setConsoleMode(self, mode):
        print "Settinng console write mode to: " + str(mode)
        self.cprint = mode
    
    def setFileMode(self, mode):
        print "Setting file write mode to: " + str(mode)
        self.fprint = mode;
        if((mode == True) & (self.file == None)):
            today = datetime.datetime.today()
            d = str(today.year) + "_" + str(today.month) + "_" + str(today.day)
            t = str(today.hour) + "_" + str(today.minute) + "_" + str(today.second)
            fname = d + '-' + t + '.txt'
            self.file = open(fname, 'w')
        
    def writeHeader(self):
        if(self.file != None):
            self.file.write("Timestamp\t")
            self.file.write("Ref\t\t\t")            
            self.file.write("Pose\t\t\t")            
            self.file.write("Err\t\t\t")            
            self.file.write("U\t\t\t")
            self.file.write("ED\tRSSI\n")
            
    def writeLine(self, str):
        if(self.file != None):
            self.file.write(str + '\n')
    
    def close(self):
        if(self.file != None):
            self.file.close()
            self.file = None
        
    def processPacket(self, packet):
                
        addr_data = (packet.get('source_addr'))[0:2]
        addr = (unpack('>H', addr_data))[0]
        
        if(addr_data != self.endpoint_addr):
            print "Incorrect source: " + str(addr)
            return
        
        try:
            self._decodePacket(packet)
            self.packets_received += 1;
            
            now = time.time()
            if(now - self.last_packet_time) == 0:
                frequency = 0.0
            else:
                frequency = 1.0/(now - self.last_packet_time)
            self.last_packet_time = now;
            
            if(self.cprint):
                print "Packets received: " + str(self.packets_received)
                print "Frequency of: " + str(frequency)
            
            
            
        except Exception as e:
            print e
        
    def _decodePacket(self, packet):
        
        pld = Payload(packet.get('rf_data'))
        type = pld.type
        data = pld.data                       
        
        if type == Commands['GET_MEM_CONTENTS']:
            
            if(len(data) != 22):                
                print 'Invalid GET_MEM_CONTENTS packet of length ' + str(len(data)) + '\n'
                return
            
            telemetryData = unpack('LL3h3hH', data)
            
            gyro_timestamp = telemetryData[0];
            xl_timestamp = telemetryData[1];                        
            gyro = telemetryData[2:5];            
            xl = telemetryData[5:8];
            sample_number = telemetryData[8];
            
            if (self.cprint == True):
                print("Sample number: " + str(sample_number))
                #print("Gyro data: " + str(gyro))
                #print("Gyro timestamp: " + str(gyro_timestamp))
                #print("Xl data: " + str(xl))
                #print("Xl timestamp: " + str(xl_timestamp))
            if (self.fprint == True) & (self.file != None):
                self.file.write(str(sample_number) + "\t")
                self.file.write(str(gyro[0]) + "\t")
                self.file.write(str(gyro[1]) + "\t")
                self.file.write(str(gyro[2]) + "\t")
                self.file.write(str(gyro_timestamp) + "\t")
                self.file.write(str(xl[0]) + "\t")
                self.file.write(str(xl[1]) + "\t")
                self.file.write(str(xl[2]) + "\t")
                self.file.write(str(xl_timestamp) + "\n")

        elif type == Commands['GET_GYRO_CALIB_PARAM']:
            
            if(len(data) != 12):
                print "Invalid GET_GYRO_CALIB_PARAM packet"
                return
            
            offsets = unpack('3f', data)
            
            if(self.cprint == True):
                print("Gyro offsets: " + str(offsets))
            if(self.fprint == True) & (self.file != None):
                self.file.write("Offsets:\t" + str(offsets) + "\n")
                
        elif type == Commands['RESPONSE_TELEMETRY']:
            
            if(len(data) != 66):
                print "Invalid RESPONSE_TELEMETRY packet of length " + str(len(data))
                return
                
            raw = unpack('4f4f4f3fL2B', data)
            
            ref = raw[0:4]
            x = raw[4:8]
            err = raw[8:12]
            u = raw[12:15]
            timestamp = raw[15]
            ed = raw[16]
            rssi = raw[17]
            # timestamp = raw[0]
            # ref = raw[1:5]
            # x = raw[5:9]
            # err = raw[9:13]
            # u = raw[13:16]
            
            euler = quaternionToEuler(x)
            
            if(self.cprint == True):
                print "Timestamp: " + str(timestamp)
                print "Ref: " + str(ref)
                print "X: " + str(x)                
                print "X Euler Yaw: " + str(degrees(euler[0])) + " Pitch: " + \
                        str(degrees(euler[1])) + " Roll: " + str(degrees(euler[2]))
                print "Err: " + str(err)
                print "U: " + str(u)
                print "ED: " + str(ed) + " RSSI: " + str(rssi)               
                
            if(self.fprint == True):
                self.file.write(str(timestamp) + "\t")
                self.file.write(str(ref[0]) + "\t" + str(ref[1]) + "\t" + \
                                str(ref[2]) + "\t" + str(ref[3]) + "\t")
                self.file.write(str(x[0]) + "\t" + str(x[1]) + "\t" + \
                                str(x[2]) + "\t" + str(x[3]) + "\t")                
                self.file.write(str(err[0]) + "\t" + str(err[1]) + "\t" + \
                                str(err[2]) + "\t" + str(err[3]) + "\t")
                self.file.write(str(u[0]) + "\t" + str(u[1]) + "\t" + \
                                str(u[2]) + "\t")
                self.file.write(str(ed) + "\t" + str(rssi) + "\n")
                
        elif type == Commands['RESPONSE_ATTITUDE']:
            if(len(data) != 16):
                print "Invalid RESPONSE_ATTITUDE packet of length " + str(len(data))
            raw = unpack('4f', data);
            
            if(self.cprint == True):
                print "Quat: " + str(raw)
            
        elif type == Commands['CAM_PARAM_RESPONSE']:
            
            if(len(data) != 12):
                print "Invalid CAM_PARAM_RESPONSE packet of length " + str(len(data))
                return
            
            raw = unpack('2BH2L', data)
            type = raw[0]
            active = raw[1]
            pad = raw[2]
            start = raw[3]
            period = raw[4]
            if(self.cprint == True):
                print("Type: " + str(type))
                print("Active: " + str(active))
                print("Start: " + str(start))
                print("Period: " + str(period))
                
        elif type == Commands['DIR_DUMP_RESPONSE']:
        
            if(len(data) != 24):
                print "Invalid DIR_DUMP_RESPONSE packet of length " + str(len(data))
                return
                
            (uuid, type, params, frame_period, \
             frame_start, timestamp, address, pan_id) = unpack('QHHLLLHH', data)
                        
            if(self.cprint == True):
                print("UUID: " + str(uuid))
                print("Type: " + str(type))
                print("Params: " + hex(params))
                print("Frame period: " + str(frame_period))
                print("Frame start: " + str(frame_start))
                print("Timestamp: " + str(timestamp))
                print("Address: " + hex(address) + " PAN: " + hex(pan_id) + "\n")
                
        elif type == Commands['SET_RC_VALUES']:
        
            if(len(data) != 8):
                print "Invalid SET_RC_VALUES packet of length " + str(len(data))
                return
                
            raw = unpack('2f', data)
            thrust = raw[0]
            steer = raw[1]
            
            if(self.cprint == True):
                print("Commanded thrust: " + str(thrust) + " steer: " + str(steer) + "\n")
            
        else:
            pass
            #print "Invalid command of: " + str(type)