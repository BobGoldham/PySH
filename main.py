#!/usr/bin/env python3

import sys
import os
import getpass
import socket
import signal
import queue
import subprocess
import readline

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
            LAST_RETURN = job.returncode
        except KeyboardInterrupt:
            os.kill(job.pid, signal.SIGKILL)
        except Signal_TSTOP:
            os.kill(job.pid, signal.SIGSTOP)
            jobs.put(job)
    else:
        job = jobs.get()
        fg(index-1)
        jobs.put(job)

def alias(pat="", *subst):
    if not pat:
        [ print("{}={}".format(k, v)) for (k,v) in aliases]
    elif not subst and pat in aliases:
        print("{}={}".format(pat, aliases[pat]))
    else:
        aliases[pat] = ' '.join([*subst])

builtins = {"exit": sys.exit, "cd": cd, "alias": alias}
aliases = {}

HOME = str(Path.home())

PS1 = "%B%d-> %b"

LAST_RETURN = 0

class Signal_TSTOP(Exception):
    """Ctrl+Z was pressed"""
    pass

def handle_sigtstp(signum, frame):
    if frame.f_code == execute_command:
        job = frame.f_locals()["process"]
        os.kill(job.pid, signal.SIGTSTP)
        jobs.put(job)
    raise Signal_TSTOP

def substitute_aliases(cmd):
    tmpcmd = cmd
    for key in aliases:
        tmpcmd = tmpcmd.replace(key, aliases[key])
    return tmpcmd

def inline_substitution(cmd):
    if "~" in cmd:
        cmd = cmd.replace("~", HOME)
    if "!!" in cmd:
        cmd = cmd.replace("!!", readline.get_history_item(readline.get_current_history_length()-1))
        print(cmd)
    return cmd

def handle_builtins(cmd):
    cmdname, *cmdargs = cmd.split(' ')
    if cmdname in builtins:
        if cmdargs:
            builtins[cmdname](*cmdargs)
        else:
            builtins[cmdname]()
        return True
    return False

def execute_command(cmd, stdin=None, stdout=None):
    args = cmd.split(' ')
    i = 0
    while i < len(args):
        if args[i][0] == '"':
            while not args[i][-1] == '"':
                args[i] = ' '.join([args[i], args[i+1]])
                args = args[:i+1] + args[i+2:] if len(args) > i+2 else args[:i+1]
        i = i + 1
    return subprocess.Popen(args, stdin=stdin, stdout=stdout)

def parse_command(cmd):
    subcommands = cmd.split('|')
    try:
        tmppipe = sys.stdout
        for i in range(0, len(subcommands)-1):
            cmd = subcommands[i].strip()
            process = execute_command(cmd, stdin=tmppipe, stdout=subprocess.PIPE)
            tmppipe = process.stdout
        cmd = subcommands[-1].strip()
        process = execute_command(cmd, stdin=tmppipe)
        process.wait()
        LAST_RETURN = process.returncode
    except KeyboardInterrupt:
        print("")
    except Signal_TSTOP:
        print("\nPySH: suspended  {}".format(cmd))

def parse_line(line):
    if line and line[-1] == ':':
        parse_line.block = line
    elif line and line[0] in " \t":
        parse_line.block += line
    elif parse_line.block:
        try:
            exec(parse_line.block, globals())
        except Exception as e:
            print(e)
        finally:
            parse_line.block = ""
        parse_line(line)
    else:
        if not handle_builtins(line):
            line = substitute_aliases(line)
            line = inline_substitution(line)
            try:
                exec(line, globals())
            except (NameError,TypeError,SyntaxError,AttributeError) as e:
                try:
                    parse_command(line)
                except FileNotFoundError:
                    print("PySH error: `{}' is not a valid command or python snippet".format(line))
                    print("{}: {}".format(type(e).__name__, e))
                    print("`{}': no such file or directory".format(line.split(' ')[0]))

parse_line.block = ""

def prompt():
    line = ""
    if parse_line.block:
        _prompt = "... "
    else:
        _prompt = parse_PS1(PS1)
    line = input(_prompt)
    parse_line(line)

def main():
    if os.path.exists("{}/.pyshrc".format(HOME)):
        with open("{}/.pyshrc".format(HOME)) as pyshrc:
            block = ""
            i = 0
            for line in pyshrc:
                i += 1
                line = line.rstrip()
                parse_line(line)
            parse_line("")

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
