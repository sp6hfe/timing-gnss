from timinggnss.timinggnss import TimingGnss


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


if __name__ == "__main__":
    main()
