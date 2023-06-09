

class Furuno:
    def __init__(self):
        self.MESSAGE_GET_VERSION = 'PERDSYS,VERSION'
        self.MESSAGE_START_HOT = 'PERDAPI,START,HOT'

        self.MODULE_DETECTION_MESSAGE_PREFIX = 'PERDSYS'
        self.MODULE_DETECTION_STRING_GT88 = 'GT88'

        self.module_name = 'NA'
        self.module_model = 'NA'
        self.module_fw_version = 'NA'

    def detection_message(self):
        return Furuno.assemble_message(self.MESSAGE_GET_VERSION)

    def detect(self, message):
        if self.MODULE_DETECTION_MESSAGE_PREFIX in message:
            info = message.split('*')[0].split(',')
            if info[5] == self.MODULE_DETECTION_STRING_GT88:
                self.module_name = info[5]
                self.module_model = info[2]
                self.module_fw_version = info[3]
                return True
        return False

    def name(self):
        return self.module_name

    def model(self):
        return self.module_model

    def fw_version(self):
        return self.module_fw_version

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
