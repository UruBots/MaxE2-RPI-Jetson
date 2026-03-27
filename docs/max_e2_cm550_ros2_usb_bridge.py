from pycm import *

# ============================================================
# MAX E2 / CM-550 - ROS 2 USB bridge task
# ------------------------------------------------------------
# Protocolo esperado por rc.read():
#   10000 + motion_page   -> ejecuta motion.play(page)
#   20000                 -> LED OFF
#   20001                 -> LED RED
#   20002                 -> LED BLUE
#   20003                 -> LED MAGENTA
#   30000 + head_raw      -> cabeza OLLO raw (0..1023), con clamp
#   40000                 -> postura lista (ready / stand)
#   40001                 -> postura agachada / fight-ready
#   40002                 -> torque ON
#   40003                 -> torque OFF
#   40004                 -> stop motion
#
# Pensado para MAX E2 real con 17 motores y conexión USB.
# Sin smart app, sin rpi.mode(), sin streaming.
# ============================================================

console(UART)

# ---------- Estado ----------
class CVar:
    IsTorqOn = False
    nPos_Servo = 512

# ---------- Protocolo ROS 2 / Remocon ----------
ROS_MOTION_BASE = 10000
ROS_MOTION_MAX = 10999

ROS_LED_OFF = 20000
ROS_LED_RED = 20001
ROS_LED_BLUE = 20002
ROS_LED_MAGENTA = 20003

ROS_HEAD_BASE = 30000
ROS_HEAD_MIN = ROS_HEAD_BASE
ROS_HEAD_MAX = ROS_HEAD_BASE + 1023
ROS_HEAD_CENTER = 512

ROS_CMD_READY = 40000
ROS_CMD_FIGHT_READY = 40001
ROS_CMD_TORQUE_ON = 40002
ROS_CMD_TORQUE_OFF = 40003
ROS_CMD_STOP = 40004

# Ajuste fino de rango de cabeza para no forzar mecánica
ROS_HEAD_CLAMP_MIN = 280
ROS_HEAD_CLAMP_MAX = 760

nMotion_Ready = -1

# ---------- Utilidades ----------
def Clamp(nValue, nMin, nMax):
    if nValue < nMin:
        return nMin
    if nValue > nMax:
        return nMax
    return nValue

def Setup_Speed(nID, nValue):
    DXL(nID).write32(112, nValue)

def LedPwm(nRed, nBlue):
    OLLO(2, const.OLLO_RED_BRIGHTNESS).write(round(nRed))
    OLLO(2, const.OLLO_BLUE_BRIGHTNESS).write(round(nBlue))

def TorqAll(IsOn):
    global nMotion_Ready
    if IsOn:
        dxlbus.torque_on()
        CVar.IsTorqOn = True
    else:
        dxlbus.torque_off()
        CVar.IsTorqOn = False
        nMotion_Ready = -1

def PositionUpdate(timeout_ms=1500):
    # En algunos setups este flag puede tardar; agrego timeout
    etc.write8(65, 3)
    t0 = millis()
    while True:
        if etc.read8(65) == 0:
            return True
        if (millis() - t0) > timeout_ms:
            return False
        delay(5)

def Motion_Play(nMotionIndex, nNextMotion = 0):
    if nMotionIndex <= 0:
        motion.play(int(nMotionIndex))
    else:
        Setup_Speed(254, 0)
        if nNextMotion == 0:
            motion.play(int(nMotionIndex))
        else:
            motion.play(int(nMotionIndex), int(nNextMotion))

def Motion_Wait(timeout_ms=10000):
    t0 = millis()
    while motion.status():
        if (millis() - t0) > timeout_ms:
            break
        delay(5)

def Motion_Play_And_Wait(nMotionIndex, nNextMotion = 0, timeout_ms=10000):
    Motion_Play(nMotionIndex, nNextMotion)
    Motion_Wait(timeout_ms)

def Motion_Stop():
    Motion_Play(-3)

def PlayRosMotionPage(page):
    page = int(page)
    # Some MAX E2 walk motions work more reliably as start + loop.
    if page == 103:
        Motion_Play(101, 103)
    else:
        Motion_Play(page)

def Motion_Ready(nInit = 1):
    # nInit = 1 -> ready/stand
    # nInit = 2 -> fight-ready / crouch
    global nMotion_Ready

    if CVar.IsTorqOn == False:
        TorqAll(True)

    PositionUpdate()

    if nInit == 2:
        Motion_Play_And_Wait(2)
    else:
        if nMotion_Ready < 0:
            Motion_Play_And_Wait(2)
            Motion_Play_And_Wait(16)
        else:
            if nInit != nMotion_Ready:
                if nInit != 2:
                    Motion_Play_And_Wait(16)
        Motion_Play_And_Wait(1)

    nMotion_Ready = nInit

def SetHeadRaw(nHead):
    nHead = Clamp(int(nHead), ROS_HEAD_CLAMP_MIN, ROS_HEAD_CLAMP_MAX)
    CVar.nPos_Servo = nHead
    OLLO(1, const.OLLO_JOINT_POSITION).write(nHead)

def InitBridge():
    # Importante:
    # 35 = Task Print Port -> BLE
    # 43 = Remote Port     -> USB
    # Así rc.read() recibe por USB y no mezclamos print con remocon.
    etc.write8(35, 0)
    etc.write8(43, 2)
    delay(50)

    # Humanoid vertical
    eeprom.imu_type(0)

    # Estado inicial seguro
    TorqAll(False)
    delay(100)

    # Config común de bus
    DXL(254).write8(10, 0)   # velocity based profile
    DXL(254).write8(12, 255) # clear secondary id
    DXL(254).write8(11, 3)   # position mode
    delay(20)

    TorqAll(True)
    delay(100)

    # Apaga LED de body y centra cabeza
    DXL(254).write8(65, 0)
    LedPwm(0, 0)
    # Ajusta ROS_HEAD_CENTER si tu horn de cabeza no queda centrado en 512.
    SetHeadRaw(ROS_HEAD_CENTER)

    # Lleva a postura lista para dejarlo arrancado estable
    Motion_Ready(1)

def HandleRosRemocon():
    if rc.received() != True:
        return False

    nValue = int(rc.read())

    # Motion pages
    if (nValue >= ROS_MOTION_BASE) and (nValue <= ROS_MOTION_MAX):
        PlayRosMotionPage(int(nValue - ROS_MOTION_BASE))
        return True

    # Head raw
    if (nValue >= ROS_HEAD_MIN) and (nValue <= ROS_HEAD_MAX):
        SetHeadRaw(int(nValue - ROS_HEAD_BASE))
        return True

    # LEDs
    if nValue == ROS_LED_OFF:
        LedPwm(0, 0)
        return True
    if nValue == ROS_LED_RED:
        LedPwm(100, 0)
        return True
    if nValue == ROS_LED_BLUE:
        LedPwm(0, 100)
        return True
    if nValue == ROS_LED_MAGENTA:
        LedPwm(100, 100)
        return True

    # Control commands
    if nValue == ROS_CMD_READY:
        Motion_Ready(1)
        return True
    if nValue == ROS_CMD_FIGHT_READY:
        Motion_Ready(2)
        return True
    if nValue == ROS_CMD_TORQUE_ON:
        TorqAll(True)
        return True
    if nValue == ROS_CMD_TORQUE_OFF:
        TorqAll(False)
        return True
    if nValue == ROS_CMD_STOP:
        Motion_Stop()
        return True

    return False

# ---------- Main ----------
InitBridge()

while True:
    HandleRosRemocon()
    delay(5)
