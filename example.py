from timinggnss.timinggnss import TimingGnss
import time


def main():
    with TimingGnss('/dev/ttyUSB0', 38400) as TG:
        TG.debug_log(True)

        if not TG.init():
            print('GNSS module couldn\'t be initialized - exiting.')
            return

        tg_status = TG.status()
        TG.debug_log(False)
        if (tg_status['detected']):
            print('Connected to ' + tg_status['id'] + ' receiver (name: ' +
                  tg_status['name'] + ', version: ' + tg_status['version'] + '.')
        else:
            print('Something is wrong, GNSS module should be detected already.')
            return

        timing_mode = 'TO'
        if tg_status['mode'] == timing_mode:
            print('Position mode is timing. Exiting.')
            return
        else:
            print("Position mode is not timing. Waiting...")

            start = time.time()
            while tg_status['mode'] != timing_mode and time.time() - start < 5:
                time.sleep(1)
                tg_status = TG.status()

            tg_status = TG.status()
            if tg_status['mode'] == timing_mode:
                print("Position mode changed to timing. Exiting.")
            else:
                print("Position mode is not timing. Exiting.")


if __name__ == "__main__":
    main()
