from .hw_adapter_interface import HwAdapterInterface
from ..common.enums import PositionMode, PositionFixMode


class HwAdapterFuruno(HwAdapterInterface):

    DETECTION_MESSAGES = ['PERDSYS']
    POSITION_MODE_MESSAGES = ['PERDCRY', 'GNGSA']

    def __init__(self):
        self.MESSAGE_START_HOT = 'PERDAPI,START,HOT'

        self.position_mode = {
            'mode': PositionMode.NOT_DEFINED,
            'fix': PositionFixMode.FIX_MISSING,
            'sigma_threshold': 0,
            'time_threshold': 0,
            'position_updates': 0,
            'receiver_status': 0
        }

    # General processing #

    def detect(self, data: str):
        message = self.__recover_message_from_data(data)
        if len(message) > 0:
            # PERDSYS,VERSION,device,version,reason,reserve*CRC
            if 'PERDSYS,VERSION' in message:
                data_count = 6

                module_data = message.split(',')
                if len(module_data) == data_count:
                    module_info = {
                        'name': module_data[2],
                        'version': module_data[3],
                        'id': module_data[5]
                    }
                    return module_info
        return None

    def process(self, data: str):
        message = self.__recover_message_from_data(data)
        if len(message) > 0:
            if self.__detect_message(message, self.POSITION_MODE_MESSAGES):
                self.__position_mode_decode(message)

    # Data providers #

    def get_position_mode_data(self):
        return self.position_mode

    # Message generators #

    def get_detection_message(self):
        return self.__assemble_message('PERDSYS,VERSION')

    def get_position_mode_set_message(self, position_mode: PositionMode = PositionMode.SELF_SURVEY, sigma_threshold: int = 10, time_threshold: int = 1440, latitude: float = 0, longitude: float = 0, altitude: float = 0):
        # modes: 'NAV'- navigation, 'SS' - self survey, 'CSS' - continous self survey, 'TO' - time only
        # sigma threshold in meters
        sigma_threshold_low_limit = 0
        sigma_threshold_high_limit = 255
        # time threshold in minutes
        time_threshold_low_limit = 0
        time_threshold_high_limit = 10080
        # latitude and longitude up to seventh decimal place
        latitude_low_limit = -90
        latitude_high_limit = 90
        longitude_low_limit = -180
        longitude_high_limit = 180
        # altitude up to two decimal places
        altitude_low_limit = -1000
        altitude_high_limit = 18000

        clamped_sigma_threshold = self.__clamp_value(
            sigma_threshold_low_limit, sigma_threshold, sigma_threshold_high_limit)
        clamped_time_threshold = self.__clamp_value(
            time_threshold_low_limit, time_threshold, time_threshold_high_limit)
        clamped_latitude = self.__clamp_value(
            latitude_low_limit, self.__limit_float_decimal_places(latitude, 7), latitude_high_limit)
        clamped_longitude = self.__clamp_value(
            longitude_low_limit, self.__limit_float_decimal_places(longitude, 7), longitude_high_limit)
        clamped_altitude = self.__clamp_value(
            altitude_low_limit, self.__limit_float_decimal_places(altitude, 2), altitude_high_limit)

        query = ''
        if position_mode == PositionMode.SELF_SURVEY:
            query = 'PERDAPI,SURVEY,1,' + \
                str(clamped_sigma_threshold) + \
                ',' + str(clamped_time_threshold)
        elif position_mode == PositionMode.TIME_ONLY:
            query = 'PERDAPI,SURVEY,3,0,0,' + \
                str(clamped_latitude) + ',' + \
                str(clamped_longitude) + ',' + str(clamped_altitude)

        return self.__assemble_message(query)

    def get_ext_signal_enable_message(self, frequency_hz=10**6, duty=50, offset_to_pps=0):
        frequency_low_limit_hz = 10
        frequency_high_limit_hz = 40*10**6
        duty_low_limit = 10
        duty_high_limit = 90
        offset_low_limit = 0
        offset_high_limit = 99

        new_frequency_hz = self.__clamp_value(
            frequency_low_limit_hz, int(frequency_hz), frequency_high_limit_hz)
        new_duty = self.__clamp_value(
            duty_low_limit, int(duty), duty_high_limit)
        new_offset_to_pps = self.__clamp_value(
            offset_low_limit, int(offset_to_pps), offset_high_limit)

        query = 'PERDAPI,FREQ,1,' + \
            str(new_frequency_hz) + ',' + str(new_duty) + \
            ',' + str(new_offset_to_pps)
        return self.__assemble_message(query)

    def get_ext_signal_disable_message(self):
        return self.__assemble_message('PERDAPI,FREQ,0,0,0,0')

    # Provate message decoders #

    def __position_mode_decode(self, message):
        if 'PERDCRY,TPS3' in message:
            data_count = 11
            data = message.split(',')
            if len(data) == data_count:
                self.position_mode['mode'] = self.__translate_position_mode(
                    int(data[2]))
                self.position_mode['sigma_threshold'] = int(data[4])
                self.position_mode['position_updates'] = int(data[5])
                self.position_mode['time_threshold'] = int(data[6])
                self.position_mode['receiver_status'] = int(data[10], 0)
        if 'GNGSA,A' in message:
            data_count = 19
            data = message.split(',')
            if len(data) == data_count:
                self.position_mode['fix'] = self.__translate_position_fix_pode(
                    int(data[2]))
            print(self.position_mode)

    # Helpers #

    def __assemble_message(self, data):
        if len(data) < 1:
            return ''

        checksum = format(self.__checksum(data), '02X')
        message = '$' + data + '*' + checksum + '\r\n'
        return message

    def __recover_message_from_data(self, message):
        if len(message) < 1:
            return ''

        checksum_separator = '*'
        message_parts_after_split_with_checksum = 2
        message_parts = message.split(checksum_separator)
        if len(message_parts) == message_parts_after_split_with_checksum:
            data = message_parts[0].replace('$', '', 1)
            calculated_checksum = format(self.__checksum(data), '02X')
            received_checksum = message_parts[1][:2]
            if calculated_checksum == received_checksum:
                return data
        return ''

    def __checksum(self, data):
        checksum = 0
        for byte in data:
            checksum ^= ord(byte)
        return checksum

    def __clamp_value(self, min, val, max):
        return sorted((min, val, max))[1]

    def __limit_float_decimal_places(self, value: float, max_decimal_places: int):
        decimal_places = str(value)[::1].find('.')
        if decimal_places > max_decimal_places:
            value = int(value * 10**max_decimal_places) / \
                (10**max_decimal_places)
        return value

    def __detect_message(self, message, detectables_list):
        for detectable in detectables_list:
            if detectable in message:
                return True
        return False

    def __translate_position_mode(self, mode_code: int):
        if mode_code == 0:
            return PositionMode.NAVIGATION
        if mode_code == 1:
            return PositionMode.SELF_SURVEY
        if mode_code == 2:
            return PositionMode.SELF_SURVEY
        if mode_code == 3:
            return PositionMode.TIME_ONLY
        return PositionMode.NOT_DEFINED

    def __translate_position_fix_pode(self, mode_code: int):
        if mode_code == 1:
            return PositionFixMode.FIX_MISSING
        if mode_code == 2:
            return PositionFixMode.FIX_2D
        if mode_code == 3:
            return PositionFixMode.FIX_3D
        return PositionFixMode.FIX_MISSING
