from abc import ABC, abstractmethod
from typing import Optional, Union, Dict

from ..common.enums import PositionMode, PositionFixMode


class HwAdapterInterface(ABC):
    # General processing #

    @abstractmethod
    def detect(self, data: str) -> Optional[Dict[str, str]]:
        pass

    @abstractmethod
    def process(self, data: str) -> None:
        pass

    # Data providers #

    @abstractmethod
    def get_position_mode_data(self) -> Optional[Dict[str, Union[int, PositionMode, PositionFixMode]]]:
        pass

    @abstractmethod
    def get_ext_signal_data(self) -> Optional[Dict[str, Union[bool, int]]]:
        pass

    # Message generators #

    @abstractmethod
    def get_detection_message(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_position_mode_set_message(self, position_mode: PositionMode, sigma_threshold: int, time_threshold: int, latitude: float, longitude: float, altitude: float) -> Optional[str]:
        pass

    @abstractmethod
    def get_ext_signal_status_message(self):
        pass

    @abstractmethod
    def get_ext_signal_enable_message(self, frequency_hz: int, duty: int, offset_to_pps: int) -> Optional[str]:
        pass

    @abstractmethod
    def get_ext_signal_disable_message(self) -> Optional[str]:
        pass
