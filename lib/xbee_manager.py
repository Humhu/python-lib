# XBee wrapper class
# @author Humphrey Hu
# @date 7/26/2012

import threading
from serial import *
from xbee import XBee
from Queue import *
from struct import *

class XBeeManager(threading.Thread):

    def __init__(self, com, baud):
        threading.Thread.__init__(self)
        self.initialized = False
        self.running = False
        self.tx_fifo = Queue(100)
        self.rx_fifo = Queue(100)
        self.ser = None
        self.xb = None
        try:
            self.ser = Serial(port = com, baudrate = baud)
            self.xb = XBee(self.ser, self._rx_callback)
        except Exception as e:
            print "Exception in XBeeManager initialization:"
            print e
            self._cleanup()
            return     
        self.initialized = True   

    def run(self):
        if not self.initialized:
            return
        self.running = True
        while self.running:        
            try:
                (dest, packet) = self.tx_fifo.get(False, 1.0) # 1 second timeout
                self.xb.tx(dest_addr = dest, data = packet)
            except Empty:
                pass
            except Exception as e:
                print "Exception in XBeeManager main loop:"
                print e
                break
        
        self._cleanup()
        print "XBee Manager has terminated."            

    def isInitialized(self):
        return self.initialized

    def setAddress(self, addr, pan):
        if not self.initialized:
            print "Cannot set address - module not initialized"
            return
        print "Setting addr: " + hex(addr) + " pan: " + hex(pan)
        self.xb.at(command = 'MY', parameter = pack('>H', addr))
        self.xb.at(command = 'ID', parameter = pack('>H', pan)) 

    def putTxPacket(self, dest, packet):
        if not self.initialized:
            return
        
        try:
            self.tx_fifo.put_nowait((dest, packet))
        except Full:
            print "XB transmit buffer full!"

    def hasRxPacket(self):
        if not self.initialized:
            return False
        return not self.rx_fifo.empty()

    def getRxPacket(self, packet):
        if not self.initialized:
            return None
        try:
            packet = self.rx_fifo.get_nowait()
        except Empty:
            packet = None
        return packet

    def close(self):
        self.running = False

    def _rx_callback(self, packet):     
        try:   
            self.rx_fifo.put_nowait(packet)
        except Full:
            print "XB receive buffer full!"

    def _cleanup(self):
        if self.xb != None:
            print "Halting XBee."
            self.xb.halt()
        if self.ser != None:
            print "Closing COM port."
            self.ser.close()
