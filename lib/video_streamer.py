import threading, time, sys, msvcrt
from struct import *
from Tkinter import *
from PIL import Image, ImageDraw
from ImageWin import Dib, HWND
from serial import *
from xbee import XBee
from payload import Payload
from telemetry_reader import TelemetryReader
from dictionaries import *
from command_interface import CommandInterface


class WindowManager(threading.Thread):
    
    def __init__(self, targetWindow):
        threading.Thread.__init__(self)
        self.window = targetWindow
        
    def run(self):
        self.window.mainloop()
        
#end class

class ImageView(Frame):

    def __init__(self, master, **options):
        Frame.__init__(self, master, **options)
        self.pack()
        self.dib = None

    def setimage(self, image):
        self.config(bg="") # don't update the background
        self.dib = Dib(image)
        self.dib.expose(HWND(self.winfo_id()))
            
#end class

class VideoStreamer(object):
    
    DEFAULT_DESTINATION = '\x11\x01'    
    INDICATOR_DECAY = 30
    
    def __init__(self, callback):
        self.tx_callback = callback
        
        # Transmitter Parameters
        self.block_size = 75

        # Image Parameters
        self.capture_width = 150
        self.capture_height = 120
        
        self.scale = 3
        self.hardware_col_subsample = 3
        self.hardware_row_subsample = 3
        
        self.dx = self.scale*self.hardware_col_subsample;
        self.dy = self.scale;
        
        self.display_width = self.capture_width * self.scale        
        self.display_height = self.capture_height * self.scale        
             
        # Radio parameters
        self.endpoint_addr = VideoStreamer.DEFAULT_DESTINATION
        
        # Viewer window
        self.root = Tk()
        self.stream = ImageView(self.root, width = self.display_width + self.dx, height = self.display_height)
        self.manager = WindowManager(self.root)
        self.manager.start()
        
        self.frame = Image.new('L',(self.display_width, self.display_height))
        self.cframe = Image.new('RGB',(self.display_width + self.dx, self.display_height))
        self.frame_array = self.frame.load()
        self.cframe_array = self.cframe.load()
        self.frame_draw = ImageDraw.Draw(self.cframe)

        # Other state
        self.lastFrame = 0		
        self.lastFrameTime = time.clock()
        
        print("capture width: " + str(self.capture_width) + " height: " + str(self.capture_height))
        print("Display width: " + str(self.display_width) + " height: " + str(self.display_height))
        print("Scale: " + str(self.scale))

    def save(self, filename):
        self.frame.save(filename + ".png", "PNG")
        
    def close(self):        
        pass
        
    def setEndpoint(self, addr):
        print "Setting endpoint address of: " + hex(unpack('>H', addr)[0])
        self.endpoint_addr = addr        
        
    def processPacket(self, packet):
        pld = Payload(packet.get('rf_data'))
        type = pld.type
        data = pld.data
        status = pld.status

        if type == Commands['RAW_FRAME_RESPONSE']:
            data_flag = str(self.block_size) + 'B'
            raw = unpack('HHH' + data_flag, data)

            frame_num = raw[0]
            row = raw[1]*self.hardware_row_subsample
            col = raw[2]
            pixels = raw[3::]
                              
            #print "Received row: " + str(row) + " col: " + str(col)
                              
            self.writeBlock(row, col, pixels)
            
        elif type == Commands['CENTROID_REPORT']:
            raw = unpack('4H2B', data)            
            self.mergeImages()
            self.drawCentroid(raw[0:2])
            self.drawMax(raw[2:4])
            print "Max lum: " + str(raw[4]) + " avg: " + str(raw[5])
            self.updateImage()           
            self.displayFrameRate()
            
            
        else:
            print "Invalid command: " + str(type)                                
                        
    def displayFrameRate(self):
        now = time.clock()
        rate = 1.0/(now - self.lastFrameTime)
        print "Framerate: " + str(rate) + " fps\n"
        self.lastFrameTime = now
        
    def writeBlock(self, row, col_start, data):
        #x = horizontal, y = vertical
        x_start = col_start*self.hardware_col_subsample*self.scale
        x_end = x_start + self.block_size*self.hardware_col_subsample*self.scale
        y_start = row*self.scale
        y_end = y_start + self.scale*self.hardware_row_subsample
        
        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                self.frame_array[x, y] = data[(x - x_start)/(self.hardware_col_subsample*self.scale)]
            
        # Write indicator pixels        
        for y in range(y_start, y_end):
            for x in range(0, self.dx):
                self.cframe_array[x, y] = 0x0000FF
            
    def drawCentroid(self, centroid):
        x_start = centroid[0]*self.dx;
        y_start = centroid[1]*self.dy*self.hardware_row_subsample;
        print "Centroid at: " + str(centroid)        
        for y in range(y_start, y_start + self.dy):            
            for x in range(x_start, x_start + self.dx):                
                self.cframe_array[x, y] = 0x0000FF
                
    def drawMax(self, max):
        x_start = max[0]*self.dx;
        y_start = max[1]*self.dy*self.hardware_row_subsample;
        print "Max at: " + str(max)        
        for y in range(y_start, y_start + self.dy):            
            for x in range(x_start, x_start + self.dx):                
                self.cframe_array[x, y] = 0x00FF00
    
                
    def mergeImages(self):
        self.cframe.paste(self.frame, [self.dx, 0, \
                    self.display_width + self.dx, self.display_height])        
            
    def updateImage(self):                
        self.stream.setimage(self.cframe)      
    
    def decayIndicators(self):
        for y in range(0, self.display_height - 1):            
            for x in range(0, self.dx):            
                pixel = self.cframe_array[x, y];                
                if pixel >= (self.INDICATOR_DECAY,0,0):
                    self.cframe_array[x, y] = (pixel[0] - self.INDICATOR_DECAY, 0, 0)
                else:
                    self.cframe_array[x, y] = (0, 0, 0)
        self.updateImage()
        
def txCallback(dest, packet):
    global xb
    xb.tx(dest_addr = dest, data = packet)
    
if __name__ == '__main__':

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
        
    streamer = VideoStreamer(txCallback)	
    reader = TelemetryReader(addr, txCallback)
    coord = CommandInterface(addr, txCallback)
    
    ser = Serial(port = com, baudrate = baud)
    xb = XBee(ser, callback = streamer.processPacket)
    print "Setting PAN ID to " + hex(DEFAULT_PAN)
    xb.at(command = 'ID', parameter = pack('>H', DEFAULT_PAN))
    
    streamer.setEndpoint(addr)    
    time.sleep(0.25)    

    #raw_input("Press any key to capture background frame.")
    #coord.setBackgroundFrame()
    
    prev_time = time.time()
    file_index = 0;
    
    while True:
        try:
            curr_time = time.time()
            if(curr_time - prev_time) > 4.0:
                coord.requestRawFrame()
                streamer.decayIndicators()
                prev_time = curr_time
                
            if msvcrt.kbhit():
                c = msvcrt.getch()
                if c == 'e':
                    print "Closing..."
                    break
                elif c == 'h':
                    coord.setHP(0)
                    print "High pass toggled."
                elif c == 'c':
                    streamer.save(str(file_index))
                    print "Image captured."
                    file_index = file_index + 1
                
            time.sleep(0.1)
                
        except:
           print "Exception: ", sys.exc_info()[0]
           break
            
    time.sleep(0.25)
    streamer.close()
    xb.halt()
    ser.close()
