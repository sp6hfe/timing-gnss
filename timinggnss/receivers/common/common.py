from enum import Enum


class PositionMode(Enum):
    NOT_DEFINED = 0
    NAVIGATION = 1
    SELF_SURVEY = 2
    CONSTANT_SELF_SURVEY = 3
    TIMING_ONLY = 4
