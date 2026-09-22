import os


def is_file(path):
    result = False
    try:
        result = os.stat(path)[0] == 0x8000
    except OSError:
        pass
    return result

def is_dir(path):
    result = False
    try:
        result = os.stat(path)[0] == 0x4000
    except OSError:
        pass
    return result

def dirname(path):
    pos = path.rstrip(os.sep).rfind(os.sep)
    if pos == -1:
        return ''
    return path[:pos] if pos > 0 else os.sep

def make_path(path, *args):
    path = path.rstrip(os.sep)
    full_path = [path]
    for part in args:
        full_path.append(part.strip(os.sep))
    return os.sep.join(full_path)