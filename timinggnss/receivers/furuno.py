

class Furuno:
    def __init__(self):
        self.MESSAGE_START_HOT = 'PERDAPI,START,HOT'

    def detect(self, message):
        # PERDSYS,VERSION,device,version,reason,reserve*CRC
        if 'PERDSYS' in message:
            data_count_after_split_with_crc = 2
            elements_count_in_info_section = 6

            data = message.split('*')
            if len(data) == data_count_after_split_with_crc:
                # interesting information is in the 1st data section
                info = data[0].split(',')
                if len(info) == elements_count_in_info_section:
                    if info[5] == 'GT88':
                        module_info = {
                            'name': info[2],
                            'version': info[3],
                            'id': info[5]
                        }
                        return module_info
        return None

    # MESSAGES #

    def detection_message(self):
        return self.__assemble_message('PERDSYS,VERSION')

    def ext_signal_enable_message(self, frequency_hz=10**6, duty=50, offset_to_pps=0):
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

    def ext_signal_disable_message(self):
        return self.__assemble_message('PERDAPI,FREQ,0,0,0,0')

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
