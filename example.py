import logging
from timinggnss.timinggnss import TimingGnss
import time

SERIAL_IF = '/dev/ttyUSB0'
SERIAL_BAUD = 38400
PRECISE_TIMING_ENTERING_THRESHOLD_FOR_SIGMA_IN_METERS = 0
PRECISE_TIMING_ENTERING_THRESHOLD_FOR_TIME_IN_MINUTES = 1
AWAITING_FOR_PRECISE_TIMING_IN_MINUTES = PRECISE_TIMING_ENTERING_THRESHOLD_FOR_TIME_IN_MINUTES + 1


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
        if TG.is_in_precise_timing_mode():
            print('In precise timing mode already. Exiting.')
            return

        # 3. If not init precise timing based on self survey
        print("Not in precise timing mode. Setting reasonable self survey parameters.")
        TG.init_precise_timing_by_self_survey(
            sigma_threshold=PRECISE_TIMING_ENTERING_THRESHOLD_FOR_SIGMA_IN_METERS, time_threshold=PRECISE_TIMING_ENTERING_THRESHOLD_FOR_TIME_IN_MINUTES)

        # 4. Monitor transition into to precise timing
        print('Waiting for transition into precise timing mode...')
        start = time.time()
        while not TG.is_in_precise_timing_mode() and int(((time.time() - start) / 60)) < AWAITING_FOR_PRECISE_TIMING_IN_MINUTES:
            time.sleep(1)

        # 5. Summary
        if TG.is_in_precise_timing_mode():
            print("GNSS module entered precise timing mode.")
        else:
            print("GNSS module couldn't make it into precise timing mode.")


def configure_logging():
    logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    main()
