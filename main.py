#!/usr/bin/env python3

import sys
import os
import getpass
import socket
import signal
import queue
import subprocess

from pathlib import Path
from PS1 import parse_PS1

jobs = queue.LifoQueue()

def cd(path):
    os.chdir(path)

def exit(exit_code=0):
    try:
        sys.exit(int(exit_code))
    except:
        sys.exit(1)

def fg(index=0):
    if index < 0:
        raise TypeError("Must be positive")
    if index >= len(jobs):
        raise TypeError("Job {} does not exist.".format(index))
    if index == 0:
        job = jobs.get()
        try:
            os.kill(job.pid, signal.SIGCONT)
            job.communicate()
        except KeyboardInterrupt:
            os.kill(job.pid, signal.SIGKILL)
        except Signal_TSTOP:
            os.kill(job.pid, signal.SIGSTOP)
            jobs.put(job)
    else:
        job = jobs.get()
        fg(index-1)
        jobs.put(job)

builtins = {"exit": exit, "cd": cd}

HOME = str(Path.home())
if "PS1" in os.environ:
    PS1 = os.environ["PS1"]
else:
    PS1 = "%B%d -> %b"

class Signal_TSTOP(Exception):
    """Ctrl+Z was pressed"""
    pass

def handle_sigtstp(signum, frame):
    if frame.f_code == execute:
        job = frame.f_locals["process"]
        os.kill(job.pid, signal.SIGSTOP)
        jobs.put(job)
    raise Signal_TSTOP

def handle_builtins(cmd):
    cmdname, *cmdargs = cmd.split(' ')
    if cmdname in builtins:
        if cmdargs:
            builtins[cmdname](*cmdargs)
        else:
            builtins[cmdname]()
        return True
    return False

def execute(cmd):
    subcommands = cmd.split('|')
    try:
        tmppipe = sys.stdout
        for i in range(0, len(subcommands)-1):
            cmd = subcommands[i].strip()
            process = subprocess.Popen(cmd.split(' '), stdin=tmppipe, stdout=subprocess.PIPE)
            tmppipe = process.stdout
        cmd = subcommands[-1].strip()
        process = subprocess.Popen(cmd.split(' '), stdin=tmppipe)
        process.wait()
    except KeyboardInterrupt:
        print("")
    except Signal_TSTOP:
        print("PySH: suspended `{}'".format(cmd))
    except Exception as e:
        print(e)
        print(cmd)

def prompt():
    cmd = ""
    _prompt = parse_PS1(PS1)
    cmd = input(_prompt)
    try:
        if handle_builtins(cmd):
            return
    except TypeError:
        print("Invalid arguments to builtin command `{}'".format(cmd.split(' ')[0]))
        return
    while cmd and cmd.rstrip()[-1] == ':':
        line = input("...")
        while line and line[0] in " \t":
            cmd += "\n{}".format(line)
            line = input("...")
        exec(cmd)
        cmd = line
    if cmd:
        try:
            exec(cmd)
        except (NameError,SyntaxError) as e:
            try:
                execute(cmd)
            except FileNotFoundError:
                print("That was neither a valid python snippet, nor a valid command.")
                print(e)
                print("`{}': no such file or directory".format(cmd.split(' ')[0]))

def main():
    while True:
        try:
            prompt()
        except (KeyboardInterrupt, Signal_TSTOP):
            print("")
        except EOFError:
            print("")
            return

if __name__ == "__main__":
    signal.signal(signal.SIGTSTP, handle_sigtstp)
    main()
