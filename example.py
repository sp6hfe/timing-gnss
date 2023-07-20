import logging
from timinggnss.timinggnss import TimingGnss
import time

SERIAL_IF = '/dev/ttyUSB0'
SERIAL_BAUD = 38400
PRECISE_TIMING_ENTERING_THRESHOLD_FOR_SIGMA_IN_METERS = 0
PRECISE_TIMING_ENTERING_THRESHOLD_FOR_TIME_IN_MINUTES = 1
AWAITING_FOR_PRECISE_TIMING_IN_MINUTES = PRECISE_TIMING_ENTERING_THRESHOLD_FOR_TIME_IN_MINUTES + 1
AWAITING_FOR_EXT_SIGNAL_SETUP_IN_SEC = 5

EXT_REFERENCE_FREQUENCY_HZ = 10000000


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

        # 2. Check GNSS receiver state to see if current mode is precise timing, if so we're done
        if not TG.in_precise_timing_mode():

            # 3. If not init precise timing based on self survey
            print(
                "Not in precise timing mode. Setting reasonable self survey parameters.")
            TG.init_precise_timing_by_self_survey(
                sigma_threshold=PRECISE_TIMING_ENTERING_THRESHOLD_FOR_SIGMA_IN_METERS, time_threshold=PRECISE_TIMING_ENTERING_THRESHOLD_FOR_TIME_IN_MINUTES)

            # 4. Monitor transition into to precise timing
            print('Waiting for transition into precise timing mode...')
            start = time.time()
            while not TG.in_precise_timing_mode() and int(((time.time() - start) / 60)) < AWAITING_FOR_PRECISE_TIMING_IN_MINUTES:
                time.sleep(1)

            # 5. Summary
            if TG.in_precise_timing_mode():
                print("GNSS module entered precise timing mode.")
            else:
                print("GNSS module couldn't enter precise timing mode.")
                return
        else:
            print('GNSS module already in precise timing mode.')

        # 6. Set output reference frequency
        print('Setting reference signal to ' +
              str(EXT_REFERENCE_FREQUENCY_HZ) + 'Hz.')
        TG.ext_signal_set(EXT_REFERENCE_FREQUENCY_HZ)

        # 7. Validate if settings were applied
        print('Waiting for external signal to be reported as active...')
        start = time.time()
        while not TG.ext_signal_is_set() and int(((time.time() - start) / 60)) < AWAITING_FOR_EXT_SIGNAL_SETUP_IN_SEC:
            time.sleep(1)

        # 8. Summary
        if TG.ext_signal_is_set():
            print('External signal reported as active.')
        else:
            print('External signal wasn\'t reported as active.')


def configure_logging():
    logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    main()
