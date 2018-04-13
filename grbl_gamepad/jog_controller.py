
from serial import Serial
from time import sleep

from physics.vector import Vector as V
from gamepad import Gamepad

from grbl_gamepad import Grbl


class JogController:

    def __init__(self, grbl):
        self.gamepad = Gamepad()
        self.gamepad.on('l2', self.cancel_jog)

        self.step_size = 0.1 # mm
        self.max_feedrate = 1000
        self.loop_delay = 0.005

        self.jogging = False
        self.stepping = False
        self.grbl = grbl
    
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

    def cancel_jog(self, *a):
        print("cancel jog (0x85)")
        self.grbl.send_realtime(b'\x85')
        self.jogging = False

    def _do_jog(self):
        sleep(0.005)
        
        v = V(
            self.gamepad.axis('lx'), 
            -self.gamepad.axis('ly')
        )

        if v.length > 1e-5:
            self.jogging = True
        else:
            if self.jogging:
                self.cancel_jog()
            return

        feedrate = v.length * self.max_feedrate
        delta = v.normal * self.step_size

        #cmd = "$J=G91G21X{d.x:0.2f}Y{d.y:0.2f}F{feedrate:d}".format(
        #        d=delta,
        #        feedrate=int(feedrate))

       
        cmd = self.grbl.jog(int(feedrate), x=delta.x, y=delta.y)

        # print(cmd)
        self.grbl.enqueue(cmd.encode())



if __name__ == '__main__':
    s = Serial(port='/dev/ttyACM0', baudrate=115200)

    grbl = Grbl(serial=s)
    sleep(2)
    #grbl.enqueue(b'$N0=G20')
    #grbl.toggle_check_mode()
    #sleep(0.5)
    #grbl.request_settings()

    #grbl.toggle_check_mode()

    #grbl.unlock()

    j = JogController(grbl)
    j.start()
    
    input("Press ENTER to quit")
