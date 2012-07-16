import time, sys, random
from struct import *
from serial import *
from xbee import XBee
from payload import Payload
from dictionaries import *
import threading

# Bootloader constants
BOOTLOADER_SERVER_ADDR = 0x1020
BOOTLOADER_SERVER_PAN = 0x1000
BOOTLOADER_CLIENT_ADDR = 0x1101
BOOTLOADER_CLIENT_PAN = 0x1000
BOOTLOADER_CHANNEL = 0x15

# Network discovery/assignment constants
DISCOVERY_SERVER_ADDR = 0x1020
DISCOVERY_SERVER_PAN = 0x1001
DISCOVERY_CLIENT_ADDR = 0x1101
DISCOVERY_CLIENT_PAN = 0x1001
DISCOVERY_CHANNEL = 0x15 # Not the TV channel...

# Active formation network constants
# Currently the same as the discovery network due to XBee
# PAN addressing limitations
ACTIVE_SERVER_ADDR = 0x1020
ACTIVE_SERVER_PAN = 0x1001
ACTIVE_CLIENT_PAN = 0x1001
ACTIVE_CHANNEL = 0x15

BROADCAST_ADDRESS = '\xFF\xFF'

# TODO: Make compatible with abuchan's AsynchDispatch 

class NetworkCoordinator(object):

    client_entry_template = {'UUID':0, 'Status':'Closed', 'Transaction ID':0,
        'Address':"\x00\x00", 'PAN':"\x00\x00", 'Channel':"\x15", 
        'Basestation Address':"\x00\x00", 'Basestation Pan':"\x00\x00",
        'Timestamp':0}
    client_statuses = ['Offer Sent', 'Assigned', 'Assigned to Other', 'Closed']

    def __init__(self, callback):
    
        # Local address parameters
        self.localAddress = DISCOVERY_SERVER_ADDR
        self.localPAN = DISCOVERY_SERVER_PAN
        self.localChannel = DISCOVERY_CHANNEL
        
        # Assigning address parameters
        self.activeServerAddress = ACTIVE_SERVER_ADDR
        self.activeServerPAN = ACTIVE_SERVER_PAN
        #self.activeClientAddress is assigned dynamically
        self.activeClientPAN = ACTIVE_CLIENT_PAN
        self.activeChannel = ACTIVE_CHANNEL

        # Module state information
        self.lastAddress = self.activeServerAddress + 1
        self.lastTransaction = random.randint(0, 10000)
        self._running = False
        
        print "Starting network coordinator with transaction ID at: " + str(self.lastTransaction)
        
        # Initialize client dictionary and locks
        self.clients = {}	
        self.accessLock = threading.RLock()
        
        # TX Callback for modular use
        self.tx_callback = callback
        
    # Close the coordinator and free resources
    def close(self):        
        self.halt()
        print "Closing coordinator..."
        
    # Resume coordinator operation and service requests
    def resume(self):
        print "Resuming coordinator operation..."
        self.accessLock.acquire()
        self._running = True
        self.accessLock.release()
        
    # Halt request servicing operation
    def halt(self):
        print "Halting coordinator operation..."
        self.accessLock.acquire()
        self._running = False
        self.accessLock.release()
        
    # Return a shallow copy of the clients dictionary
    # Note that this safe for us since we don't store references	
    def getClients(self):
        accessLock.acquire()
        copy = self.clients.copy()
        accessLock.release()
        return copy
    
    # Process a packet asynchronously
    # This should be registered to AsynchDispatch in the future
    def processPacket(self, packet):
        
        # Don't process packets if coordinator function halted
        self.accessLock.acquire()
        if self._running == False:
            self.accessLock.release()
            return
        self.accessLock.release()
        
        type = packet['id']
        
        if type == 'rx_long_addr':
            #print "RX Long Addr type packet received."
            addr_data = (packet.get('source_addr'))[0:8]
            addr = unpack('>Q', addr_data)
            pld = Payload(packet.get('rf_data'))
            self._handleRx(addr, pld)
        
        elif type == 'rx':
            #print "RX type packet received."
            addr_data = (packet.get('source_addr'))[0:2]
            addr = unpack('>H', addr_data)
            pld = Payload(packet.get('rf_data'))
            self._handleRx(addr, pld)
        
        elif type == 'rx_io_data_long_addr':
            #print "RX IO Data Long Addr type packet received."
            addr_data = (packet.get('source_addr'))[0:2]
            addr = unpack('>Q', addr_data)
            self._handleOther(packet)
        
        elif type == 'rx_io_data':
            addr_data = (packet.get('source_addr'))[0:2]
            addr = unpack('>H', addr_data)
            pld = Payload(packet.get('rf_data'))
            addr = unpack('H', pld.data)
            self._handleOther(packet)
        
        elif type == 'tx_status':
            #print "TX Status type packet received."
            self._handleOther(packet)
        
        elif type == 'status':
            #print "Status type packet received."
            self._handleOther(packet)
        
        elif type == 'at_response':
            #print "AT Response type packet received."
            self._handleOther(packet)
        
        elif type == 'remote_at_response':
            #print "Remote AT Response type packet received."
            self._handleOther(packet)
            
        else:
            pass
            #print "Unknown packet type received."
            
    # Decode and process a RX packet
    def _handleRx(self, addr, pld):
        status = pld.status
        type = pld.type
        data = pld.data
        
        if type == Commands['ADDRESS_REQUEST']:
            print "Address Request received."
            client_uuid = unpack('Q', data)[0]
            self._handleAddressRequest(client_uuid)
            
        elif type == Commands['ADDRESS_OFFER']:
            print "Address Offer received."
            (client_uuid, transaction_id, address_offer, pan_offer, channel_offer) = \
            unpack('QIHHB', data)
            self._handleAddressOffer(client_uuid, transaction_id, address_offer, \
                pan_offer, channel_offer)
        
        elif type == Commands['ADDRESS_ACCEPT']:
            print "Address Accept received."
            (client_uuid, transaction_id) = unpack('QI', data)
            self._handleAddressAccept(client_uuid, transaction_id)
            
        else:
            pass
            #print "Invalid payload command of " + hex(type) + " received."
        
    # Decode and process an address request packet
    def _handleAddressRequest(self, client_uuid):
        self.accessLock.acquire()
        entry = self.clients.get(client_uuid)
        print "Searching for Client UUID: " + str(client_uuid) + "..."
        
        if(entry == None):
            print "New client. Generating offer..."
            
            transaction_id = self.lastTransaction
            address_offer = self.lastAddress
            pan_offer = self.activeClientPAN
            channel_offer = self.activeChannel
            
            basestation_address_offer = self.activeServerAddress
            basestation_pan_offer = self.activeServerPAN
            basestation_channel_offer = self.activeChannel
            
            timestamp = int(time.time())
            
            entry = {'UUID':client_uuid, 'Status':'Offer Sent', 'Transaction ID':transaction_id, \
                'Address':address_offer, 'PAN':pan_offer, 'Channel':channel_offer, \
                'Basestation Address':basestation_address_offer, 'Basestation PAN':basestation_pan_offer, \
                'Basestation Channel':basestation_channel_offer, 'Timestamp':timestamp}
            self.clients[client_uuid] = entry;
            
            # Increment transaction and address
            self.lastTransaction = self.lastTransaction + 1
            self.lastAddress = self.lastAddress + 1
            
            self._sendOffer(client_uuid, transaction_id, address_offer, pan_offer, \
                channel_offer, basestation_address_offer, basestation_pan_offer, \
                basestation_channel_offer, timestamp)
            self.accessLock.release()
            
        else:
            print "Old client. Resending offer..."
            
            transaction_id = entry['Transaction ID']
            address_offer = entry['Address']
            pan_offer = entry['PAN']
            channel_offer = entry['Channel']
            
            basestation_address_offer = entry['Basestation Address']
            basestation_pan_offer = entry['Basestation PAN']
            basestation_channel_offer = entry['Basestation Channel']
            
            # Update timestamp now that we are resending the offer
            timestamp = int(time.time())
            entry['Timestamp'] = timestamp
            
            self._sendOffer(client_uuid, transaction_id, address_offer, pan_offer, \
                channel_offer, basestation_address_offer, basestation_pan_offer, \
                basestation_channel_offer, timestamp)
            self.accessLock.release()

    # Decode and process an address offer
    def _handleAddressOffer(self, client_uuid, transaction_id, address, pan, channel):
        # Nothing to do yet, perhaps coordinator multiple servers in future?
        pass
        
    # Decode and process an address acceptance
    def _handleAddressAccept(self, client_uuid, transaction_id):

        # Search for client entry in directory using UUID
        entry = self.clients.get(client_uuid)
        print "Searching for Client UUID: " + str(client_uuid) + "..."
        
        if entry == None:
            # If no entry found, consider it a bogus acceptance and ignore
            print "Client not found. Invalid acceptance."
        
        else:
            # If an entry is found, verify the transaction ID
            offer_ID = entry['Transaction ID']
            
            if offer_ID == transaction_id:
                # Matching ID means client accepted local offer
                print "Transaction ID match. Address assignment complete."
                entry['Status'] = 'Assigned'
                self.sendDirectory();
            
            else:
                # Non-matching ID means client accepted another server's offer
                print "Transaction ID mismatch. Address assignment completed by \
                    other coordinator."
                entry['Status'] = 'Assigned to Other'

    # Decode and process non request, offer, and acceptance packets
    def _handleOther(self, packet):
        # Nothing to do here
        pass
        
    # Broadcast a directory update on the active PAN
    # TODO: Switch trasnceiver to active PAN and back to discovery PAN
    def sendDirectory(self):
        print "Broadcasting directory"
        data_strings = []
        keySet = self.clients.keys()
        data_pack = ''
        bytes = 0
        
        for key in keySet:
            entry = self.clients[key]
            if entry['Status'] != 'Assigned':
                continue            
            new_data = pack('QLH', entry['UUID'], entry['Timestamp'], entry['Address'])                
            print "Packing: " + str(entry['UUID']) + "\t" + hex(entry['Address']) + "\t" + str(entry['Timestamp'])
            data_pack = data_pack + new_data
            bytes = bytes + len(new_data)
            # If the next pack would cause packet to exceed size, delimit 
            if bytes + len(new_data) > 100:
                data_strings.append(data_pack)
                data_pack = ''
                bytes = 0
        
        # Catch undelimited data
        if bytes != 0:
            data_strings.append(data_pack)
            
        # Send all data
        for data in data_strings:
            print "Sending directory update packet..."
            pld = Payload(data = data, status = 0, type = Commands['DIR_UPDATE_RESPONSE'])
            self.tx_callback(dest = BROADCAST_ADDRESS, packet = str(pld))
    
    # Broadcast an address offer on the discovery PAN
    def _sendOffer(self, client_uuid, transaction_id, address_offer, pan_offer, channel_offer, \
        basestation_addr_offer, basestation_pan_offer, basestation_channel_offer, timestamp):
    #def _sendOffer(self, entry):        
    
        print "\n\tTransaction ID: " + str(transaction_id) + "\n\tOffering Address: " + \
            hex(address_offer) + "\n\tPAN: " + hex(pan_offer) + "\n\tChannel Offer: " + \
            hex(channel_offer) + "\n\tBasestation Address: " + hex(basestation_addr_offer) + \
            "\n\tBasestation PAN: " + hex(basestation_pan_offer) + "\n\tBasestation Channel: " + \
            hex(basestation_channel_offer) + "\n\tTimestamp: " + str(timestamp) + \
            "\n\tTo client: " + hex(client_uuid)
        
        data_pack = pack('QIHHHHHHL', client_uuid, transaction_id, \
            address_offer, pan_offer, channel_offer, basestation_addr_offer, \
            basestation_pan_offer, basestation_channel_offer, timestamp)
            
        pld = Payload(data_pack, 0, Commands['ADDRESS_OFFER'])

        self.tx_callback(dest = BROADCAST_ADDRESS, 
                packet = str(pld))
    
