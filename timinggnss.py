import serial
import threading
import time

class SerialLineReader(threading.Thread):
    """
    A threaded line reader for serial communication.

    This class reads lines of text from a serial port and invokes a callback function
    whenever a new line is received. It runs in a separate thread, allowing for concurrent
    reading from the serial port.

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

class GT88:
	def __init__(self, port, baudrate, threaded_read=True):
		self.gnss_port = port
		self.gnss_baudrate = baudrate
		self.out_frequency = 0
		try:
			self.gnss = serial.Serial(self.gnss_port, self.gnss_baudrate,timeout=1)
		except:
			self.gnss = None

	def __del__(self):
		if self.__is_opened():
			self.gnss.close()

	def set_out_frequency(self, frequency=1000):
		if frequency < 10:
			return False

		self.out_frequency = int(frequency)

		return self.enable_out_frequency()


	def enable_out_frequency(self):
		query = "PERDAPI,FREQ,1," + str(self.out_frequency) + ",50,0"
		message = self.__assemble_message(query)
		self.direct_write(message)

	def disable_out_frequency(self):
		message = self.__assemble_message("PERDAPI,FREQ,0,0,0,0")
		self.direct_write(message)

	def open(self):
		if self.gnss is not None:
			if not self.gnss.is_open:
				try:
					self.gnss.open()
				except:
					self.gnss = None
		else:
			try:
				self.gnss = serial.Serial(self.gnss_port, self.gnss_baudrate,timeout=1)
			except:
				self.gnss = None
	
	def close(self):
		if self.__is_opened():
			self.gnss.close()

	def direct_read(self, max_chars_no=1):
		if max_chars_no < 1:
			return []
		
		if self.__is_opened():
			# sync to the start of the nearest message
			garbage = self.gnss.read_until("\n", 1000)
			if garbage[-1] == "\n":
				raw_data = self.gnss.readlines(max_chars_no)

			# remove newline characters
			cleaned_data = list()
			for line in raw_data:
				cleaned_data.append(line.split()[0])

		return cleaned_data

	def direct_write(self, data):
		if self.__is_opened():
			message = self.__assemble_message(data)
			if len(message) > 0:
				self.gnss.write(message)

	def __is_opened(self):
		return self.gnss is not None and self.gnss.is_open

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

def main():
	gnss = GT88("/dev/ttyUSB0", 38400)

	gnss.direct_write("PERDSYS,VERSION")
	data = gnss.direct_read(2000)

	for line in data:
		if "$PERDSYS" in line:

			info = line.split("*")[0].split(",")
			print("Connected to " + info[5] + " receiver (" + info[2] + ") version: " + info[3] + ".")

if __name__=="__main__":
	main()