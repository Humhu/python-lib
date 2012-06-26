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

    def getGyroCalibParam(self):
        data_pack = pack('H', 0)
        if self.debugPrint:
            print "Requesting gyro offsets..."
        pld = Payload(data = data_pack, status = 0, type = Commands['GET_GYRO_CALIB_PARAM'])
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
        
    def setRegulatorRef(self, ref):
        data_pack = pack(3*'f', *ref)
        if self.debugPrint:
            print "Setting [yaw, pitch, roll] references to " + str(ref) + " radians."
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_REGULATOR_REF'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def setRegulatorPid(self, coeffs):
        data_pack = pack(3*'7f', *coeffs)
        if self.debugPrint:
            print "Setting yaw PID coefficents of " + str(coeffs)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_REGULATOR_PID'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def setRegulatorRateFilter(self, order, filter_coeffs):    
        data_pack = pack(3*'2B8f', *filter_coeffs)
        if self.debugPrint:
            print "Setting " + str(order) + "-order yaw filter coefficients of " + str(filter_coeffs)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_REGULATOR_RATE_FILTER'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
            
    def setEstimateRunning(self, mode):
        data_pack = pack('B', mode)
        if self.debugPrint:
            print "Setting pose estimation mode to: " + str(mode)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_ESTIMATE_RUNNING'])
        self.tx_callback(dest = self.endpoint_addr, packet = str(pld))
    
    def setRegulatorState(self, flag):        
        data_pack = pack('B', flag)
        if self.debugPrint:
            print "Setting regulator state to " + str(flag)
        pld = Payload(data = data_pack, status = 0, type = Commands['SET_REGULATOR_STATE'])
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
        
    def processPacket(self, packet):
        print "Hi!"
        pass
    