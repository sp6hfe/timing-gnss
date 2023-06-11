from .furuno import Furuno
import time


class GNSS:
    def __init__(self, data_tx_callback):
        self.detected = False
        self.tx = data_tx_callback
        self.hw = Furuno()

    def detect(self):
        self.detected = False
        max_detection_time_sec = 5

        self.__send(self.hw.detection_message())

        start = time.time()
        while time.time() - start < max_detection_time_sec:
            if self.detected:
                break
            time.sleep(1)

        return self.detected

    def process(self, message):
        if not self.detected:
            self.__hw_detection(message)

    def __hw_detection(self, message):
        self.detected = self.hw.detect(message)
        if self.detected:
            hw_info = self.hw.info()
            print('Connected to ' + hw_info['id'] + ' receiver (name: ' +
                  hw_info['name'] + ', version: ' + hw_info['version'] + '.')

    def __send(self, message):
        if self.tx:
            self.tx(message)
