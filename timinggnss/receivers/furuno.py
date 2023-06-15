

class Furuno:

    DETECTION_MESSAGES = ['PERDSYS']
    POSITION_MODE_MESSAGES = ['PERDCRY']

    def __init__(self):
        self.MESSAGE_START_HOT = 'PERDAPI,START,HOT'

    # MESSAGE DECODERS #

    def detect(self, message):
        # PERDSYS,VERSION,device,version,reason,reserve*CRC
        if 'PERDSYS,VERSION' in message:
            data_count_after_split_with_crc = 2
            elements_count_in_info_section = 6

            data = message.split('*')
            if len(data) == data_count_after_split_with_crc:
                # interesting information is in the 1st data section
                info = data[0].split(',')
                if len(info) == elements_count_in_info_section:
                    module_info = {
                        'name': info[2],
                        'version': info[3],
                        'id': info[5]
                    }
                    return module_info
        return None

    def position_mode_decode(self, message):
        pass

    # MESSAGE GENERATORS #

    def get_detection_message(self):
        return self.__assemble_message('PERDSYS,VERSION')

    def get_position_mode_set_message(self, mode: str = 'SS', sigma_threshold: int = 10, time_threshold: int = 1440, latitude: float = 0, longitude: float = 0, altitude: float = 0):
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
        if mode == 'SS':
            query = 'PERDAPI,SURVEY,1,' + \
                str(clamped_sigma_threshold) + \
                ',' + str(clamped_time_threshold)
        elif mode == 'TO':
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

    # HELPERS #

    def __assemble_message(self, data):
        if len(data) < 1:
            return ''

        checksum = self.__checksum(data)
        message = '$' + data + '*' + hex(checksum)[2:].upper() + '\r\n'
        return message

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
