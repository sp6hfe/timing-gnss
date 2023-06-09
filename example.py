from timinggnss.timinggnss import TimingGnss
import time


def main():
    with TimingGnss('/dev/ttyUSB0', 38400) as TG:
        TG.init()

        for _ in range(0, 3):
            time.sleep(1)


if __name__ == "__main__":
    main()
