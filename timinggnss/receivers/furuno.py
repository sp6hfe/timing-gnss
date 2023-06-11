

class Furuno:
    def __init__(self):
        self.MESSAGE_GET_VERSION = 'PERDSYS,VERSION'
        self.MESSAGE_START_HOT = 'PERDAPI,START,HOT'

        self.MODULE_DETECTION_MESSAGE_PREFIX = 'PERDSYS'
        self.MODULE_DETECTION_STRING_GT88 = 'GT88'

        self.module_info = {
            'name': 'NA',
            'version': 'NA',
            'id': 'NA'
        }

    def detection_message(self):
        return Furuno.assemble_message(self.MESSAGE_GET_VERSION)

    def detect(self, message):
        if self.MODULE_DETECTION_MESSAGE_PREFIX in message:
            # PERDSYS,VERSION,device,version,reason,reserve*CRC
            data_count_after_split_with_crc = 2
            elements_count_in_info_section = 6

            data = message.split('*')
            if len(data) == data_count_after_split_with_crc:
                # interesting information is in the 1st data section
                info = data[0].split(',')
                if len(info) == elements_count_in_info_section:
                    if info[5] == self.MODULE_DETECTION_STRING_GT88:
                        self.module_info['name'] = info[2]
                        self.module_info['version'] = info[3]
                        self.module_info['id'] = info[5]
                        return True
        return False

    def info(self):
        return self.module_info

    @staticmethod
    def assemble_message(data):
        if len(data) < 1:
            return ''

        checksum = Furuno.__checksum(data)
        message = '$' + data + '*' + hex(checksum)[2:].upper() + '\r\n'
        return message

    @staticmethod
    def __checksum(data):
        checksum = 0
        for byte in data:
            checksum ^= ord(byte)
        return checksum
