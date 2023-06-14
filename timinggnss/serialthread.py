import serial
from threading import Thread, Lock
import time


class SerialThread(Thread):
    """
    A threaded serial port handler.

    This class reads lines of text from a serial port and invokes a callback function
    whenever a new line is received. At the same time it sends queued data over serial port.
    Data sending is done all at once so it may happen that the reader will loose incoming
    bytes.
    It runs in a separate thread, allowing for concurrent reading from the serial port.

    Args:
        port (str): The serial port to connect to (e.g., "/dev/ttyUSB0").
        baudrate (int): The baud rate for the serial communication (e.g., 38400).
        on_new_line_callback (function): The callback function to be invoked when a new line is received.
            The function should accept a single argument, which is the received line of text.
        on_error_callback (function): The callback function to be invoked when a serial device error is detected.
            Invoking this function inform subscriber that no further data readout is possible.
        max_bytes (int, optional): The maximum number of bytes to receive for each line. Defaults to 1024.

    Attributes:
        port (str): The serial port to connect to.
        baudrate (int): The baud rate for the serial communication.
        on_new_line_callback (function): The callback function to be invoked when a new line is received.
        on_error_callback (function): The callback function to be invoked when a serial device error is detected.
        max_bytes (int): The maximum number of bytes to receive for each line.
        serial_port (serial.Serial): The serial connection object.
        is_started (bool): Indocates if the reading/writing thread is started.
        is_paused (bool): Indicates if the reading loop is currently paused (writing is possible).
        write_queue (list): Queue to store messages to send.
        thread (threading.Threadad): Thread responsible for serial communication.
        debug_log_enabled (bool): Indicates if read/written data is logged to the console for debug purposes

    """

    def __init__(self, port, baudrate, on_new_line_callback, on_error_callback=None, max_bytes=1024):
        self.port = port
        self.baudrate = baudrate
        self.on_new_line_callback = on_new_line_callback
        self.on_error_callback = on_error_callback
        self.max_bytes = max_bytes
        self.serial_port = None
        self.is_started = False
        self.is_paused = False
        self.write_queue = []
        self.thread = None
        self.debug_log_enabled = False
        self.mutex = Lock()
        Thread.__init__(self)

    def __run(self):
        """
        The main method executed in the thread.

        Opens the serial connection and continuously reads from the serial port.
        Invokes the callback function when a new line is received
        ('\n' is not included) or an error detected.
        Spawned thread may be paused, resumed, stopped and restarted.
        When stared or resumed data is synchronized to new line,
        treating all preceding bytes as garbage data.

        """
        # most outer loop is used to re-open serial port in case of an errors detected
        # which is usable when, for example, one disconnect the serial device by accident
        while True:
            try:
                self.__open_serial_connection()
                sync_with_newline = True
                garbage_data = ''
                line_buffer = ''

                # inner loop control general flow of the write/read process
                # each step checks if process is_running to quickly exit
                # this loop when needed
                while self.serial_port.is_open:
                    # send any buffered data (even when reader is paused)
                    self.__send_data_from_queue()

                    if self.serial_port.is_open and self.is_paused:
                        # when reader is paused do not consume too much CPU time
                        sync_with_newline = True
                        time.sleep(0.1)
                        continue

                    while self.serial_port.is_open and sync_with_newline:
                        # sync by reading small chunks of incoming ASCII data
                        garbage_data += self.serial_port.read_until(
                            b'\n', 100).decode('UTF-8')
                        if garbage_data[-1] == '\n':
                            if self.debug_log_enabled:
                                print('< [g] ' + garbage_data[::-1])
                            sync_with_newline = False
                            garbage_data = ''
                            line_buffer = ''

                    if self.serial_port.is_open:
                        # analyze incoming data byte by byte
                        incoming_byte = self.serial_port.read(
                            1).decode('UTF-8')
                        if incoming_byte == '\n':
                            # send received line for further processing
                            if self.debug_log_enabled:
                                print('< ' + line_buffer)
                            self.on_new_line_callback(line_buffer)
                            line_buffer = ''
                        elif len(incoming_byte) > 0 and len(line_buffer) < self.max_bytes:
                            # line buffer is filled up to its capacity
                            line_buffer += incoming_byte
                # when above loop is finished it means thread end was requested
                break
            except serial.SerialException as e:
                # any problem with the serial device stops its further usage
                print('Serial connection error:', e)
                if self.on_error_callback:
                    self.on_error_callback()
            finally:
                # on any error serial port should be closed to be freshly opened in a while
                self.__close_serial_connection()
                # if thread stop was requested this method should return
                if not self.is_started:
                    return

    def start(self):
        """
        Start serial handler.
        If handler is not running it spawn a new read/write thread and open serial connection.

        """
        if self.thread == None or not self.thread.is_alive():
            try:
                self.thread = Thread(target=self.__run)
                self.thread.start()
                self.is_started = True
            except:
                print("Can't start serial handling thread!")

    def stop(self):
        """
        Stop serial handler.
        It terminate internally spawned reading/writing thread and close serial connection.

        """
        self.__close_serial_connection()
        self.is_started = False

    def join(self):
        """
        Join serial handler thread.

        It stop reading/writing thread and join.

        """
        if self.is_started:
            self.stop()
        if self.thread:
            self.thread.join()

    def pause(self):
        """
        Pause the reading loop.

        The thread will continue running, but no data will be read from the serial port.

        """
        self.is_paused = True

    def resume(self):
        """
        Resume the reading loop.

        If the loop was previously paused, it will resume reading data from the serial port.
        Data will be synchronized to the next incoming message.

        """
        self.is_paused = False

    def write(self, data):
        """
        Write new data to the FIFO writing queue.
        Data to be sent automatically as soon as possible.

        Args:
            data (str): ASCII data to be sent via serial conection
        """
        if self.is_started and len(data) > 0:
            self.write_queue.append(data)

    def debug_log(self, is_enabled):
        """
        Enable or disable read/write operation logging.
        This function is purely for debugging purposes.

        Args:
            is_enabled (bool): True: read/write data logging enabled, False: no logging.
        """
        self.debug_log_enabled = is_enabled

    def __open_serial_connection(self):
        """"
        Open HW connection to the serial device.

        """
        self.serial_port = serial.Serial(self.port, self.baudrate)

    def __close_serial_connection(self):
        """
        Close HW connection to the serial device.

        """
        with self.mutex:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

    def __send_data_from_queue(self):
        """
        Send all queued data (FIFO order) over serial port.

        """
        if self.serial_port and self.serial_port.is_open:
            while self.write_queue:
                data = self.write_queue.pop(0)
                if self.debug_log_enabled:
                    print('> ' + data)
                self.serial_port.write(data.encode('UTF-8'))
