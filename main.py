#!/usr/bin/env python3

import sys
import os
import getpass
import socket
import signal

from pathlib import Path
from subprocess import run as run_subp
from PS1 import parse_PS1

HOME = str(Path.home())
PS1 = "%B-> %b" # This should probably be either in a dotfile or env-var

class Signal_TSTOP(Exception):
    """Ctrl+Z was pressed"""
    pass

def handle_sigtstp(signum, frame):
    raise Signal_TSTOP

def execute(cmd):
    try:
        args = []
        if " " in cmd:
            args = cmd.split(" ")[1:]
            cmd = cmd.split(" ")[0]
        if cmd == "exit":
            if not args:
                sys.exit(0)
            try:
                exit_code = int(args[0])
            except:
                exit_code = 1
            sys.exit(exit_code)
        run_subp([cmd] + args)
    except FileNotFoundError:
        print('PySH: command not found: {}'.format(cmd))
    except Signal_TSTOP:
        print('PySH: suspended {}'.format(cmd))

def prompt():
    cmd = ""
    _prompt = parse_PS1(PS1)
    cmd = input(_prompt)
    execute(cmd)

def main():
    while True:
        try:
            prompt()
        except (Signal_TSTOP, KeyboardInterrupt):
            print("")

if __name__ == "__main__":
    signal.signal(signal.SIGTSTP, handle_sigtstp)
    main()
