import time, sys
from struct import *
from serial import *
from xbee import XBee
from lib.payload import Payload
from lib.commandinterface import CommandInterface

reception_begun = False
done = False
num_received = 0

number_expected = 0
received = set()


def txCallback(dest, packet):
    global xb
    xb.tx(dest_addr = dest, data = packet)
    
def processPacket(packet):
    global reception_begun, rec, done, num_received, num_expected, received
    
    pld = Payload(packet.get('rf_data'))
    type = pld.type
    data = pld.data
    
    if(type == 0x10):
        reception_begun = True
        num_received += 1;
        num_dat = unpack('H', data[0:2])
        num = num_dat[0]
        print "Received packet number: " + str(num_received) + " data: " + str(num)
        received.add(num)
        if(num >= number_expected):
            print "All packets received."
            done = True
    else:
        print "Invalid packet type of: " + hex(type)
            
def calculateResults():
    global number_expected, number_received
    
    number_missing = 0
    greatest = 0
    for i in range(1, number_expected + 1):
        if i in received:
            greatest = i
        else:
            number_missing += 1
    number_received = number_expected - number_missing            
    success_chance = float(number_received)/number_expected*100
    
    print ("Success rate: " + str(success_chance) + "% (" + str(number_received) +
            "/" + str(number_expected) +") received.")

if __name__ == '__main__':

    global num_expected, done, reception_begun

    DEFAULT_COM_PORT = 'COM7'
    DEFAULT_BAUD_RATE = 115200
    DEFAULT_SOURCE = 0x1020
    DEFAULT_DESTINATION = '\xff\xff'
    DEFAULT_PAN = 0x1001
    DEFAULT_ITERS = 200
    DEFAULT_SIZE = 10
    
    if len(sys.argv) == 1:
        com = DEFAULT_COM_PORT
        baud = DEFAULT_BAUD_RATE
        addr = DEFAULT_DESTINATION
        iters = DEFAULT_ITERS
        size = DEFAULT_SIZE
    elif len(sys.argv) == 6:
        com = sys.argv[1]
        baud = int(sys.argv[2])
        addr = pack('>H', int(sys.argv[3], 16))
        iters = int(sys.argv[4])
        size = int(sys.argv[5])
    else:
        print ("Wrong number of arguments. Must be: COM BAUD ADDR ITERS SIZE")
        sys.exit(1)
           
    # Enable XBee
    ser = Serial(port = com, baudrate = baud)
    xb = XBee(ser, callback = processPacket)
    print "Setting PAN ID to " + hex(DEFAULT_PAN)
    xb.at(command = 'ID', parameter = pack('>H', DEFAULT_PAN))
    print("Setting local address to " + hex(DEFAULT_SOURCE))
    xb.at(command = 'MY', parameter = pack('>H', DEFAULT_SOURCE))
    
    raw_input("Press any key to begin test...")
    
    number_expected = iters
    
    data_pack = pack('HH', iters, size)
    pld = Payload(data = data_pack, status = 0, type = 0x10)
    
    try:
        while(reception_begun == False):
            txCallback(dest = addr, packet = str(pld))
            time.sleep(1)
        while(done == False):
            time.sleep(1)
        #calculateResults()
    finally:
        calculateResults()
        xb.halt()
        ser.close()
    
    
    