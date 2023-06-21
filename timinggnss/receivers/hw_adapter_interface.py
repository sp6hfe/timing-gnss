from abc import ABC, abstractmethod

from ..common.enums import PositionMode


class HwAdapterInterface(ABC):
    # General processing #

    @abstractmethod
    def detect(self, data: str):
        pass

    @abstractmethod
    def process(self, data: str):
        pass

    # Data providers #

    @abstractmethod
    def get_position_mode_data(self):
        pass

    # Message generators #

    @abstractmethod
    def get_detection_message(self):
        pass

    @abstractmethod
    def get_position_mode_set_message(self, position_mode: PositionMode, sigma_threshold: int, time_threshold: int, latitude: float, longitude: float, altitude: float):
        pass

    @abstractmethod
    def get_ext_signal_enable_message(self, frequency_hz: int, duty: int, offset_to_pps: int):
        pass

    @abstractmethod
    def get_ext_signal_disable_message(self):
        pass
