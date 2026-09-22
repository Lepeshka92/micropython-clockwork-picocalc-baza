import gc
import os
import sys

import util


def cls(terminal, args):
    terminal.clear_screen()

def color(terminal, args):
    if not args or len(args) != 1:
        return
    if len(args[0]) != 2:
        terminal.writeline('color: wrong parameters: {}'.format(args[0]))
        return
    try:
        from term import PALETTE
        bg = PALETTE[int(args[0][0], 16) % 8]
        fg = PALETTE[int(args[0][1], 16) % 8]
    except ValueError:
        terminal.writeline('color: wrong parameters: {}'.format(args[0]))
        return

    terminal.set_color(bg, fg)
    terminal.clear_screen()

def ver(terminal, args):
    _, name = sys.version.split(';')
    terminal.writeline(name.strip())
    terminal.writeline(os.uname().machine)
    terminal.writeline('Powered by baza scripts')

def mem(terminal, args):
    terminal.writeline('Free memory: {} bytes'.format(gc.mem_free()))
    terminal.writeline('Allocated memory: {} bytes'.format(gc.mem_alloc()))

def pwd(terminal, args):
    terminal.writeline(os.getcwd())

def cd(terminal, args):
    path = util.make_path(' '.join(args))
    try:
        os.chdir(path)
    except OSError:
        terminal.writeline('cd: no such file or directory: {}'.format(path))

def ls(terminal, args):
    path = util.make_path(' '.join(args))
    try:
        for et in os.ilistdir(path):
            _name = et[0]
            _type = et[1]
            if _type == 0x4000:
                terminal.writeline(_name + '/')
            else:
                terminal.writeline(_name)
    except OSError:
        terminal.writeline('ls: no such file or directory: {}'.format(path))

def rm(terminal, args):
    if not args:
        terminal.writeline('rm: missing operand')
        return
    path = util.make_path(' '.join(args))
    try:
        os.remove(path)
    except OSError:
        try:
            os.rmdir(path)
        except OSError:
            terminal.writeline('rm: cannot remove: {}'.format(path))

def mkdir(terminal, args):
    if not args:
        terminal.writeline('mkdir: missing operand')
        return
    util.make_path(' '.join(args))
    try:
        os.mkdir(path)
    except OSError:
        terminal.writeline('mkdir: cannot create: {}'.format(path))

def bat(terminal, args):
    import bios
    terminal.writeline(bios.read_batt())

def halt(terminal, args):
    import bios
    bios.power_off()
    terminal.writeline('shutting down ...')

def boot(terminal, args):
    import machine
    machine.bootloader()