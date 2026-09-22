from time import sleep_ms
from machine import Pin, PWM
from micropython import const


PWM_PIN_L = const(26)
PWM_PIN_R = const(27)


class Sound(object):

    def __init__(self, vol):
        self._l = PWM(Pin(PWM_PIN_L))
        self._r = PWM(Pin(PWM_PIN_R))