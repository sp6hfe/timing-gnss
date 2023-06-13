from timinggnss.timinggnss import TimingGnss
import time


def main():
    with TimingGnss('/dev/ttyUSB0', 38400) as TG:
        if not TG.init():
            print('GNSS module couldn\'t be initialized - exiting.')

        tg_status = TG.status()
        if (tg_status['detected']):
            print('Connected to ' + tg_status['id'] + ' receiver (name: ' +
                  tg_status['name'] + ', version: ' + tg_status['version'] + '.')
        else:
            print('Something is wrong, GNSS module should be detected already.')


if __name__ == "__main__":
    main()
