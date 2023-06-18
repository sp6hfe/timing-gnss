import logging
from timinggnss.timinggnss import TimingGnss
from timinggnss.common.enums import PositionMode
import time

SERIAL_IF = '/dev/ttyUSB0'
SERIAL_BAUD = 38400
SS_SIGMA_THRESHOLD = 0
SS_TIME_THRESHOLD = 1
TIME_ONLY_TRANSITION_TIME = SS_TIME_THRESHOLD + 1


def main():
    configure_logging()

    with TimingGnss(SERIAL_IF, SERIAL_BAUD) as TG:
        # 1. Perform initialization which, in turn, perform HW detection
        if not TG.init():
            print('GNSS module couldn\'t be initialized - exiting.')
            return

        tg_status = TG.status()
        if (tg_status['detected']):
            print('Connected to ' + tg_status['id'] + ' receiver (name: ' +
                  tg_status['name'] + ', version: ' + tg_status['version'] + ').')
        else:
            print('Something is wrong, GNSS module should be detected already.')
            return

        # 2. Check GNSS receiver state to see if in TIME ONLY mode, if so we're done
        if in_time_only_mode(tg_status):
            print('Position mode is TIME ONLY. Exiting.')
            return

        # 3. If not switch to SELF SURVEY mode with reasonable parameters allowing switching to TIME ONLY mode
        print(
            "Position mode is not TIME ONLY. Setting reasonable SELF SURVEY parameters...")

        TG.set_self_survey_position_mode(
            sigma_threshold=SS_SIGMA_THRESHOLD, time_threshold=SS_TIME_THRESHOLD)

        # 4. Monitor transition to TIME ONLY mode
        print('Waiting for TIME ONLY position mode...')
        tg_status = TG.status()
        start = time.time()
        while not in_time_only_mode(tg_status) and int(((time.time() - start) / 60)) < TIME_ONLY_TRANSITION_TIME:
            time.sleep(1)
            tg_status = TG.status()

        # 5. Summary
        if in_time_only_mode(TG.status()):
            print("Position mode changed to TIME ONLY.")
        else:
            print("Position mode is not TIME ONLY.")


def configure_logging():
    logging.basicConfig(level=logging.DEBUG)


def in_time_only_mode(status):
    return status['position_mode_data']['mode'] == PositionMode.TIME_ONLY


if __name__ == "__main__":
    main()
