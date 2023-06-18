from enum import Enum


class PositionMode(Enum):
    NOT_DEFINED = 0
    NAVIGATION = 1
    SELF_SURVEY = 2
    CONSTANT_SELF_SURVEY = 3
    TIME_ONLY = 4


class PositionFixMode(Enum):
    NOT_DEFINED = 0,
    FIX_MISSING = 1,
    FIX_2D = 2,
    FIX_3D = 3
