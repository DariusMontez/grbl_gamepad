from .messages import *

def parse_line(line):
    # Grbl 1.1d ['$' for help]  # welcome message
    # >G20G90:ok                # startup block executed ok
    # [MSG:Enabled]             # something was enabled
    # [MSG:Disabled]            # something was disabled
    # <Idle|MPos:0.000,0.000,0.000|FS:0,0|WCO:0.000,0.000,0.000>    # status report
    # error:5                   # error response message with number

    if 'Grbl' in line:
        version = line.split(' ')[1]
        return WelcomeMessage(version)

    elif 'ALARM' in line:
        alarm_state = line.split(':')[1]
        return AlarmMessage(alarm_state)

    elif line[0] == '$':
        setting_name, setting_value = line[1:].split('=')
        return SettingsMessage(setting_name, setting_value)

    elif line == 'ok':
        return OKMessage()
    
    elif line.startswith('error:'):
        error_number = line.split(':')[1]
        return ErrorMessage(error_number)

    elif line.startswith('[MSG:'):
        feedback = line.replace('[MSG:', '').replace(']', '')
        return FeedbackMessage(feedback)

    elif line.startswith('<'):
        params = line.replace('<', '').replace('>', '').split('|')
        
        status = {}
        status['mode'] = params[0]

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

            status[k] = v

        return StatusMessage(status)

    elif line.startswith('>'):
        data = line.replace('>', '').split(':')
        startup_block = data[0]
        is_valid = data[1] == 'ok'
        return StartupBlockMessage(startup_block, is_valid)