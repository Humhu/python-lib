#!/usr/bin/env python

import time, sys, math
from struct import *
from serial import *
from xbee import XBee
from payload import Payload
from dictionaries import *

class CommandInterface(object):

    def __init__(self, address, callback):
        self.endpoint_addr = address
        self.tx_callback = callback
        self.debugPrint = False
        
    def close(self):
        pass
        
    def enableDebug(self):
        self.debugPrint = True
    
    def disableDebug(self):
        self.debugPrint = False

    def runGyroCalib(self, samples):
        data_pack = pack('H', samples)
        if self.debugPrint:
            print "Requesting gyro calibration of " + str(samples) + " samples."           
        pld = Payload(data = data_pack, status = 0, type = Commands['RUN_GYRO_CALIB'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
        
    def getGyroCalibParam(self):
        data_pack = pack('H', 0)
        if self.debugPrint:
            print "Requesting gyro offsets..."
        pld = Payload(data = data_pack, status = 0, type = Commands['GET_GYRO_CALIB_PARAM'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))

    def setTelemetrySubsample(self, period):
        data_pack = pack('H', period)
        if self.debugPrint:
            print "Setting telemetry subsample period to " + str(period)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_TELEM_SUBSAMPLE'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
        
    def startSensorDump(self, datasets):
        data_pack = pack('H', datasets)
        if self.debugPrint:
            print "Requesting " + str(datasets) + " samples to be written to flash."
        pld = Payload(data = data_pack, status = 0, type = Commands['RECORD_SENSOR_DUMP'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def requestDumpData(self, start_page, end_page, tx_size):
        data_pack = pack('3H', start_page, end_page, tx_size)
        if self.debugPrint:
            print "Requesting memory from page " + str(start_page) + " to " + str(end_page) +\
                  ", " + str(tx_size) + " bytes at a time."
        pld = Payload(data = data_pack, status = 0, type = Commands['GET_MEM_CONTENTS'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def requestRawFrame(self):
        data_pack = pack('L', 0)
        if self.debugPrint:
            print "Requesting raw frame."
        pld = Payload(data = data_pack, status = 0, type = Commands['RAW_FRAME_REQUEST'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def requestTelemetry(self):
        data_pack = pack('L', 0)
        if self.debugPrint:
            print "Requesting telemetry."
        pld = Payload(data = data_pack, status = 0, type = Commands['REQUEST_TELEMETRY'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def setBackgroundFrame(self):
        data_pack = pack('L', 0)
        if self.debugPrint:
            print "Capturing and setting background frame."
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_BACKGROUND_FRAME'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
        
    def rotateRefGlobal(self, rotation):
        data_pack = pack(4*'f', *rotation)
        if self.debugPrint:
            print "Applying rotation to reference in global axes: " + str(rotation)
        pld = Payload(data = data_pack, status = 0, type = Commands['ROTATE_REF_GLOBAL'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
        
    def rotateRefLocal(self, rotation):
        data_pack = pack(4*'f', *rotation)
        if self.debugPrint:
            print "Applying rotation to reference in local axes: " + str(rotation)
        pld = Payload(data = data_pack, status = 0, type = Commands['ROTATE_REF_LOCAL'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
        
        
    def setRegulatorOffsets(self, offsets):
        data_pack = pack(3*'f', *offsets)
        if self.debugPrint:
            print "Setting offsets to: " + str(offsets)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_REGULATOR_OFFSETS'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
        
    def setRegulatorRef(self, ref):
        data_pack = pack(4*'f', *ref)
        if self.debugPrint:
            print "Setting quaternion reference to: " + str(ref)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_REGULATOR_REF'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def setRegulatorPid(self, coeffs):
        data_pack = pack(3*'7f', *coeffs)
        if self.debugPrint:
            print ("Setting PID coefficents to: \n" + \
                    "\tOffset Kp Ki Kd\n" + \
                    "Yaw: " + str(coeffs[1:5]) + "\n" + \
                    "Pitch: " + str(coeffs[8:12]) + "\n" + \
                    "Roll: " + str(coeffs[15:19]))
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_REGULATOR_PID'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def setRegulatorRateFilter(self, filter_coeffs):    
        data_pack = pack('2H8f', *filter_coeffs)
        if self.debugPrint:
            print "Setting filter coefficients of " + str(filter_coeffs)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_REGULATOR_RATE_FILTER'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
            
    def setRateMode(self, flag):
        data_pack = pack('B', flag)
        if self.debugPrint:
            print "Setting rate mode to: " + str(flag)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_RATE_MODE'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def setGlobalRateSlew(self, rate):
        data_pack = pack('3f', *rate)
        if self.debugPrint:
            print "Setting rate slew to: " + str(rate)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_RATE_SLEW'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    
    def setEstimateRunning(self, mode):
        data_pack = pack('B', mode)
        if self.debugPrint:
            print "Setting pose estimation mode to: " + str(mode)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_ESTIMATE_RUNNING'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def setRegulatorMode(self, flag):        
        data_pack = pack('B', flag)
        if self.debugPrint:
            print "Setting regulator state to " + str(flag)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_REGULATOR_MODE'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def setRemoteControlValues(self, thrust, steer, elevator):        
        data_pack = pack('3f', thrust, steer, elevator)
        if self.debugPrint:
            print "Setting RC values to thrust: " + str(thrust) + "\tsteer: " + str(steer) + \
                    "\televator: " + str(elevator)
        pld = Payload (data = data_pack, status = 0, type = Commands['SET_RC_VALUES'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def getTelemetryData(self):
        data_pack = pack('H', 0)
        if self.debugPrint:
            print "Requesting telemetry data..."
        pld = Payload(data = data_pack, status = 0, type = Commands['REQUEST_TELEMETRY'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def sendPing(self):
        data_pack = pack('H', 0)
        if self.debugPrint:
            print "Pinging..."
        pld = Payload(data = data_pack, status = 0, type = Commands['PING'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def sendEcho(self):
        data_pack = pack('H', 0)
        if self.debugPrint:
            print "Requesting echo..."
        pld = Payload(data = data_pack, status = 0, type = Commands['ECHO'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
        
    def requestCamParams(self):
        data_pack = pack('H', 0)
        if self.debugPrint:
            print "Requesting camera parameters..."
        pld = Payload(data = data_pack, status = 0, type = Commands['CAM_PARAM_REQUEST'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
        
    def requestDirDump(self, addr, pan):
        data_pack = pack('HH', addr, pan)
        if self.debugPrint:
            print "Requesting directory dump of: " + str(addr) + " " + str(pan)
        pld = Payload(data = data_pack, status = 0, type = Commands['DIR_DUMP_REQUEST'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))

    def setHP(self, flag):
        data_pack = pack('H', flag)
        if self.debugPrint:
            print "Setting high pass to " + str(flag)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_HP'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))

    def zeroEstimate(self):
        data_pack = pack('H', 0)
        if self.debugPrint:
            print "Zeroing attitude estimate."
        pld = Payload(data = data_pack, status = 0, type = Commands['ZERO_ESTIMATE'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
        
    def requestAttitude(self):
        data_pack = pack('H', 0)
        if self.debugPrint:
            print "Requesting attitude."
        pld = Payload(data = data_pack, status = 0, type = Commands['REQUEST_ATTITUDE'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))

    def setSlewLimit(self, limit):
        data_pack = pack('f', limit)
        if self.debugPrint:
            print "Setting slew rate limit to: " + str(limit) + " radians/sec."
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_SLEW_LIMIT'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
                
    def processPacket(self, packet):
        print "Command interface objects don't need to process packets."
        pass
    