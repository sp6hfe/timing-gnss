import serial


class TimingGnss:
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