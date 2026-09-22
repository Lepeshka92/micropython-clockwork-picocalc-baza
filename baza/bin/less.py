from bios import SPACE, ESC, ENTER


def main(args):
    if not args:
        terminal.writeline("Usage: less <filename>")
    else:
        path = ' '.join(args)
        terminal.clear_screen()
        cols, rows = terminal._cols, terminal._rows
        try:
            with open(path, 'r') as f:
                i = 0 
                for line in f:
                    for pos in range(0, len(line), cols):
                        chunk = line[pos: pos + cols]
                        if chunk:
                            terminal.write(chunk)
                            i += 1
                            if i >= rows - 1:
                                key = terminal.read_key(True)
                                if chr(key.code) == 'q' or key.code == ESC:
                                    return
                                elif key.code == ENTER:
                                    i = rows - 1
                                else:
                                    i = 0
        except OSError:
            terminal.writeline("less: {}: No such file".format(path))
        except Exception as e:
            terminal.writeline("less error: {}".format(e))

if __name__ == '__main__':
    main(args)