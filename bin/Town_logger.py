import logging
import logging.handlers
from os import environ
from os.path import exists

from bin.Town_tools import TOWNSHELL_PATH, copyc, exePath, read_cfg


# Fetch the log level from 'townshell.cfg'
def get_loglevel():

    # Checks that townshell.cfg exists
    if exists(TOWNSHELL_PATH) is False:
        myTownshell = copyc(exePath(r"tmp_townshell.cfg"), TOWNSHELL_PATH)
        if myTownshell is None:
            return "INFO"

    loglevel = read_cfg("loglevel")
    if loglevel not in ("INFO", "WARNING", "DEBUG", "ERROR"):
        print("Invalid log level found in 'townshell.cfg'. INFO will be used")

        return "INFO"
    else:
        return loglevel


# Logging config to File
def listenerConfigurer():
    handler = logging.FileHandler(
        environ.get("LOGFILE", "log\\town.log"), encoding="utf-8"
    )
    formatter = logging.Formatter(
        "{asctime} : [{name}:{processName}:{funcName}] {levelname} :{message}",
        style="{",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)


# Logging process function handling the writing to file
def listenerProcess(queue, configurer):
    configurer()
    while True:
        try:
            record = queue.get()
            if (
                record is None
            ):  # We send this as a sentinel to tell the listener to quit.
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)  # No level or filter logic applied - just do it!
        except Exception:
            import sys, traceback

            print("Whoops! Problem:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


# Functional part of logger using QueueHandler to log events
def workerConfigurer(queue):
    h = logging.handlers.QueueHandler(queue)  # Just the one handler needed
    root = logging.getLogger("Town")
    root.addHandler(h)
    root.setLevel(get_loglevel())
