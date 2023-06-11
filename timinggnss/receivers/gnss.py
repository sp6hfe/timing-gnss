from .furuno import Furuno
import time


class GNSS:
    def __init__(self, tx_data_callback):
        self.tx_data = tx_data_callback
        self.hw_detection_list = [Furuno()]

        self.hw = None
        self.hw_detected = False

    def detect(self):
        self.hw_detected = False
        max_detection_time_sec = 5

        for concrete_hw in self.hw_detection_list:
            self.hw = concrete_hw
            self.__tx_data(self.hw.detection_message())

            start = time.time()
            while time.time() - start < max_detection_time_sec:
                time.sleep(1)
                if self.hw_detected:
                    return True

        return self.hw_detected

    def process(self, message):
        if self.hw is not None:
            if not self.hw_detected:
                self.__process_hw_detection(message)

    def ext_signal_enable(self, frequency_hz, duty, offset_to_pps):
        if self.hw is not None:
            self.__tx_data(self.hw.ext_signal_enable_message(
                frequency_hz, duty, offset_to_pps))

    def ext_signal_disable(self):
        if self.hw is not None:
            self.__tx_data(self.hw.ext_signal_disable_message())

    def __process_hw_detection(self, message):
        self.hw_detected = self.hw.detect(message)
        if self.hw_detected:
            hw_info = self.hw.info()
            print('Connected to ' + hw_info['id'] + ' receiver (name: ' +
                  hw_info['name'] + ', version: ' + hw_info['version'] + '.')

    def __tx_data(self, message):
        if self.tx_data:
            self.tx_data(message)
