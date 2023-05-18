import serial
import threading
import time

class SerialPortHandler(threading.Thread):
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
        serial (serial.Serial): The serial connection object.
        is_running (bool): Indicates if the thread is running.
        is_paused (bool): Indicates if the reading loop is currently paused.
        write_queue (list): Queue to store messages to send.

    """
    def __init__(self, port, baudrate, on_new_line_callback, on_error_callback=None, max_bytes=1024):
        threading.Thread.__init__(self)
        self.port = port
        self.baudrate = baudrate
        self.on_new_line_callback = on_new_line_callback
        self.on_error_callback = on_error_callback
        self.max_bytes = max_bytes
        self.serial = None
        self.is_running = False
        self.is_paused = False
        self.write_queue = []

    def run(self):
        """
        The main method executed in the thread.

        Opens the serial connection and continuously reads from the serial port.
        Invokes the callback function when a new message is received or an error detected.
        Reading thread may be paused. When resumed data is synchronized to new line,
        treating all preceding bytes as garbage data.

        """
        try:
            self.serial = serial.Serial(self.port, self.baudrate)
            self.is_running = True
            sync_with_newline = True
            line_buffer = ''

            while self.is_running:
                # handle data to send
                self.__send_from_queue()

                if self.is_paused:
                    time.sleep(0.1)
                    sync_with_newline = True
                    continue
        
                while sync_with_newline:
                    # sync by reading small chunks of incoming data
                    garbage_data = self.serial.read_until('\n', 100)
                    if garbage_data[-1] == '\n':
                        line_buffer = ''
                        sync_with_newline = False

                # analyze incoming data byte by byte
                incoming_byte = self.serial.read(1)

                if incoming_byte == '\n':
                    # TODO: add data interity check here (before a callback is executed)
                    self.on_new_line_callback(line_buffer)
                    line_buffer = ''
                elif len(incoming_byte) > 0 and len(line_buffer) < self.max_bytes:
                    line_buffer += incoming_byte
        except serial.SerialException as e:
            # any problem with the serial device stops its further usage
            print('Serial connection error:', e)
            if self.on_error_callback:
                self.on_error_callback()
        finally:
            if self.serial and self.serial.is_open:
                self.serial.close()

    def stop(self):
        """
        Stop the thread and close the serial connection.

        """
        self.is_running = False

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
        Data will be send automatically as soon as possible.

        """
        if len(data) > 0:
            self.write_queue.append(data)

    def __send_from_queue(self):
        """
        Send all queued data (FIFO order) over serial port.
        
        """
        if self.serial and self.serial.is_open:
            while self.write_queue:
                data = self.write_queue.pop(0)
                self.serial.write(data)

class TimingGnss:
    def __init__(self, port, baudrate, threaded_read=True):
        self.serial_handler = SerialPortHandler(port, baudrate, self.__new_message, self.__serial_thread_error)
        self.serial_handler_thread = None
        self.out_frequency = 0

    def __enter__(self):
        self.__start_serial_handler()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__stop_serial_handler()
        self.serial_handler_thread.join()

    def write(self, data):
        message = self.__assemble_message(data)
        self.serial_handler.write(message)

    def set_out_frequency(self, frequency=1000):
        if frequency < 10:
            return False

        self.out_frequency = int(frequency)

        return self.enable_out_frequency()

    def enable_out_frequency(self):
        query = "PERDAPI,FREQ,1," + str(self.out_frequency) + ",50,0"
        message = self.__assemble_message(query)
        self.serial_handler.write(message)

    def disable_out_frequency(self):
        message = self.__assemble_message("PERDAPI,FREQ,0,0,0,0")
        self.serial_handler.write(message)

    def __checksum(self, data):
        checksum = 0

        for byte in data:
            checksum ^= ord(byte)

        return checksum
    
    def __assemble_message(self, data):
        message = ""
        if len(data) < 1:
            return message
        
        checksum = self.__checksum(data)
        message = "$" + data + "*" + hex(checksum)[2:].upper() + "\r\n"

        return message

    def __new_message(self, message):
        if "$PERDSYS" in message:
            info = message.split("*")[0].split(",")
            print("Connected to " + info[5] + " receiver (" + info[2] + ") version: " + info[3] + ".")

    def __serial_thread_error(self):
        print("Reading thread error occured.")

    def __start_serial_handler(self):
        self.serial_handler_thread = threading.Thread(target=self.serial_handler.run)
        self.serial_handler_thread.start()

    def __stop_serial_handler(self):
        self.serial_handler.stop()

    def __pause_serial_reader(self):
        self.serial_handler.pause()

    def __resume_serial_reader(self):
        self.serial_handler.resume()

def main():
    with TimingGnss("/dev/ttyUSB0", 38400) as GNSS:
        GNSS.write("PERDSYS,VERSION")

        for _ in range(0,3):
            time.sleep(1)

if __name__=="__main__":
    main()