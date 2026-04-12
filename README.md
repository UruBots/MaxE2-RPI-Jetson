# MAX-E2 — ROS 2 + CM-550 (Remocon)

Proyecto para operar un **ROBOTIS MAX-E2** (CM-550) desde una **Raspberry Pi 4** o **NVIDIA Jetson**: visión en el SBC y **actuación documentada solo vía paquetes Remocon** (estilo RC-100) por **USB o UART** hacia la CM-550, leídos en firmware con **`rc.read()`**.

**Alcance:** el flujo soportado usa **`cm550_remocon_bridge_node`** para cuerpo (motions), cabeza OLLO y LEDs. Código **legacy** (`dynamixel_node`, teleop hacia `/cmd_vel` sin Remocon) sigue en el repo pero **no** se describe aquí como despliegue actual.

## Tabla de contenidos

- [Qué incluye el workspace](#qué-incluye-el-workspace)
- [Hardware](#hardware)
- [Conexión SBC ↔ CM-550](#conexión-sbc--cm-550)
- [Control por Remocon](#control-por-remocon)
- [Firmware en la CM-550](#firmware-en-la-cm-550)
- [Instalación y compilación](#instalación-y-compilación)
- [Configuración (puerto serie)](#configuración-puerto-serie)
- [Visión y seguimiento → `/max/motion_cmd`](#visión-y-seguimiento--maxmotion_cmd)
- [Paquetes ROS 2](#paquetes-ros-2)
- [Launchers](#launchers)
- [Teleoperación por teclado](#teleoperación-por-teclado)
- [Depuración](#depuración)
- [Recursos](#recursos)

---

## Qué incluye el workspace

| Paquete | Rol |
|--------|-----|
| `max_interfaces` | Mensajes (`Detection`, `AprilTagArray`, …) |
| `max_vision` | Cámara, detectores (color, línea, forma, AprilTag), `debug_view_node`, `hsv_calibrator` |
| `max_control` | Trackers, `twist_to_motion_node`, `motion_mux_node`, `apriltag_head_search_node`, … |
| `max_driver` | **`cm550_remocon_bridge_node`** (principal), nodos legacy |
| `max_bringup` | Launches, `config/*.yaml`, documentación en `doc/` |

Índice de launches: [`src/max_bringup/doc/LAUNCHERS.md`](src/max_bringup/doc/LAUNCHERS.md).  
Teleop y **cámara por SSH / red**: [`src/max_bringup/doc/TELEOP_SSH.md`](src/max_bringup/doc/TELEOP_SSH.md).  
Teclas → páginas motion (101/103, `walk`): [`src/max_bringup/doc/MOTION_TELEOP.md`](src/max_bringup/doc/MOTION_TELEOP.md).  
Integración paso a paso: [`docs/INTEGRATION_MAX_E2.md`](docs/INTEGRATION_MAX_E2.md).

---

## Hardware

| Componente | Notas |
|------------|--------|
| SBC | Raspberry Pi 4 u otra placa Linux con ROS 2; **Jetson** soportado vía YAML de cámara (`max_params_jetson.yaml`) |
| CM-550 | Controlador MAX-E2; micro-USB al SBC (recomendado) |
| Cámara | USB V4L2 o CSI (Jetson: pipeline en YAML) |
| Batería | LiPo 3S típica para CM-550 y servos |

**UART GPIO (opcional):** cruzar TX/RX, 3.3 V, GND común. RPi suele usar `/dev/ttyAMA0` (tras `enable_uart=1` y desactivar consola serie); Jetson frecuentemente `/dev/ttyTHS1` (tras deshabilitar `nvgetty`). Ajusta **`port`** en el YAML del puente.

---

## Conexión SBC ↔ CM-550

### USB (recomendado)

```
SBC [USB-A] ─── cable micro-USB ─── [CM-550]
```

En Linux suele aparecer como **`/dev/ttyACM0`**. El firmware debe dejar el **Remote Port** en **USB** (`etc.write8(43, 2)` en los scripts de referencia; ver [Firmware](#firmware-en-la-cm-550)).

### UART

Misma idea de cableado que en el manual ROBOTIS (TX↔RX, 3.3 V). Configura el dispositivo (`port`) y **57600** baud (por defecto en el YAML del puente) según tu montaje.

### BLE

El CM-550 tiene BLE, pero **este repositorio no incluye** un puente ROS hacia BLE; el flujo documentado es **serie USB/UART** con `cm550_remocon_bridge_node`.

---

## Control por Remocon

```
SBC (ROS 2)
    │  /max/motion_cmd, /max/head_*, /max/led_*, …
    ▼
cm550_remocon_bridge_node  ──serie USB/UART──►  CM-550 (Play + script rc.read())
                                                      │
                                                      ▼
                                              motions · OLLO · LEDs
```

**Uso rápido:**

```bash
source /opt/ros/humble/setup.bash   # o jazzy
source install/setup.bash

ros2 launch max_bringup cm550_motion_bridge_launch.py
ros2 topic pub --once /max/motion_cmd std_msgs/msg/String "{data: walk}"
```

**Página motion directa** (sin nombre en `command_map`):

```bash
ros2 topic pub --once /max/motion_page_cmd std_msgs/msg/UInt16 "{data: 3}"
```

**Configuración principal:** `src/max_bringup/config/cm550_motion_bridge_max_e2.yaml` (`command_map`, `port`, baudrate, topics).

**Walk / página 103:** con el firmware de referencia (`docs/max_e2_cm550_ros2_usb_bridge.py`), un solo valor **10000+103** dispara **`Motion_Play(101, 103)`**. No dupliques en `command_sequences` como `walk:101|103` salvo que tu firmware lo requiera distinto; detalle en [MOTION_TELEOP.md](src/max_bringup/doc/MOTION_TELEOP.md).

**Mapa desde `.mtn3`:**

```bash
python3 scripts/extract_cm550_motion_map.py /ruta/a/tu_archivo.mtn3
```

**LED por topic** (entrecomillar `'off'`; si no, YAML lo interpreta como booleano):

```bash
ros2 topic pub --once /max/led_preset std_msgs/msg/String "{data: 'off'}"
```

---

## Firmware en la CM-550

Sin un script que llame a **`rc.read()`** y enrute USB, los paquetes del puente **no mueven el robot**, aunque el log muestre `Remocon enviado`.

1. Cargar **motions** (`.mtn3`) y el **`.py`** en la CM-550 (R+ Task 3.0 u otra herramienta ROBOTIS).
2. **MODE** verde → **START**; no dejar R+ Task/Manager conectados en paralelo al USB de control.
3. Script de referencia mínimo en este repo: **[`docs/max_e2_cm550_ros2_usb_bridge.py`](docs/max_e2_cm550_ros2_usb_bridge.py)**. Versión completa con UI ENG2: **`docs/01_ENG2_Max_E2_PY_ros2_ready.py`** (incluye `HandleRosRemocon` y `etc.write8(35,0); etc.write8(43,2)`).

Checklist operativo ampliado: [`docs/INTEGRATION_MAX_E2.md`](docs/INTEGRATION_MAX_E2.md) § 3.1.

---

## Instalación y compilación

**ROS 2:** Ubuntu con **Humble** o **Jazzy**. Sustituye `humble` por `jazzy` en los paquetes `ros-*` si corresponde.

```bash
sudo apt update
sudo apt install -y \
  python3-pip python3-colcon-common-extensions \
  ros-humble-cv-bridge ros-humble-image-transport \
  ros-humble-teleop-twist-keyboard ros-humble-image-view

pip3 install --user pyserial pupil-apriltags dynamixel-sdk numpy
```

`dynamixel-sdk` hace falta para compilar nodos legacy en `max_driver`; el **puente Remocon** solo necesita **pyserial** en runtime.

```bash
cd /ruta/al/workspace
colcon build --symlink-install
source install/setup.bash
```

**Jetson:** suele venir OpenCV/GStreamer en JetPack; usa  
`config/max_params_jetson.yaml` en los launches que aceptan `config_file:=...`.

---

## Configuración (puerto serie)

1. Conectar USB; comprobar `ls -l /dev/ttyACM*`.
2. Usuario en grupo **`dialout`**: `sudo usermod -aG dialout $USER` (cerrar sesión después).
3. En **`cm550_motion_bridge_max_e2.yaml`**, revisar `cm550_remocon_bridge_node/ros__parameters/port` si no es `ttyACM0`.

**UART en RPi:** `enable_uart=1` y desactivar login por consola serie (`raspi-config`); dispositivo típico `/dev/ttyAMA0`.  
**Jetson:** deshabilitar `nvgetty` si usas UART; dispositivo típico `/dev/ttyTHS1`.

En el flujo Remocon **no** se manda Protocolo 2.0 a los servos desde ROS; el bus lo gobierna el firmware de la CM-550.

---

## Visión y seguimiento → `/max/motion_cmd`

Los nodos de visión publican detecciones; los de control (`tracker_node`, `line_tracker_node`, `action_executor_node`, …) pueden usar **`output_mode: motion`** para publicar **strings** de acción en **`/max/motion_cmd`**, que el puente traduce a Remocon.

**YAML habitual:** `src/max_bringup/config/max_params_motion.yaml` (cámara + trackers en modo motion).

**Varias fuentes** (teleop + visión): `motion_mux_launch.py` y topics del tipo `/max/motion_cmd_teleop`, etc. (ver LAUNCHERS.md).

**Calibración HSV** (en lugar de pegar scripts sueltos):

```bash
ros2 run max_vision hsv_calibrator
```

Launches de visión + cuerpo por Remocon: `line_follow_motion_launch.py`, `shape_track_motion_launch.py`, `apriltag_action_motion_launch.py`, `apriltag_head_search_launch.py` (todos en `max_bringup`).

---

## Paquetes ROS 2

```
src/
├── max_interfaces/    # msgs/srv
├── max_vision/        # detector_*, apriltag_*, debug_view, hsv_calibrator
├── max_control/       # trackers, twist_to_motion, motion_mux, failsafe, …
├── max_driver/        # cm550_remocon_bridge_node (+ legacy)
└── max_bringup/       # launch/, config/, doc/, scripts/
```

### max_driver (despliegue actual)

- **`cm550_remocon_bridge_node`** — Entradas: `/max/motion_cmd`, `/max/motion_page_cmd`, `/max/head_*`, `/max/led_*`, `/max/profile_velocity`. Salida: paquetes Remocon por serie. Un solo proceso, un solo puerto.

**Legacy (no flujo Remocon del cuerpo):** `dynamixel_node`, `engineer_joint_node`, `led_ollo_bridge_node` (SDK; los launches `head_ollo_bridge` / `led_ollo_bridge` usan en realidad **`cm550_remocon_bridge_node`** con YAML dedicado).

### max_control (extracto)

- **`twist_to_motion_node`** — `/cmd_vel` → `/max/motion_cmd` (teleop CM-550).
- **`tracker_node`**, **`line_tracker_node`**, **`action_executor_node`** — `output_mode: motion` → `/max/motion_cmd`.
- **`motion_mux_node`**, **`failsafe_node`**, **`apriltag_head_search_node`**, **`joint_teleop_node`** (Engineer, no Remocon del cuerpo).

### max_vision (extracto)

- **`detector_node`**, **`line_detector_node`**, **`shape_detector_node`**, **`apriltag_detector_node`** — publican topics bajo `/max/...`.
- **`debug_view_node`** — imagen compuesta para depuración.
- **`hsv_calibrator`** — calibración HSV interactiva.

---

## Launchers

Resumen en [**`src/max_bringup/doc/LAUNCHERS.md`**](src/max_bringup/doc/LAUNCHERS.md).

**Remocon (soportado):**

| Launch | Uso breve |
|--------|-----------|
| `cm550_motion_bridge_launch.py` | Solo puente |
| `preflight_launch.py` | Comprobar cámara y serie |
| `teleop_cm550_launch.py` | Teclado + mapper + puente |
| `motion_mux_launch.py` | Multiplexar fuentes hacia `/max/motion_cmd` |
| `line_follow_motion_launch.py` / `shape_track_motion_launch.py` / `apriltag_action_motion_launch.py` | Visión → motions |
| `apriltag_head_search_launch.py` | AprilTag + cabeza + cuerpo |
| `head_ollo_bridge_launch.py` / `led_ollo_bridge_launch.py` | Cabeza / LED vía **mismo** `cm550_remocon_bridge_node` |
| `debug_image_view_launch.py` | Vistas de imagen (requiere `image_view`) |

**Legacy:** `max_launch.py`, `teleop_launch.py`, `line_follow_launch.py`, … (ruedas `dynamixel_node`).

**Opcional Engineer:** `engineer_joint_launch.py`, `engineer_joints_teleop_launch.py`.

---

## Teleoperación por teclado

`teleop_twist_keyboard` **necesita TTY**. `ros2 launch` a menudo **no** lo da al nodo hijo.

**Escritorio o `ssh -X`:**

```bash
ros2 launch max_bringup teleop_cm550_launch.py teleop_prefix:='xterm -hold -e '
# sudo apt install xterm
```

**Un solo SSH sin gráficos** (mapper + puente en segundo plano, teclado al frente):

```bash
bash "$(ros2 pkg prefix max_bringup)/share/max_bringup/scripts/teleop_cm550_one_terminal.sh"
```

(Requiere `colcon build`/`install` de `max_bringup`.)

**Dos terminales / `include_teleop:=false`:** ver [**TELEOP_SSH.md**](src/max_bringup/doc/TELEOP_SSH.md).

---

## Depuración

```bash
ros2 topic list
ros2 topic echo /cmd_vel
ros2 topic echo /max/motion_cmd
```

Si el puente loguea `Remocon enviado: value=10103` y el robot no camina, el problema está en **firmware / `.mtn3` / modo Play**, no en ROS; ver [MOTION_TELEOP.md](src/max_bringup/doc/MOTION_TELEOP.md) y [INTEGRATION_MAX_E2.md](docs/INTEGRATION_MAX_E2.md).

```bash
ros2 topic pub --once /max/motion_cmd std_msgs/msg/String "{data: walk}"
ros2 param list /cm550_remocon_bridge_node
```

---

## Recursos

- [CM-550 e-Manual](https://emanual.robotis.com/docs/en/parts/controller/cm-550/)
- [MicroPython `pycm`](https://emanual.robotis.com/docs/en/edu/pycm/)
- [Foro ROBOTIS](https://forum.robotis.com/) · [Discord ROBOTIS](https://discord.gg/robotis)
- Guía local: [**docs/INTEGRATION_MAX_E2.md**](docs/INTEGRATION_MAX_E2.md)
