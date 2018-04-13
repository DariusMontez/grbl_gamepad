# -*- coding: utf-8 -*-

"""Main module."""

from queue import Queue
from threading import Thread, Lock
from time import sleep


class Grbl:

    realtime_commands = [

        # Basic commands
        b'\x18', # soft-reset
        b'?',    # status report query
        b'~',    # cycle start / resume
        b'!',    # feed hold

        b'\x84', # saftey door opened
        b'\x85', # jog cancel

        # Feedrate overrides
        b'\x90', # set to 100% of programmed rate
        b'\x91', # increase 10%
        b'\x92', # decrease 10%
        b'\x93', # increase 1%
        b'\x94', # decrease 1%

        # Rapid overrides
        b'\x95', # set to 100% rapid rate
        b'\x96', # set to 50%
        b'\x97', # set to 25%

        # Spindle speed override
        b'\x99', # set to 100% of programmed speed
        b'\x9A', # increase 10%
        b'\x9B', # decrease 10%
        b'\x9C', # increase 1%
        b'\x9D', # decrease 1%
        
        b'\x9E', # toggle spindle stop [HOLD]

        b'\xA0', # toggle flood coolant [IDLE, RUN, HOLD]
        b'\xA1', # toggle mist coolant  [IDLE, RUN, HOLD]
    ]

    status_modes = [
        'idle',
        'run',
        'jog',
        'hold',
        'door',
    ]

    max_planner_size = 128-1


    def __init__(self, serial):
        self.planner_size = 0
        self.send_queue = Queue()
        self.response_queue = Queue()
        
        self.status = {
        #     'mode': None,       
        #     'machine_position': None,
        #     'work_coordinates': None,
        #     'fs': None
        }

        self.settings = {}

        self.alarm_state = None
        self.check = False
        self.version = None
        self.sleeping = False

        self.serial = serial
        self.serial_mutex = Lock()

        self.thread = Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def _planner_cleared(self):
        self.planner_size = 0  # GRBL's planner is empty
        self.response_queue = Queue()  # no more responses will come

    def _unit_code(self, unit):
        return {
            'in': 'G20',
            'mm': 'G21',
        }[unit.lower()]

    def build_gcode(self, code, *a, **kw):
        return "{code}{flags}{words}".format(
                code=code,
                flags=''.join(flag for flag in a if flag),
                words=''.join('{}{:0.2f}'.format(word.upper(), kw[word]) for word in kw if kw[word]))


    def jog(self, feedrate, unit='mm', relative=True, **kw):
        cmd = '$J='

        params = [x.lower() for x in kw]

        assert 'x' in params or 'y' in params or 'z' in params
        
        flags = []

        if relative:
            flags.append('G91')

        flags.append(self._unit_code(unit))
        flags.append('F{:d}'.format(feedrate))

        return self.build_gcode('$J=', *flags, **kw)


    def enqueue(self, command):
        self.send_queue.put(command + b'\n')

    def send_realtime(self, command):
        #self.response_queue.put(command + b'\n')
        #self._serial_write_safe(command + b'\n')
        self.enqueue(command)

    # command wrappers

    def toggle_check_mode(self):
        self.enqueue(b'$C')


    def unlock(self):
        self.enqueue(b'$X')

    def query_status(self):
        self.send_realtime(b'?')

    def query_settings(self):
        self.send_realtime(b'$$')

    def soft_reset(self):
        self.send_realtime(b'\x18')


    # events

    def on_connect(self):
        print("Grbl booted up!")

        #sleep(3)
        
        self._planner_cleared()

        self.query_status()
        self.query_settings()

    def on_alarm_message(self, message):
        self.alarm_state = message.split(':')[1]
        print("alarm message: {}".format(self.alarm_state))

    def on_settings_message(self, message):
        k, v = message[1:].split('=')
        self.settings[k] = v
        print("settings message: ${} = {}".format(k, v))

    def on_response_message(self, message):

        def consume_res():
            if self.response_queue.empty():
                print("Received and un-called-for 'ok' response")
                return

            cmd = self.response_queue.get()

            self.planner_size -= len(cmd)

            print("got response for cmd: {}\tplanner size: {}".format(cmd, self.planner_size))
            
            # Jog Cancel will empty the planner of all JOG commands
            if cmd == b'\x85':
                self._planner_cleared()

            self.response_queue.task_done()
        
        consume_res()

        if message == 'ok':
            pass
        elif 'error' in message:
            errno = message.split(':')[1]
            print("ERR: {}".format(errno))

    def on_feedback_message(self, message):
        m = message.replace('[MSG:', '').replace(']', '')
        print("feedback message: {}".format(m))

    def on_status_message(self, message):
        params = message.replace('<', '').replace('>', '').split('|')
        self.status['mode'] = params[0]

        for param in params[1:]:
            k, v = param.split(':')

            # split arrays
            if ',' in v:
                v = v.split(',')

                # convert numbers
                for i, item in enumerate(v):
                    try:
                        v[i] = float(item)
                    except:
                        pass

            self.status[k] = v

        print("status message: {}".format(self.status))

    def on_startup_message(self, message):
        data = message.replace('>', '').split(':')
        gcode = data[0]
        valid = data[1] == 'ok'

        if not valid:
            errno = data[2]
            print("startup message error: {}".format(errno))
        else:
            print("startup message: {}".format(gcode))
        

    def _serial_write_safe(self, data):
        self.serial_mutex.acquire()
        self.serial.write(data)
        print("SEND: {}\tplanner size: {}".format(data, self.planner_size))
        self.serial_mutex.release()

    def _process_serial(self):
        if self.serial.in_waiting > 0:
            line = self.serial.readline()
            line = line.decode('utf-8')
            line = line.strip()
            print("RECV: {}".format(line))
            if line:
                self._parse_line(line)

    def _parse_line(self, line):
            # Grbl 1.1d ['$' for help]  # welcome message
            # >G20G90:ok                # startup block executed ok
            # [MSG:Enabled]             # something was enabled
            # [MSG:Disabled]            # something was disabled
            # <Idle|MPos:0.000,0.000,0.000|FS:0,0|WCO:0.000,0.000,0.000>    # status report
            # error:5                   # error response message with number

            if 'Grbl' in line:
                self.version = line.split(' ')[1]
                self.on_connect()

            elif 'ALARM' in line:
                self.on_alarm_message(line)

            elif line[0] == '$':
                self.on_settings_message(line)

            elif line == 'ok' or line.startswith('error:'):
                self.on_response_message(line)

            elif line.startswith('[MSG:'):
                self.on_feedback_message(line)

            elif line.startswith('<'):
                self.on_status_message(line)

            elif line.startswith('>'):
                self.on_startup_message(line)

            

    def _process_queue(self):
        if self.send_queue.empty():
            return
        
        command = self.send_queue.get()
        cmd_size = len(command)

        if self.planner_size + cmd_size <= self.max_planner_size:
            self.planner_size += cmd_size
            self._serial_write_safe(command)
            self.response_queue.put(command)
            self.send_queue.task_done()
    
    def run(self):
        while True:
            self._process_serial()
            self._process_queue()
            
