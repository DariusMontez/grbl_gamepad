# -*- coding: utf-8 -*-

"""Main module."""

from time import sleep

from .parser import parse_line
from .messages import *
from .protocol import CharacterCountProtocol


"""
Read more about the streaming strategy recommended by grbl.
https://github.com/gnea/grbl/wiki/Grbl-v1.1-Interface#streaming-a-g-code-program-to-grbl


classes

FlowController ->
    - BlockingFlowController
    - CharCountFlowController

MessageBase ->
    - WelcomeMessage
    - AlarmMessage
    - StatusMessage
    - SettingsMessage
    - FeedbackMessage
    - StartupBlockMessage
    - ResponseMessage ->
        - ErrorMessage

"""

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

def debug_message_handler(message):
    print(message)

class GrblState:
    def __init__(self):

        self.version = None

        self.alarm_state = None

        self.status = {
            'mode': None,
            'WCO': None,
            'MPos': None,
            'FS': None
        }

        self.settings = {}
        
        self.sleeping = False

        # Grbl check mode
        self.check = False

    def message_handler(self, message):
        if isinstance(message, WelcomeMessage):
            self.version = message.version

        elif isinstance(message, AlarmMessage):
            self.alarm_state = message.alarm_state

        elif isinstance(message, StatusMessage):
            self.status.update(message.status)

        elif isinstance(message, SettingsMessage):
            self.settings[message.setting_name] = message.setting_value

        # TODO: handle sleep mode

        # TODO: handle check mode



class Grbl:

    def __init__(self, serial, protocol=SimpleProtocol, debug=False):

        self.state = GrblState()

        self.protocol = protocol(serial)
        self.protocol.add_message_handler(self.state.message_handler)
        if debug:
            self.protocol.add_message_handler(debug_message_handler)
        
        self.start()
        
    def start(self):
        self.protocol.start()

    def stop(self):
        self.protocol.stop()

    def send(self, command):
        self.protocol.enqueue(command)

    def add_message_handler(self, handler):
        def wrapper(message):
            handler(message, self)

        self.protocol.add_message_handler(wrapper)

    @property
    def version(self):
        return self.state.version

    @property
    def status(self):
        return self.state.status

    @property
    def alarm_state(self):
        return self.state.alarm_state

    @property
    def check(self):
        return self.state.check

    @property
    def sleeping(self):
        return self.state.sleeping

    # command wrappers

    def toggle_check_mode(self):
        self.send('$C')

    def unlock(self):
        self.send('$X')

    def query_status(self):
        self.send('?')

    def query_settings(self):
        self.send('$$')

    def soft_reset(self):
        self.send(b'\x18')

    def jog_cancel(self):
        self.send(b'\x85')

    
    # G-code functions

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

        cmd = self.build_gcode('$J=', *flags, **kw)
        self.send(cmd)
