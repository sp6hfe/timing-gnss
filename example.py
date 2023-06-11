from timinggnss.timinggnss import TimingGnss
import time


def main():
    with TimingGnss('/dev/ttyUSB0', 38400) as TG:
        if not TG.init():
            print('GNSS module couldn\'t be initialized - exiting.')


if __name__ == "__main__":
    main()
