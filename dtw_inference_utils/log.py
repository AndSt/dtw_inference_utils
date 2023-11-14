import logging
import sys


def init_logging(level=logging.DEBUG):
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter(
        "[%(asctime)s, p%(process)s, %(name)s, %(filename)s:%(lineno)d] - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root.handlers = []
    root.addHandler(handler)