def txCallback(dest, packet):
    global xb
    xb.tx(dest_addr = dest, data = packet)
    
# Standalone mode uses all default values
if __name__ == '__main__':

    DEFAULT_COM_PORT = 'COM21'
    DEFAULT_BAUD_RATE = 115200
    DEFAULT_ADDR = 0x1020
    DEFAULT_UPDATE_RATE = 0.1 # Directory broadcast rate in hertz
    
    if len(sys.argv) == 1:
        com = DEFAULT_COM_PORT
        baud = DEFAULT_BAUD_RATE
    elif len(sys.argv) == 3:
        com = sys.argv[1]
        baud = int(sys.argv[2])
                
    networkcoordinator = NetworkCoordinator(txCallback)
    
    ser = Serial(port = com, baudrate = baud)
    xb = XBee(ser, callback = networkcoordinator.processPacket)
    
    print "Setting Local Address to " + hex(networkcoordinator.localAddress)
    xb.at(command = 'MY', parameter = pack('>H', networkcoordinator.localAddress))
    print "Setting PAN ID to " + hex(networkcoordinator.localPAN)
    xb.at(command = 'ID', parameter = pack('>H', networkcoordinator.localPAN))
    
    networkcoordinator.resume()
    
    sleepTime = 1.0/DEFAULT_UPDATE_RATE
    
    while True:
        try:
            time.sleep(sleepTime)
            networkcoordinator.sendDirectory()
        except:            
            networkcoordinator.close()
            break
    xb.halt()
    ser.close()
    