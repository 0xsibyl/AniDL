import signal
import sys


def signal_handler(sig, frame):
    print('\n你按下了 Ctrl+C! 程序即将终止.')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
