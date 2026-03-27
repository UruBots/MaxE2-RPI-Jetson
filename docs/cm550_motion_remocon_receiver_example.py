from pycm import *


# Ejemplo minimo para CM-550:
# lee Received Remocon Data (61) y ejecuta motions locales.
# Usa las mismas paginas extraidas del .mtn3 del MAX-E2.

CMD_STAND = 1
CMD_STAND_UP = 3
CMD_HELLO = 5
CMD_CLAP = 9
CMD_TURN_LEFT = 50
CMD_TURN_RIGHT = 51
CMD_SITDOWN = 60
CMD_WALK_START = 101
CMD_WALK_GO = 103
CMD_REVERSE_START = 156
CMD_REVERSE_GO = 158


def handle_command(value):
    if value in (
        CMD_STAND,
        CMD_STAND_UP,
        CMD_HELLO,
        CMD_CLAP,
        CMD_TURN_LEFT,
        CMD_TURN_RIGHT,
        CMD_SITDOWN,
    ):
        motion.play(value)
    elif value == CMD_WALK_START:
        motion.play(CMD_WALK_START, CMD_WALK_GO)
    elif value == CMD_WALK_GO:
        motion.play(CMD_WALK_GO)
    elif value == CMD_REVERSE_START:
        motion.play(CMD_REVERSE_START, CMD_REVERSE_GO)
    elif value == CMD_REVERSE_GO:
        motion.play(CMD_REVERSE_GO)


def main():
    prev_value = -1
    while True:
        value = etc.read16(61)
        arrived = etc.read8(63)
        if arrived == 1 and value != prev_value:
            handle_command(value)
            prev_value = value
            etc.write8(63, 0)
        delay(20)


main()
