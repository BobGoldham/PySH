import os
import getpass
import socket
from pathlib import Path
from datetime import datetime

def parse_PS1(PS1):
    __HOME = str(Path.home())
    __SYNTAX_LIST = {
        "%B": "\33[1m",
        "%b": "\33[0m",
        "%U": "\33[4m",
        "%u": "\33[0m",
        "%S": "\33{7m",
        "%s": "\33[0m",
        "%M": socket.gethostname(),
        "%m": socket.gethostname().split(".")[0],
        "%n": getpass.getuser(),
        "%#": "%" if os.getuid() else "#", # This should technically check for uid=0 OR POSIX.1e capabilities
        "%d": os.getcwd(),
        "%/": os.getcwd(),
        "%~": os.getcwd().replace(__HOME, "~"),
        "%D": datetime.now().strftime("%y-%m-%d"),
        "%T": datetime.now().strftime("%-H:%M"),
        "%t": datetime.now().strftime("%-I:%M"),
        "%@": datetime.now().strftime("%-I:%M"),
        "%*": datetime.now().strftime("%-H:%M:%S"),
        "%w": datetime.now().strftime("%a %-d"),
        "%W": datetime.now().strftime("%m/%d/%y"),
    }
    for key in __SYNTAX_LIST.keys():
        PS1 = PS1.replace(key, __SYNTAX_LIST[key])
    return PS1
