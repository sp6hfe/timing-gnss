from .serialthread import SerialThread


class TimingGnss:
    def __init__(self, port, baudrate):
        self.serial_thread = SerialThread(
            port, baudrate, self.__new_message, self.__serial_thread_error)
        self.out_frequency = 0

    def __enter__(self):
        self.serial_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.serial_thread.join()

    def write(self, data):
        message = self.__assemble_message(data)
        if len(message) > 0:
            self.serial_thread.write(message)

    def set_out_frequency(self, frequency=1000):
        if frequency < 10:
            return False

        self.out_frequency = int(frequency)
        return self.enable_out_frequency()

    def enable_out_frequency(self):
        query = 'PERDAPI,FREQ,1,' + str(self.out_frequency) + ',50,0'
        message = self.__assemble_message(query)
        self.serial_thread.write(message)

    def disable_out_frequency(self):
        message = self.__assemble_message('PERDAPI,FREQ,0,0,0,0')
        self.serial_thread.write(message)

    def __checksum(self, data):
        checksum = 0
        for byte in data:
            checksum ^= ord(byte)
        return checksum

    def __assemble_message(self, data):
        if len(data) < 1:
            return ''

        checksum = self.__checksum(data)
        message = '$' + data + '*' + hex(checksum)[2:].upper() + '\r\n'
        return message

    def __new_message(self, message):
        if '$PERDSYS' in message:
            info = message.split('*')[0].split(',')
            print('Connected to ' +
                  info[5] + ' receiver (' + info[2] + ') version: ' + info[3] + '.')

    def __serial_thread_error(self):
        print('Serial thread error occured.')
