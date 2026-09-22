import socket
import network
from bios import ESC, ENTER
from term import RED, CYAN, YELLOW

CRLF = '\r\n'

class IRCError(Exception):
    pass

def create_sock(host, port):
    addr = socket.getaddrinfo(host, int(port), 0, socket.SOCK_STREAM)[0][-1]
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect(addr)
    return sock 

def parse_line(line, chan):
    chan_in_line = chan.lower() in line.lower()
    
    if ' 403 ' in line and chan_in_line:
        raise IRCError('Error: {} not exists!'.format(chan))

    if ' 473 ' in line and chan_in_line:
        raise IRCError('Error: join {} by invitation only!'.format(chan))

    if ' JOIN ' in line and chan_in_line:
        user = line.split("!")[0].lstrip(":")
        terminal.writeline('[{}] {} joined'.format(chan, user), fg=CYAN)

    if ' PART ' in line and chan_in_line:
        user = line.split("!")[0].lstrip(":")
        terminal.writeline('[{}] {} left'.format(chan, user), fg=RED)

    if ' QUIT ' in line:
        user = line.split("!")[0].lstrip(":")
        terminal.writeline('{} quit IRC'.format(user), fg=RED)

    if 'PRIVMSG' in line and chan_in_line:
        user = line.split("!")[0].lstrip(":")
        sep = 'PRIVMSG {} :'.format(chan)
        text = line.split(sep, 1)
        if len(text) == 2:
            terminal.writeline('[{}] {}: {}'.format(chan, user, text[1]))

def handle_key(code, chan, nick):
    result = None
    if code == ESC:
        result = 'PART {}{}'.format(chan, CRLF).encode()
        result += 'QUIT {}'.format(CRLF).encode()
        terminal.writeline('Leaving {}'.format(chan))
    elif code == ENTER:
        terminal.write('>')
        msg = terminal.readline()
        if msg:
            result = 'PRIVMSG {} :{}{}'.format(chan, msg, CRLF).encode()
            terminal.writeline('[{}] {}: {}'.format(chan, nick, msg), fg=YELLOW)
    return result

def main(args):
    if len(args) != 4:
        terminal.writeline('Usage: pirc <server> <port> <channel> <nick>')
        return
    if not network.WLAN(network.STA_IF).isconnected():
        terminal.writeline('WiFi not connected')
        return

    host, port, chan, nick = args

    terminal.writeline('Connecting to {} ...'.format(host))
    irc_sock = create_sock(host, port)
    irc_sock.settimeout(0.05)
    irc_sock.send('USER {} 0 * :{}{}'.format(nick, nick, CRLF).encode())
    irc_sock.send('NICK {}{}'.format(nick, CRLF).encode())
    irc_sock.send('JOIN {}{}'.format(chan, CRLF).encode())

    code = None
    chunk = 512
    buffer = ''
    while not code == ESC:
        key = terminal.read_key()
        code = key.code if key else None
        msg = handle_key(code, chan, nick)

        try:
            if msg:
                irc_sock.send(msg)
            data = irc_sock.recv(chunk)
            if not data:
                terminal.writeline('Connection closed by server.')
                break

            buffer += data.decode()
            while CRLF in buffer:
                line, buffer = buffer.split(CRLF, 1)
                if line.startswith('PING'):
                    pong = line.replace('PING', 'PONG')
                    irc_sock.send((pong + CRLF).encode())
                parse_line(line, chan)

        except OSError as e:
            if 110 in e.args: #timeout
                continue
            terminal.writeline('Network error: {}'.format(e))
            break
        except IRCError as e:
            terminal.writeline('IRC: {}'.format(e))
            break
        except Exception as e:
            terminal.writeline('Error: {}'.format(e))
            break
    irc_sock.close()


if __name__ == '__main__':
    main(args)