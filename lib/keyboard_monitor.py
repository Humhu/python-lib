# Keyboard character getter
# @author Humphrey Hu
# @date 7/26/2012

import sys, tty, termios, threading
from Queue import Queue

# Adapted from code.activestate.com/recipes/134892/
class KeyboardMonitor(threading.Thread):

    def __init__(self):
        self.initialized = False
        try:
            threading.Thread.__init__(self)
            self.output_fifo = Queue(100) # size of 100 just in case        
            self.stdin_fd = sys.stdin.fileno()
            self.running = False
            self.escape_char = 'q' # Since we can't get KeyboardInterrupts anymore, always use q to quit for now
        except Exception as e:
            print e
            return        
        self.initialized = True
    
    # Call start() to begin thread execution, not run()
    def run(self):
        self.running = True
        self._configureKeyboard()

        while self.running:
            try:                    
                c = self._readKey()
                if c == self.escape_char: 
                    break
                self.output_fifo.put_nowait(c)
            except Full:
                print "Keyboard monitor buffer is full!"
                pass            
            except Exception as e:
                print e
                break

        self._restoreKeyboard() # Always cleanup
        print "Keyboard Monitor has terminated."

    def isInitialized(self):
        return self.initialized

    # Should be called on program completion
    def close(self):
        self.running = False # Not thread safe, should be an event instead

    def hasKey(self):
        if not self.initialized:
            return False
        return not self.output_fifo.empty()

    # Return empty character if error or empty
    def getCh(self):
        if not self.initialized:
            return ''
        try:
            c = self.output_fifo.get_nowait()
        except Empty:
            c = ''
        return c

    def _readKey(self):
        return sys.stdin.read(1)

    def _configureKeyboard(self):
        try:
            self.old_keyboard_settings = termios.tcgetattr(self.stdin_fd)
            tty.setraw(self.stdin_fd)
        except Exception as e:
            print "Could not configure keyboard settings:"
            print e

    def _restoreKeyboard(self):
        try:
            termios.tcsetattr(self.stdin_fd, termios.TCSADRAIN, self.old_keyboard_settings)             
        except Exception as e:
            print "Could not restore keyboard settings:"
            print e


