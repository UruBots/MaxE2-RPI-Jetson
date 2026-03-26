from pycm import *


# Ejemplo minimo para CM-550:
# - valores 0..1023: cabeza OLLO en Port 1
# - valores 20000..20003: presets LED en Port 2
# Ajusta rangos y colores antes de probar en hardware real.

HEAD_CENTER = 512
HEAD_MIN = 280
HEAD_MAX = 760
LED_OFF = 20000
LED_RED = 20001
LED_BLUE = 20002
LED_MAGENTA = 20003


def clamp(value, lo, hi):
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def main():
    head = OLLO(1, const.OLLO_JOINT_POSITION)
    red_led = OLLO(2, const.OLLO_RED_BRIGHTNESS)
    blue_led = OLLO(2, const.OLLO_BLUE_BRIGHTNESS)
    head.write(HEAD_CENTER)
    red_led.write(0)
    blue_led.write(0)

    prev_value = -1
    while True:
        # 61 = Received Remocon Data en CM-550
        value = etc.read16(61)
        arrived = etc.read8(63)
        if arrived == 1 and value != prev_value:
            if 0 <= value <= 1023:
                head.write(clamp(value, HEAD_MIN, HEAD_MAX))
            elif value == LED_OFF:
                red_led.write(0)
                blue_led.write(0)
            elif value == LED_RED:
                red_led.write(100)
                blue_led.write(0)
            elif value == LED_BLUE:
                red_led.write(0)
                blue_led.write(100)
            elif value == LED_MAGENTA:
                red_led.write(100)
                blue_led.write(100)
            prev_value = value
            etc.write8(63, 0)
        delay(20)


main()
