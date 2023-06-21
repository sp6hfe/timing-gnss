import logging

from .serialthread import SerialThread
from .receivers.gnss_receiver import GNSSReceiver
from .receivers.hw_adapter_furuno import HwAdapterFuruno


class TimingGnss:
    def __init__(self, port, baudrate):
        self.ext_signal_enabled = False
        self.ext_signal_frequency_hz = 0
        self.ext_signal_duty = 50
        self.ext_signal_offset_to_pps = 0

        self.serial_thread = SerialThread(
            port, baudrate, self.__new_message, self.__serial_thread_error)
        self.gnss = GNSSReceiver(self.write)
        self.gnss.add_adapter(HwAdapterFuruno())

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

    def status(self):
        # assemble full status
        timinggnss_status = self.gnss.status()
        timinggnss_status['ext_signal_enabled'] = self.ext_signal_enabled
        timinggnss_status['ext_signal_frequency_hz'] = self.ext_signal_frequency_hz
        timinggnss_status['ext_signal_duty'] = self.ext_signal_duty
        timinggnss_status['ext_signal_offset_to_pps'] = self.ext_signal_offset_to_pps

        return timinggnss_status

    def set_self_survey_position_mode(self, sigma_threshold: int, time_threshold: int):
        self.gnss.set_self_survey_position_mode(
            sigma_threshold=sigma_threshold, time_threshold=time_threshold)

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
        logging.error('Serial thread error occured.')
