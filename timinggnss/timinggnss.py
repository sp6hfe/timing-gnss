from .serialthread import SerialThread
from .receivers.gnss import GNSS


class TimingGnss:
    def __init__(self, port, baudrate):
        self.ext_signal_enabled = False
        self.ext_signal_frequency_hz = 0
        self.ext_signal_duty = 50
        self.ext_signal_offset_to_pps = 0

        self.serial_thread = SerialThread(
            port, baudrate, self.__new_message, self.__serial_thread_error)
        self.gnss = GNSS(self.write)

    def __enter__(self):
        self.serial_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.serial_thread.join()

    def init(self):
        return self.gnss.detect()

    def write(self, data):
        if len(data) > 0:
            self.serial_thread.write(data)

    def debug_log(self, is_enabled):
        self.serial_thread.debug_log(is_enabled)
        self.gnss.debug_log(is_enabled)

    def status(self):
        # assemble full status
        timinggnss_status = self.gnss.status()
        timinggnss_status['ext_signal_enabled'] = self.ext_signal_enabled
        timinggnss_status['ext_signal_frequency_hz'] = self.ext_signal_frequency_hz
        timinggnss_status['ext_signal_duty'] = self.ext_signal_duty
        timinggnss_status['ext_signal_offset_to_pps'] = self.ext_signal_offset_to_pps

        return timinggnss_status

    def ext_signal_set(self, frequency=1000):
        self.ext_signal_frequency_hz = int(frequency)
        return self.ext_signal_enable()

    def ext_signal_enable(self):
        self.gnss.ext_signal_enable(
            self.ext_signal_frequency_hz, self.ext_signal_duty, self.ext_signal_offset_to_pps)
        self.ext_signal_enabled = True

    def ext_signal_disable(self):
        self.gnss.ext_signal_disable()
        self.ext_signal_enabled = False

    def __new_message(self, message):
        # possibly place for messages filtering and dispatching
        self.gnss.process(message)

    def __serial_thread_error(self):
        print('Serial thread error occured.')
