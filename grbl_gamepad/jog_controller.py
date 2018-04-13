
from serial import Serial
from time import sleep
from threading import Thread

from physics.vector import Vector as V
from gamepad import Gamepad

from grbl_gamepad.interface import Grbl


class JogController:

    def __init__(self, grbl):
        self.step_size = 0.1 # mm
        self.max_feedrate = 1000
        self.loop_delay = 0.02

        self.jogging = False
        self.stepping = False
        self.grbl = grbl
    
        self.gamepad = Gamepad()
        self.gamepad.on('l2',       self.cancel_jog)
        self.gamepad.on('btn11',    self.toggle_stepping) # left axis btn
        self.gamepad.on('select',   lambda *a: self.grbl.soft_reset())
        self.gamepad.on('start',    lambda *a: self.grbl.unlock())
    
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
        self.grbl.send_realtime(b'\x85')
        self.jogging = False

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

        feedrate = v.length * self.max_feedrate
        delta = v.normal * self.step_size
        cmd = self.grbl.jog(int(feedrate), x=delta.x, y=delta.y, z=delta.z)
        self.grbl.enqueue(cmd.encode())


def main():
    s = Serial(port='/dev/ttyACM0', baudrate=115200)

    grbl = Grbl(serial=s)
    sleep(2.5)

    if grbl.status['mode'] == 'alarm':
        print("GRBL is locked!")

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
