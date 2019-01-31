class MessageBase:
    pass

# PUSH MESSAGES
# =============
# Spontanteous messages that Grbl may send at any time

class WelcomeMessage(MessageBase):
    def __init__(self, version):
        self.version = version

    def __repr__(self):
        return "WelcomeMessage(version={})".format(self.version)

class StartupBlockMessage(MessageBase):
    def __init__(self, startup_block, is_valid):
        self.startup_block = startup_block
        self.is_valid = is_valid

    def __repr__(self):
        return "StartupBlockMessage(startup_block={}, is_valid={})".format(
            self.startup_block,
            self.is_valid)

class AlarmMessage(MessageBase):
    def __init__(self, alarm_state):
        self.alarm_state = alarm_state

    def __repr__(self):
        return "AlarmMessage(alarm_state={})".format(self.alarm_state)

class StatusMessage(MessageBase):
    def __init__(self, status):
        self.status = status

    def __repr__(self):
        return "StatusMessage(status={})".format(self.status)

class SettingsMessage(MessageBase):
    def __init__(self, setting_name, setting_value):
        self.setting_name = setting_name
        self.setting_value = setting_value

    def __repr__(self):
        return "SettingsMessage(setting_name={}, setting_value={})".format(
            self.setting_name,
            self.setting_value)

class FeedbackMessage(MessageBase):
    def __init__(self, feedback):
        self.feedback = feedback

    def __repr__(self):
        return "FeedbackMessage(feedback={})".format(self.feedback)

# RESPONSE MESSAGES
# =================
# Every command sent to Grbl will invoke a response (either OK or Error)

class ResponseMessage(MessageBase):
    def __repr__(self):
        return "ResponseMessage()"

class OKMessage(ResponseMessage):
    def __repr__(self):
        return "OKMessage()"

class ErrorMessage(ResponseMessage):
    def __init__(self, error_number):
        self.error_number = error_number

    def __repr__(self):
        return "ErrorMessage(error_number={})".format(self.error_number)