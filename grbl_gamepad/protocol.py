from queue import Queue
from threading import Thread, Lock

from .messages import ResponseMessage
from .parser import parse_line


class ProtocolBase:
    def __init__(self, serial):
        self.serial = serial
        self.serial_mutex = Lock()
        self.send_queue = Queue()
        self.message_handlers = []

    def add_message_handler(self, handler):
        self.message_handlers.append(handler)

    def start_thread(self):
        self.thread = Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def enqueue(self, command):
        # add a newline and encode the command string into bytes
        # all Grbl commands exist in the ASCII charset

        command += "\n"
        command_bytes = command.encode()

        self.send_queue.put(command_bytes)

    def run(self):
        while True:
            self._process_serial()
            self._process_queue()
    
    def _serial_write_safe(self, data):
        self.serial_mutex.acquire()
        self.serial.write(data)
        self.serial_mutex.release()

    def _process_serial(self):
        if self.serial.in_waiting > 0:
            line = self.serial.readline()
            line = line.decode('utf-8')
            line = line.strip()
            print("RECV: {}".format(line))
            if line:
                message = parse_line(line)

                for handler in self.message_handlers:
                    handler(message)

    def _process_queue(self):
        return NotImplementedError

class CharacterCountProtocol(ProtocolBase):

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

        self.planner_size = 0
        self.MAX_PLANNER_SIZE = 128
        self.response_queue = Queue()

        self.add_message_handler(self._message_handler)

    # def _planner_cleared(self):
    #     self.planner_size = 0  # GRBL's planner is empty
    #     self.response_queue = Queue()  # no more responses will come

    def _message_handler(self, message):
        if isinstance(message, ResponseMessage):
            command = self.response_queue.get()
            self.planner_size -= len(command)

            if self.planner_size < 0:
                raise Exception("planner size is negative")

            self.response_queue.task_done()

    def _process_queue(self, send_queue):

        # process queue
        if not send_queue.empty():

            command = send_queue.get()
            predicted_planner_size = self.planner_size + len(command)
            
            if predicted_planner_size < self.MAX_PLANNER_SIZE:
                
                self._serial_write_safe(command)
                print("SEND: {}\tplanner size: {}".format(command, self.planner_size))
                send_queue.task_done()

                # now that the command has been sent, store it until an "ok" is received
                self.response_queue.put(command)