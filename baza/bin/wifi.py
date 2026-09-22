from time import sleep_ms
import network


def main(args):
    sta_if = network.WLAN(network.STA_IF)
    if not args:
        return
    command, *param = args

    if command == 'status':
        if not sta_if.active():
            terminal.writeline('WiFi down')
        else:
            terminal.writeline('WiFi connected' if sta_if.isconnected() else 'WiFi active')

    elif command == 'up':
        sta_if.active(False)
        sleep_ms(1000)
        sta_if.active(True)
        terminal.writeline('WiFi active')

    elif command == 'down':
        sta_if.active(False)
        terminal.writeline('WiFi down')

    elif command == 'scan':
        if not sta_if.active():
            terminal.writeline('WiFi down')
            return
        terminal.writeline('Available stations:')
        for ssid, _, chan, rssi, _, _ in sta_if.scan():
            terminal.writeline('{:<20} chan: {:>2} rssi: {}'.format(ssid, chan, rssi))

    elif command == 'hostname':
        if param:
            sta_if.config(hostname=param[0])
        terminal.writeline('WiFi hostname: {}'.format(sta_if.config('hostname')))

    elif command == 'connect':
        if not param:
            terminal.writeline('Usage: connect <ssid> [password]')
            return
        ssid, passwd = param[0], param[1] if len(param) > 1 else ''

        sta_if.active(False)
        sleep_ms(1000)
        sta_if.active(True)
        
        terminal.writeline('Connecting to {}...'.format(ssid))
        sta_if.connect(ssid, passwd)
        for _ in range(100):
            if sta_if.isconnected():
                break
            sleep_ms(100)
        terminal.writeline('WiFi connected' if sta_if.isconnected() else 'Failed')

    elif command == 'ipconfig':
        if not sta_if.isconnected():
            terminal.writeline('WiFi not connected')
            return
        ip, netmask, gateway, dns = sta_if.ifconfig()
        terminal.writeline('ip: {}'.format(ip))
        terminal.writeline('netmask: {}'.format(netmask))
        terminal.writeline('gateway: {}'.format(gateway))
        terminal.writeline('dns: {}'.format(dns))

    else:
        terminal.writeline('Unknown command: {}'.format(command))
        

if __name__ == '__main__':
    main(args)