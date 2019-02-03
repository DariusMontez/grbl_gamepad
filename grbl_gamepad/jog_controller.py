
from serial import Serial
from time import sleep
from threading import Thread

from easy_vector import Vector as V
from gamepad import Gamepad

from grbl_link.interface import Grbl
from grbl_link.messages import *
from grbl_link.protocol import SimpleProtocol


class JogController:

    def __init__(self, grbl):
        self.step_size = 0.1 # mm
        self.max_feedrate = 1000
        self.loop_delay = 0.02

        self.jogging = False
        self.stepping = False
        self.grbl = grbl
    
        self.gamepad = Gamepad()

        # Feed hold
        self.gamepad.on('l1',       lambda *a: grbl.send(b'!'))

        # Resume cycle
        self.gamepad.on('l2',       lambda *a: grbl.send(b'~'))

        self.gamepad.on('btn11',    self.toggle_stepping) # left axis btn
        self.gamepad.on('select',   lambda *a: grbl.soft_reset())
        self.gamepad.on('start',    lambda *a: grbl.unlock())
        self.gamepad.on('dpady',    self.on_dpady)
        
        # zero X-axis work coordinates
        self.gamepad.on('btn2',     
            lambda *a: grbl.set_active_coord_system(x=0))
        
        # zero Y-axis work coordinates
        self.gamepad.on('btn1',     
            lambda *a: self.grbl.set_active_coord_system(y=0))
        
        # zero Z-axis work coordinates
        self.gamepad.on('btn3',     
            lambda *a: self.grbl.set_active_coord_system(z=0))
    
    def start(self):
        self._running = True
        self.thread = Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self._running = False
        self.thread.join()
        del self.thread

    def run(self):
        while self._running:
            if self.gamepad.connected:
                self._do_jog()

    def toggle_stepping(self, *a):
        self.stepping = not self.stepping
        print("stepping: {}".format(self.stepping))

    def cancel_jog(self, *a):
        print("cancel jog (0x85)")
        self.grbl.jog_cancel()
        self.jogging = False

    def on_dpady(self, value, event):
        self.max_feedrate *= (1 - 0.1*value)
        print("max feedrate: {}".format(self.max_feedrate))
    
    def _do_jog(self):
        sleep(0.005)
        
        # create vector from controller inputs (invert Y)

        v = V(
            self.gamepad.axis('lx'), 
            -self.gamepad.axis('ly'),
            -self.gamepad.axis('ry'),
        )

        
        if v.length > 1e-5:
            if self.stepping and self.jogging:
                return
            self.jogging = True
        else:
            if self.jogging:
                self.cancel_jog()
            return

        feedrate = int(v.length * self.max_feedrate)
        step_size_mod = self.step_size * (feedrate / self.max_feedrate)
        delta = v.normal * step_size_mod
        
        self.grbl.jog(feedrate, x=delta.x, y=delta.y, z=delta.z)


def message_handler(message, grbl):
    if isinstance(message, WelcomeMessage):
        grbl.query_status()
        #grbl.query_settings()
    elif isinstance(message, StatusMessage):
        if grbl.status['mode'] == 'Alarm':
            print("Grbl is locked!")

def main():
    s = Serial(port='/dev/ttyACM0', baudrate=115200)

    grbl = Grbl(s, protocol=SimpleProtocol, debug=True)
    grbl.add_message_handler(message_handler)

    # while not grbl.status['mode']:
    #     pass

    # if grbl.status['mode'] == 'Alarm':
    #     print("GRBL is locked!")

    #grbl.enqueue(b'$N0=G20')
    #grbl.toggle_check_mode()
    #sleep(0.5)
    #grbl.request_settings()

    #grbl.toggle_check_mode()
    

    j = JogController(grbl)
    j.start()
    
    input("Press ENTER to quit")

if __name__ == '__main__':
    main()
