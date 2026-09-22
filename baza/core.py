import gc
import os
import sys


BIN_PATH = '/baza/bin'
LIB_PATH = '/baza/lib'
ETC_PATH = '/baza/etc'

commands = {}
terminal = None

def execute(command):
    cmd_and_args = command.strip().split()
    if not cmd_and_args: 
        return

    cmd, args = cmd_and_args[0], cmd_and_args[1:]

    if cmd in commands:
        try:
            commands[cmd](terminal, args)
        except Exception as e:
            terminal.writeline('Error executing {}: {}'.format(cmd, e))
    else:
        path = util.make_path(BIN_PATH, cmd) + '.py'
        if not util.is_file(path):
            terminal.writeline('Command not found: {}'.format(cmd))
            return

        _globals = {
            'args': args,
            'terminal': terminal,
            '__file__': path,
            '__name__': '__main__'
        }
        try:
            execfile(path, _globals)
        except NameError:
            with open(path, r) as f:
                exec(f.read(), _globals)
        except KeyboardInterrupt:
            terminal.writeline('Ctrl-C')
        except SystemExit:
            pass
        except Exception as e:
            terminal.writeline('Error executing {}: {}'.format(cmd, e))

def batch():
    path = util.make_path(ETC_PATH, 'auto.sh')
    if util.is_file(path):
        with open(path, 'r') as f:
            for command in f.readlines():
                execute(command)
                gc.collect()

def setup():
    global util
    global commands
    global terminal
    
    sys.path.append(LIB_PATH)
    import bios
    import term
    import disp
    import tool
    util = __import__('util')

    display = disp.Display()
    keyboard = bios.Keyboard()
    terminal = term.Terminal(display, keyboard, 40, 32)

    for func in dir(tool):
        if callable(getattr(tool, func)) and not func.startswith('_'):
            commands[func] = getattr(tool, func)

def shell():
    while True:
        terminal.write('\n>')
        try:
            command = terminal.readline()
        except KeyboardInterrupt:
            terminal.writeline('Ctrl-C')
            command = None

        if command == 'exit':
            break
        if command:
            execute(command)
        gc.collect()

def start():
    setup()
    batch()
    shell()


if __name__ == "__main__":
    start()