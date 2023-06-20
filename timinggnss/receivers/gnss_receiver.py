import logging
from .furuno_adapter import FurunoAdapter
from ..common.enums import PositionMode
import time


class GNSSReceiver:
    def __init__(self, tx_data_callback):
        self.tx_data = tx_data_callback

        self.hw_adapters_list = [FurunoAdapter()]
        self.messages_processing_prefix_list = list()

        self.hw = None
        self.hw_detected = False
        self.hw_name = 'NA'
        self.hw_version = 'NA'
        self.hw_id = 'NA'

    # PUBLIC METHODS #

    def detect(self):
        self.hw = None
        self.hw_detected = False
        self.hw_name = 'NA'
        self.hw_version = 'NA'
        self.hw_id = 'NA'

        max_detection_time_sec = 5

        for concrete_hw in self.hw_adapters_list:
            self.hw = concrete_hw
            self.__enable_incoming_messages_processing(
                self.hw.DETECTION_MESSAGES)
            self.__tx_data(self.hw.get_detection_message())

            start = time.time()
            while time.time() - start < max_detection_time_sec:
                time.sleep(1)
                # don't wait longer when HW detected
                if self.hw_detected:
                    break

            self.__disable_incoming_messages_processing(
                self.hw.DETECTION_MESSAGES)
            # don't try another module when HW detected
            if self.hw_detected:
                break

        if self.hw_detected:
            # enable reception of the state-carrying messages
            self.__enable_incoming_messages_processing(
                self.hw.POSITION_MODE_MESSAGES)

        return self.hw_detected

    def process(self, message):
        for prefix in self.messages_processing_prefix_list:
            if prefix in message:
                logging.debug('< ^^')
                # incoming messages processing
                if self.hw_detected:
                    self.hw.process(message)
                else:
                    self.__process_hw_detection(message)

    def status(self):
        result = dict()
        result['detected'] = self.hw_detected
        result['name'] = self.hw_name
        result['version'] = self.hw_version
        result['id'] = self.hw_id
        result['position_mode_data'] = self.hw.get_position_mode_data()

        return result

    def set_self_survey_position_mode(self, sigma_threshold: int = 0, time_threshold: int = 0):
        self.__tx_data(self.hw.get_position_mode_set_message(
            position_mode=PositionMode.SELF_SURVEY, sigma_threshold=sigma_threshold, time_threshold=time_threshold))

    def set_time_only_position_mode(self, latitude: float = 0, longitude: float = 0, altitude: float = 0):
        self.__tx_data(self.hw.get_position_mode_set_message(
            position_mode=PositionMode.TIME_ONLY, latitude=latitude, longitude=longitude, altitude=altitude))

    # FEATURES #

    def ext_signal_enable(self, frequency_hz, duty, offset_to_pps):
        if self.hw is not None:
            self.__tx_data(self.hw.get_ext_signal_enable_message(
                frequency_hz, duty, offset_to_pps))

    def ext_signal_disable(self):
        if self.hw is not None:
            self.__tx_data(self.hw.get_ext_signal_disable_message())

    # PRIVATE METHODS #

    def __process_hw_detection(self, message):
        if self.hw is not None:
            detection_result = self.hw.detect(message)
            if detection_result is not None:
                self.hw_name = detection_result['name']
                self.hw_version = detection_result['version']
                self.hw_id = detection_result['id']
                self.hw_detected = True

    def __tx_data(self, message):
        if self.tx_data:
            self.tx_data(message)

    def __enable_incoming_messages_processing(self, prefix_list):
        for new_prefix in prefix_list:
            if new_prefix not in self.messages_processing_prefix_list:
                self.messages_processing_prefix_list.append(new_prefix)

    def __disable_incoming_messages_processing(self, prefix_list):
        for prefix in prefix_list:
            if prefix in self.messages_processing_prefix_list:
                self.messages_processing_prefix_list.remove(prefix)