from pycm import *


# Ejemplo minimo para CM-550:
# lee el valor Remocon TX/RX y mueve la cabeza OLLO en el Port 1.
# Ajusta el rango seguro del servo antes de probar en hardware real.

HEAD_CENTER = 512
HEAD_MIN = 280
HEAD_MAX = 760


def clamp(value, lo, hi):
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def main():
    head = OLLO(1, const.OLLO_JOINT_POSITION)
    head.write(HEAD_CENTER)

    prev_value = -1
    while True:
        # 61 = Received Remocon Data en CM-550
        value = etc.read16(61)
        arrived = etc.read8(63)
        if arrived == 1 and value != prev_value:
            head.write(clamp(value, HEAD_MIN, HEAD_MAX))
            prev_value = value
            etc.write8(63, 0)
        delay(20)


main()
