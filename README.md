# MAX-E2 — ROS 2 + CM-550 (Remocon)

Proyecto para operar un robot **ROBOTIS MAX-E2** (CM-550) desde una **Raspberry Pi 4B** o **NVIDIA Jetson Nano**: visión por computadora en el SBC y **un único camino de actuación documentado: paquetes Remocon** (estilo RC-100) por USB/UART hacia la CM-550, consumidos en firmware con `rc.read()`.

> **Alcance del proyecto:** la documentación y los flujos recomendados usan **solo** `cm550_remocon_bridge_node` para mover el cuerpo (motions), cabeza OLLO y LEDs. No se documenta aquí el control de ruedas vía DYNAMIXEL SDK/bypass ni el bus directo U2D2; parte del código histórico (`dynamixel_node`, launches `*_launch.py` sin `motion`) permanece en el repositorio pero **no forma parte del despliegue soportado**.

## Tabla de contenidos

- [Elección de SBC: RPi 4B vs Jetson Nano](#elección-de-sbc-rpi-4b-vs-jetson-nano)
- [Hardware](#hardware)
- [Conexión SBC - CM-550](#conexión-sbc---cm-550)
  - [Método 1: USB (recomendado)](#método-1-usb-recomendado)
  - [Método 2: UART Serial (GPIO)](#método-2-uart-serial-gpio)
  - [Método 3: BLE inalámbrico](#método-3-ble-inalámbrico)
- [Control por Remocon](#control-por-remocon)
- [Instalación](#instalación)
  - [Raspberry Pi 4B](#raspberry-pi-4b)
  - [Jetson Nano](#jetson-nano)
- [Configuración](#configuración)
  - [Conexión USB](#conexión-usb)
  - [Conexión UART (RPi)](#conexión-uart-rpi)
  - [Conexión UART (Jetson Nano)](#conexión-uart-jetson-nano)
  - [CM-550 y bus Dynamixel](#cm-550-y-bus-dynamixel)
- [Visión y seguimiento (→ motions)](#visión-y-seguimiento--motions)
- [Launchers (max_bringup)](src/max_bringup/doc/LAUNCHERS.md)
- [Recursos](#recursos)

---

## Elección de SBC: RPi 4B vs Jetson Nano

Ambas placas son compatibles con el CM-550 y el DYNAMIXEL SDK. El libro oficial de ROBOTIS *"Projects Guide for ROBOTIS Engineer: Volume 2"* cubre explícitamente ambas plataformas. La conexión física y el software son prácticamente idénticos; la diferencia está en el rendimiento de visión por computadora.

### Comparación

| Spec | Raspberry Pi 4B | Jetson Nano (B01) |
|---|---|---|
| **CPU** | Broadcom BCM2711, Cortex-A72 4-core @ 1.5 GHz | NVIDIA Tegra X1, Cortex-A57 4-core @ 1.43 GHz |
| **GPU** | VideoCore VI (sin CUDA) | 128-core Maxwell (CUDA 10.2) |
| **RAM** | 2/4/8 GB LPDDR4 | 4 GB LPDDR4 (compartida CPU/GPU) |
| **Almacenamiento** | microSD | microSD (o NVMe con carrier board) |
| **USB** | 2x USB 3.0, 2x USB 2.0 | 4x USB 3.0 |
| **UART GPIO** | Pin 8 (TXD), Pin 10 (RXD), Pin 6 (GND) | Pin 8 (TXD), Pin 10 (RXD), Pin 6 (GND) |
| **Dispositivo UART** | `/dev/ttyAMA0` | `/dev/ttyTHS1` |
| **Nivel lógico** | 3.3V (no tolera 5V) | 3.3V (no tolera 5V) |
| **Consumo** | ~7.6W max | ~5-10W (modo 5W/10W) |
| **Precio** | ~$55-75 USD | ~$59-99 USD |
| **OS** | Raspberry Pi OS (Debian) | JetPack (Ubuntu 18.04/20.04) |

### Rendimiento en visión por computadora

| Métrica | RPi 4B (CPU) | Jetson Nano (GPU/TensorRT) |
|---|---|---|
| **Object detection FPS** | 4-9 FPS | 21-40 FPS |
| **Latencia end-to-end** | 112-238 ms | 38-47 ms |
| **Throttling térmico** | Sí (82°C bajo carga) | No (47-54°C con fan) |
| **Rendimiento sostenido** | Baja ~40% tras 5 min | Estable |
| **Tracking HSV (OpenCV)** | 30+ FPS | 30+ FPS |
| **YOLO / SSD inference** | ~5 FPS (CPU) | ~25 FPS (TensorRT INT8) |
| **CUDA disponible** | No | Sí (128 cores Maxwell) |
| **TensorRT** | No | Sí (FP16/INT8 optimizado) |

### Recomendación

| Caso de uso | Mejor opción |
|---|---|
| Tracking por color (HSV) simple | Ambas (RPi es suficiente) |
| Detección con deep learning (YOLO, SSD) | **Jetson Nano** (3-5x más rápido) |
| Presupuesto limitado | RPi 4B (más accesorios disponibles) |
| Proyecto con ROS | Ambas |
| Máximo rendimiento de CV en real-time | **Jetson Nano** |
| Comunidad y documentación más amplia | RPi 4B |

> **Conclusión**: Si solo necesitas tracking por color (HSV + contornos), la RPi 4B es suficiente y más sencilla de configurar. Si planeas usar modelos de deep learning (YOLO, SSD-MobileNet, etc.) para detección de objetos, la **Jetson Nano es significativamente superior** gracias a su GPU CUDA y TensorRT.

---

## Hardware

| Componente | Descripción |
|---|---|
| SBC | Raspberry Pi 4B **o** NVIDIA Jetson Nano (B01/2GB) |
| ROBOTIS CM-550 | Controlador de servos Dynamixel (ARM Cortex-M4, 168 MHz) |
| Servos Dynamixel | Serie X (TTL, half-duplex, Protocol 2.0) |
| Cámara | Pi Camera Module v2, webcam USB, o CSI camera (Jetson) |
| Cable USB | Micro USB a USB-A (conexión CM-550 a SBC) |
| Batería LiPo 3S | 11.1V para alimentar CM-550 y servos |

### CM-550 - Especificaciones relevantes

| Spec | Valor |
|---|---|
| MCU | ARM Cortex-M4 (168 MHz, 32 bit) |
| Voltaje operación | 6.5 ~ 15V (recomendado 11.1V LiPo 3S) |
| Puertos Dynamixel | 6x TTL 3-pin (serie X) |
| Puertos I/O | 5x ROBOTIS 5-pin |
| Comunicación | BLE integrado, UART 4-pin, Micro USB |
| Sensores internos | IMU (gyro + accel), mic, temperatura, voltaje |
| Protocolo | DYNAMIXEL Protocol 2.0 |
| ID por defecto | 200 |

> **Nota:** XL-320 NO es compatible con CM-550.

---

## Conexión SBC - CM-550

Los tres métodos de conexión funcionan tanto con RPi 4B como con Jetson Nano.

### Método 1: USB (recomendado)

La forma más sencilla. Conectar un cable micro USB desde el CM-550 a cualquier puerto USB del SBC.

```
SBC [USB-A] ──── cable ──── [Micro USB] CM-550
```

- Aparece como `/dev/ttyACM0` en Linux (tanto RPi como Jetson)
- El CM-550 tiene soporte nativo para RPi en su firmware:
  - **Address 156** (`USB OTG Connected`): 0 = desconectado, 1 = conectado
  - **Address 157** (`Rpi Connected`): 0 = desconectado, 2 = conectado
  - **Address 164-167** (`Rpi IP 1-4`): IP de la RPi conectada

### Método 2: UART Serial (GPIO)

Conexión directa por GPIO usando el puerto UART de 4 pines del CM-550.

#### Pinout del puerto UART del CM-550

| Pin | Función | Voltaje |
|-----|---------|---------|
| 1 | TXD (Transmit) | 3.3V |
| 2 | RXD (Receive) | 3.3V |
| 3 | VCC | 2.7 ~ 3.6V |
| 4 | GND | 0V |

#### Cableado CM-550 a SBC

Los pines del GPIO header son iguales en RPi 4B y Jetson Nano:

| CM-550 UART | SBC GPIO Header (RPi 4B / Jetson Nano) |
|---|---|
| TXD (Pin 1) | RXD (Pin 10) |
| RXD (Pin 2) | TXD (Pin 8) |
| GND (Pin 4) | GND (Pin 6) |

> **Importante:** TX y RX se cruzan. Ambas placas operan a 3.3V y NO toleran 5V. El VCC del CM-550 opera a 2.7-3.6V, compatible con 3.3V (no necesita level shifter).

Se puede usar el cable **LN-101** de ROBOTIS o fabricar un cable propio.

#### Registros del CM-550 a configurar para UART

| Address | Registro | Valor | Descripción |
|---|---|---|---|
| 13 | Baud Rate (UART) | 0-7 | 0: 9600, 1: 57600 (default), 2: 115200, 3: 1Mbps |
| 35 | Task Print Port | 1 (UART) | Monitor serial por UART |
| 36 | App Port | 1 (UART) | Puerto de aplicación por UART |
| 43 | Remote Port | 1 (UART) | Puerto de control remoto por UART |

#### Configurar UART en RPi 4B

Editar `/boot/config.txt`:

```ini
enable_uart=1
dtoverlay=disable-bt
```

Deshabilitar consola serial:

```bash
sudo raspi-config
# -> Interface Options -> Serial Port
# -> Login shell over serial: NO
# -> Serial port hardware enabled: YES
```

El dispositivo serie será `/dev/ttyAMA0`.

#### Configurar UART en Jetson Nano

Deshabilitar la consola serial del servicio `nvgetty`:

```bash
sudo systemctl stop nvgetty
sudo systemctl disable nvgetty
sudo udevadm trigger
# Reiniciar para aplicar
sudo reboot
```

El dispositivo serie será `/dev/ttyTHS1`.

Verificar acceso:

```bash
ls -l /dev/ttyTHS1
# Si no tienes permisos:
sudo usermod -aG dialout $USER
```

### Método 3: BLE inalámbrico

El CM-550 incluye un módulo BLE esclavo integrado. Se puede usar con:

- **BT-410 Dongle** de ROBOTIS conectado a USB del SBC
- Bluetooth integrado de la RPi 4B (requiere librería BLE compatible)
- Adaptador USB Bluetooth en Jetson Nano (no tiene BT integrado)

---

## Control por Remocon

El SBC envía paquetes remotos tipo **RC-100** por serial USB/UART al **CM-550**; el script MicroPython en la controladora los recibe con **`rc.read()`** y ejecuta motions, cabeza OLLO y LEDs según tu tarea.

```
SBC (ROS 2 + visión + pySerial)
    │ micro-USB o UART
    ▼
cm550_remocon_bridge_node
    │ paquete Remocon
    ▼
CM-550 (Play + script con rc.read())
    │ TTL / OLLO
    ▼
Cuerpo (motions) · servos · cabeza · LEDs
```

Registro habitual: **Address 43** (`Remote Port`): `0` BLE · `1` UART · `2` USB.

Este modo mantiene activas **TASK**, **MicroPython** y **MOTION**, y reutiliza las motions `.mtn3` del kit **ROBOTIS ENGINEER**.

Uso rápido:

```bash
ros2 launch max_bringup cm550_motion_bridge_launch.py
ros2 topic pub --once /max/motion_cmd std_msgs/msg/String "{data: walk}"
ros2 topic pub --once /max/motion_page_cmd std_msgs/msg/UInt16 "{data: 3}"
```

Notas:
- Ajusta `command_map` en `src/max_bringup/config/cm550_motion_bridge_max_e2.yaml`
  para que coincida con las páginas reales cargadas en tu `CM-550`.
- Si una motion necesita varias páginas, usa `command_sequences`, por ejemplo
  `walk:101|103` para `start -> go`.
- Este flujo asume que la `CM-550` ya tiene descargadas las motions `.mtn3` del robot
  y que el script en la controladora usa `rc.read()`.
- Si quieres integrarlo con `action_executor_node`, remapea `command_topic` a
  `/max/current_action` y usa nombres compatibles en `command_map`.
- Puedes extraer una primera versión del `command_map` desde un `.mtn3` con:

```bash
python3 scripts/extract_cm550_motion_map.py /ruta/a/01_ENG2_Max_E2_MO.mtn3
```

Script listo para la `CM-550`:
- `docs/01_ENG2_Max_E2_PY_ros2_ready.py`

Checklist de runtime:
- `MODE` rojo: `Manage`, el script no corre
- `MODE` verde parpadeando: `Play`, esperando `START`
- `MODE` verde fijo o deja de parpadear: el script debería estar corriendo
- conecta el USB al host recién después de dejar la controladora en `Play + START`

### Cabeza OLLO / Pololu

En el `MAX-E2` oficial, la cabeza no aparece controlada como un `XL430` adicional
sino como un `OLLO Joint` conectado al `Port 1` de la `CM-550`.

Uso rápido desde ROS 2:

```bash
ros2 launch max_bringup head_ollo_bridge_launch.py
ros2 topic pub --once /max/head_preset std_msgs/msg/String "{data: center}"
ros2 topic pub --once /max/head_cmd_raw std_msgs/msg/UInt16 "{data: 680}"
ros2 topic pub --once /max/head_cmd std_msgs/msg/Float32 "{data: 0.4}"
```

Este bridge usa el mismo `cm550_remocon_bridge_node` y envía un paquete remoto
al script de la `CM-550`. Para mover la cabeza, la controladora debe ejecutar un
script que use `rc.read()` y haga:

```python
OLLO(1, const.OLLO_JOINT_POSITION).write(valor)
```

Dejamos un ejemplo minimo en:
`docs/cm550_head_ollo_receiver_example.py`

### LEDs desde ROS 2

El `MAX-E2` oficial usa un LED bicolor en `OLLO(2)` y también permite usar
los LEDs de los `DYNAMIXEL` desde el Python oficial.

Para el LED OLLO dejamos un bridge ROS 2:

```bash
ros2 launch max_bringup led_ollo_bridge_launch.py
ros2 topic pub --once /max/led_preset std_msgs/msg/String "{data: red}"
ros2 topic pub --once /max/led_preset std_msgs/msg/String "{data: blue}"
ros2 topic pub --once /max/led_preset std_msgs/msg/String "{data: magenta}"
ros2 topic pub --once /max/led_preset std_msgs/msg/String "{data: off}"
```

Config:
- `src/max_bringup/config/led_ollo_bridge.yaml`

El receptor de ejemplo para la `CM-550` ya soporta cabeza + LEDs en:
- `docs/cm550_head_ollo_receiver_example.py`

### Barrido de cabeza con AprilTag

Hay un flujo listo para:
- barrer la cabeza de izquierda a derecha
- detener el barrido cuando aparezca un AprilTag
- mandar `turn_left` / `turn_right` al cuerpo
- recentrar la cabeza con el preset `center`

Uso:

```bash
ros2 launch max_bringup apriltag_head_search_launch.py
```

Nodo principal:
- `apriltag_head_search_node`

Topics usados:
- entrada: `/max/apriltag_detections`
- salida cabeza: `/max/head_cmd_raw`, `/max/head_preset`
- salida cuerpo: `/max/motion_cmd`

Archivo de parámetros:
- `src/max_bringup/config/apriltag_head_search.yaml`

---

## Instalación

### Raspberry Pi 4B

**Requisitos:** Raspberry Pi OS 64-bit, Python 3.9+

```bash
sudo apt-get update && sudo apt-get upgrade -y

# OpenCV y dependencias de video
sudo apt-get install -y python3-pip python3-opencv libopencv-dev

# Herramientas de desarrollo
sudo apt-get install -y python3-dev python3-numpy

# pySerial (puente remocon) y NumPy; dynamixel-sdk hace falta para compilar el workspace (nodos legacy en repo)
pip3 install dynamixel-sdk pyserial numpy
```

Verificar:

```bash
python3 -c "import cv2; print('OpenCV', cv2.__version__)"
python3 -c "import dynamixel_sdk; print('DYNAMIXEL SDK OK')"
```

### Jetson Nano

**Requisitos:** JetPack 4.6+ (Ubuntu 18.04), Python 3.6+

JetPack ya incluye OpenCV compilado con soporte CUDA y GStreamer. No es necesario instalar OpenCV manualmente.

```bash
sudo apt-get update && sudo apt-get upgrade -y

# Verificar que OpenCV con CUDA ya está disponible (viene con JetPack)
python3 -c "import cv2; print('OpenCV', cv2.__version__); print('CUDA:', cv2.cuda.getCudaEnabledDeviceCount())"

# Herramientas de desarrollo
sudo apt-get install -y python3-pip python3-dev python3-serial

# Ver nota RPi: dynamixel-sdk solo requerido para build completo del repo
pip3 install dynamixel-sdk pyserial numpy
```

#### TensorRT (para deep learning inference)

TensorRT viene preinstalado con JetPack. Para usarlo con modelos de detección:

```bash
# Verificar TensorRT
python3 -c "import tensorrt; print('TensorRT', tensorrt.__version__)"

# Instalar torch2trt para convertir modelos PyTorch
sudo apt-get install -y libopenblas-base libopenmpi-dev
pip3 install --pre torch torchvision --extra-index-url https://developer.download.pytorch.org/whl/nightly/cpu

# jetson-inference (framework de NVIDIA para detección/tracking)
sudo apt-get install -y git cmake
git clone --recursive https://github.com/dusty-nv/jetson-inference
cd jetson-inference && mkdir build && cd build
cmake .. && make -j$(nproc) && sudo make install
```

#### Captura de cámara optimizada en Jetson Nano

Usar GStreamer pipeline en lugar de V4L2 para menor latencia con CSI cameras:

```python
import cv2

# CSI camera (Pi Camera Module conectada al puerto CSI del Jetson)
def gstreamer_pipeline(
    capture_width=640, capture_height=480, display_width=640,
    display_height=480, framerate=30, flip_method=0,
):
    return (
        f"nvarguscamerasrc ! "
        f"video/x-raw(memory:NVMM), width=(int){capture_width}, "
        f"height=(int){capture_height}, framerate=(fraction){framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width=(int){display_width}, height=(int){display_height}, "
        f"format=(string)BGRx ! videoconvert ! "
        f"video/x-raw, format=(string)BGR ! appsink"
    )

cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)

# USB webcam (alternativa más simple)
# cap = cv2.VideoCapture(0)
```

Verificar instalación completa:

```bash
python3 -c "import cv2; print('OpenCV', cv2.__version__)"
python3 -c "import dynamixel_sdk; print('DYNAMIXEL SDK OK')"
python3 -c "import tensorrt; print('TensorRT', tensorrt.__version__)"
```

---

## Configuración

### Conexión USB

1. Conectar CM-550 al SBC por cable micro USB
2. Encender el CM-550
3. Verificar detección:

```bash
ls /dev/ttyACM*
# Esperado: /dev/ttyACM0 (tanto en RPi como en Jetson)
```

4. Dar permisos al puerto serie:

```bash
sudo usermod -aG dialout $USER
# Reiniciar sesión para aplicar
```

### Conexión UART (RPi)

1. Cablear según la tabla de [Método 2](#método-2-uart-serial-gpio)
2. Configurar `/boot/config.txt` y `raspi-config` según las instrucciones
3. Reiniciar la RPi
4. Verificar:

```bash
ls /dev/ttyAMA*
# Esperado: /dev/ttyAMA0
```

### Conexión UART (Jetson Nano)

1. Cablear según la tabla de [Método 2](#método-2-uart-serial-gpio) (mismos pines: 8, 10, 6)
2. Deshabilitar la consola serial:

```bash
sudo systemctl stop nvgetty
sudo systemctl disable nvgetty
sudo udevadm trigger
sudo reboot
```

3. Verificar:

```bash
ls /dev/ttyTHS*
# Esperado: /dev/ttyTHS1
```

4. Dar permisos:

```bash
sudo usermod -aG dialout $USER
sudo chmod 666 /dev/ttyTHS1
```

### CM-550 y bus Dynamixel

En el flujo **Remocon**, el bus TTL y los modos de los servos los gestiona el **firmware** de la CM-550 (motions, tareas). Desde ROS **no** se envían comandos DYNAMIXEL Protocol 2.0 en runtime.

Para inspección o montaje mecánico puedes usar **DYNAMIXEL Wizard 2.0** u otras herramientas ROBOTIS fuera de este stack.

---

## Visión y seguimiento (→ motions)

### Concepto

```
┌──────────────┐   topics    ┌─────────────────────┐   Remocon   ┌─────────┐
│  SBC         │────────────▶│ cm550_remocon_bridge │───────────▶│ CM-550  │
│  (RPi/Jetson)│  /max/motion│       _node          │  serial    │ + motion│
│  ┌────────┐  │  _cmd …     └─────────────────────┘            └────┬────┘
│  │ Camera │  │                                                     │ TTL
│  └───┬────┘  │                                                     ▼
│  OpenCV /    │                                              [cuerpo · ruedas]
│  detección   │
│      │       │
│  tracker /   │
│  línea / tag │
└──────────────┘
```

Los nodos de control (`tracker_node`, `line_tracker_node`, `action_executor_node`, …) pueden publicar en modo **`motion`** (`output_mode: motion`) para enviar **nombres de acción** o páginas hacia `/max/motion_cmd`, que el puente traduce a paquetes Remocon.

### Flujo del algoritmo

1. **Captura**: leer frame de la cámara
2. **Detección**: HSV/contornos, AprilTag, línea, etc.
3. **Localización**: centroide, error respecto al centro del frame, ID de tag, etc.
4. **Control**: el nodo de control elige una **acción simbólica** o continúa el seguimiento
5. **Actuación**: publicación a **`/max/motion_cmd`** (y topics de cabeza si aplica); el puente Remocon la entrega a la CM-550
6. **Repetir**

### Estrategias de detección según plataforma

| Estrategia | RPi 4B | Jetson Nano | FPS esperados |
|---|---|---|---|
| HSV color mask + contornos | 30+ FPS | 30+ FPS | Ambas OK |
| Haar Cascades (OpenCV) | 10-15 FPS | 20-30 FPS | Ambas OK |
| SSD-MobileNet (TensorRT) | No viable | 25-40 FPS | Solo Jetson |
| YOLOv5/v8 nano (TensorRT) | No viable | 15-25 FPS | Solo Jetson |

### Parámetros a calibrar

| Variable | Descripción | Cómo calibrar |
|---|---|---|
| `LOWER_COLOR` / `UPPER_COLOR` | Rango HSV del objeto a trackear | Script de calibración HSV (ver abajo) |
| `MIN_CONTOUR_AREA` | Área mínima del contorno | Según tamaño/distancia del objeto |
| `DEAD_ZONE` | Zona central sin giro (píxeles) | Más grande = más estable |
| `command_map` / `command_sequences` | Nombre de acción → página(s) motion | `cm550_motion_bridge_max_e2.yaml` alineado con tus `.mtn3` |
| `output_mode` | `motion` vs velocidad Twist | En trackers: usar `motion` para Remocon |

### Script de calibración HSV

Ejecutar en la RPi con la cámara conectada para encontrar los rangos HSV del objeto:

```python
import cv2
import numpy as np

cap = cv2.VideoCapture(0)

def nothing(x):
    pass

cv2.namedWindow("Trackbars")
cv2.createTrackbar("L-H", "Trackbars", 0, 180, nothing)
cv2.createTrackbar("L-S", "Trackbars", 120, 255, nothing)
cv2.createTrackbar("L-V", "Trackbars", 70, 255, nothing)
cv2.createTrackbar("U-H", "Trackbars", 10, 180, nothing)
cv2.createTrackbar("U-S", "Trackbars", 255, 255, nothing)
cv2.createTrackbar("U-V", "Trackbars", 255, 255, nothing)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    l_h = cv2.getTrackbarPos("L-H", "Trackbars")
    l_s = cv2.getTrackbarPos("L-S", "Trackbars")
    l_v = cv2.getTrackbarPos("L-V", "Trackbars")
    u_h = cv2.getTrackbarPos("U-H", "Trackbars")
    u_s = cv2.getTrackbarPos("U-S", "Trackbars")
    u_v = cv2.getTrackbarPos("U-V", "Trackbars")

    lower = np.array([l_h, l_s, l_v])
    upper = np.array([u_h, u_s, u_v])
    mask = cv2.inRange(hsv, lower, upper)

    result = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)
    cv2.imshow("Result", result)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        print(f"LOWER = np.array([{l_h}, {l_s}, {l_v}])")
        print(f"UPPER = np.array([{u_h}, {u_s}, {u_v}])")
        break

cap.release()
cv2.destroyAllWindows()
```

### Tips de rendimiento

**Ambas plataformas:**
- Reducir resolución de captura a 320x240 para procesamiento más rápido
- Usar `cv2.resize()` si se quiere visualizar a mayor resolución
- Apuntar a 30+ FPS para control reactivo
- El tracking por color (HSV) es suficiente para muchos casos y corre bien en ambas

**RPi 4B:**
- Usar `picamera2` en lugar de `cv2.VideoCapture` para Pi Camera (menor latencia)
- Limitar detección a HSV/contornos o Haar Cascades
- Considerar reducir resolución a 160x120 si el procesamiento es pesado

**Jetson Nano:**
- Usar GStreamer pipeline para captura CSI (ver sección de instalación)
- Aprovechar TensorRT para modelos de deep learning (FP16/INT8)
- Usar `jetson-inference` de NVIDIA para detección con SSD-MobileNet en 10 líneas de Python
- Configurar modo de energía a 10W para máximo rendimiento: `sudo nvpmodel -m 0`
- Activar todos los cores: `sudo jetson_clocks`

---

## Recursos

### Documentación oficial ROBOTIS

- [CM-550 e-Manual](https://emanual.robotis.com/docs/en/parts/controller/cm-550/)
- [CM-550 MicroPython API](https://emanual.robotis.com/docs/en/edu/pycm/)
- [DYNAMIXEL SDK - Python en Linux](https://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/library_setup/python_linux/)
- [DYNAMIXEL Protocol 2.0](https://emanual.robotis.com/docs/en/dxl/protocol2/)

### Documentación Jetson Nano

- [Jetson Nano UART (JetsonHacks)](https://jetsonhacks.com/2019/10/10/jetson-nano-uart/)
- [Jetson Nano J41 GPIO Header Pinout](https://jetsonhacks.com/nvidia-jetson-nano-j41-header-pinout/)
- [jetson-inference (detección de objetos)](https://github.com/dusty-nv/jetson-inference)
- [Real-Time Object Detection on Jetson Nano (NVIDIA Blog)](https://developer.nvidia.com/blog/realtime-object-detection-in-10-lines-of-python-on-jetson-nano/)
- [JetsonHacksNano UART Demo](https://github.com/JetsonHacksNano/UARTDemo)

### Comunidad

- [Discord ROBOTIS](https://discord.gg/robotis) - soporte en tiempo real
- [Foro ROBOTIS - CM-550 + RPi 4](https://forum.robotis.com/t/connect-cm-550-to-rasbery-pi-4-0/1456)
- [Foro ROBOTIS - Comunicación C++ con CM-550](https://forum.robotis.com/t/communicate-with-cm550-over-c/1770)
- [DynamixelSDK GitHub Issues](https://github.com/ROBOTIS-GIT/DynamixelSDK/issues)
- [NVIDIA Developer Forums - Jetson Nano](https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/jetson-nano/76)

### Guías locales

- [`docs/INTEGRATION_MAX_E2.md`](docs/INTEGRATION_MAX_E2.md) — integración MAX-E2 + CM-550 + ROS 2

### Libros

- [Projects Guide to ROBOTIS ENGINEER Vol. 2 (CM-550 + RPi4B + Jetson Nano)](https://www.amazon.com/Projects-Guide-ROBOTIS-ENGINEER-Combined-ebook/dp/B09KQCH2FV) - cubre explícitamente Hexápodo con Jetson Nano y pan-tilt camera
- [Using ARDUINO with ROBOTIS Systems](https://www.amazon.com/Using-ARDUINO-ROBOTIS-Systems-Ngoc-ebook/dp/B0BPXGQ6YX)

### Videos

- [Communications & Control Options: Bioloid Premium Humanoid + RPi-4B](https://www.youtube.com/watch?v=e9VN78SFuE8)
- [Remocon Packet entre CM-530 y RPi](https://www.youtube.com/watch?v=uLiYTpxfRCE)

---

## Paquetes ROS2

El workspace agrupa **cinco paquetes**. La actuación documentada pasa por **`cm550_remocon_bridge_node`**; los nodos que publican `/cmd_vel` hacia `dynamixel_node` se mantienen como legado en el código.

```
max/                          # Workspace root
├── README.md
└── src/
    ├── max_interfaces/       # Mensajes y servicios custom (CMake)
    ├── max_vision/           # Captura de cámara + detección (Python)
    ├── max_control/          # Controlador de tracking (Python)
    ├── max_driver/           # Puente Remocon CM-550 + nodos legacy (Python)
    └── max_bringup/          # Launch files y configuración (Python)
```

### Arquitectura de nodos y topics (stack Remocon)

```
  /max/camera/image_raw                    /max/motion_cmd …
         │                                        │
┌────────┴────────┐   detección / línea / tag   ┌──┴──────────────────────────┐
│  max_vision     │ ───────────────────────────►│ max_control                    │
│  detector_* …   │                             │ tracker / line_tracker /       │
└────────┬────────┘                             │ action_executor …             │
         │                                     └──┬──────────────────────────┘
         │  (output_mode: motion)                  │  std_msgs/String → motion
         │                                        ▼
         │                               ┌─────────────────────┐
         └────────────────────────────►│cm550_remocon_bridge │
              /max/debug_image          │      _node          │──USB/UART──► CM-550
                                        └─────────────────────┘
```

Si un nodo publica **`/cmd_vel`** en lugar de motions, hace falta el camino legacy **`dynamixel_node`** (no incluido en el despliegue Remocon documentado aquí).

### max_interfaces

Mensajes y servicios custom:

| Tipo | Nombre | Descripción |
|---|---|---|
| msg | `Detection` | Resultado de detección: header, detected, cx, cy, area, frame_width, frame_height, confidence, label |
| msg | `LineDetection` | Detección de línea: header, detected, offset_x, angle, cx, cy, line_width, frame_width, frame_height, roi_y_start |
| msg | `AprilTagDetection` | Tag individual: tag_id, tag_family, cx, cy, size_px, decision_margin, hamming, corners[8], frame_width, frame_height |
| msg | `AprilTagArray` | Header + array de AprilTagDetection |
| msg | `DynamixelState` | Estado de un servo: id, present_position, present_velocity, present_temperature |
| msg | `DynamixelStateArray` | Header + array de DynamixelState |
| srv | `SetTorque` | Habilitar/deshabilitar torque para un servo (id, enable → success, message) |
| srv | `SetOperatingMode` | Cambiar modo operación de un servo (id, mode → success, message) |

### max_vision

**Nodos:**

- **`detector_node`** - Captura cámara, detecta objetos por color HSV, publica detecciones
  - Publica: `/max/detection`, `/max/camera/image_raw`, `/max/debug_image`
  - Soporta cámara USB (V4L2) y CSI (GStreamer pipeline para Jetson)

- **`line_detector_node`** - Detecta líneas para seguimiento de línea (ROI inferior, threshold adaptivo/binario)
  - Publica: `/max/line_detection`, `/max/line_debug_image`

- **`shape_detector_node`** - Detecta formas geométricas (ball, cube, rectangle, triangle) por contornos
  - Publica: `/max/detection`, `/max/shape_debug_image`

- **`apriltag_detector_node`** - Detecta AprilTags y publica sus IDs, posición y esquinas
  - Publica: `/max/apriltag_detections`, `/max/camera/image_raw`, `/max/apriltag_debug_image`
  - Usa `pupil-apriltags` (pip install pupil-apriltags)
  - Familias soportadas: tag36h11, tag25h9, tag16h5, tagStandard41h12, etc.
  - Configurable: quad_decimate, threads, sharpening, refine_edges

- **`debug_view_node`** - Composita todas las detecciones + HUD en una imagen para `rqt_image_view`
  - Suscribe: `/max/camera/image_raw`, `/max/detection`, `/max/line_detection`, `/max/apriltag_detections`, `/max/current_action`, `/cmd_vel`
  - Publica: `/max/debug_view`

- **`hsv_calibrator`** - Herramienta con trackbars OpenCV para calibrar rangos HSV

### max_control

**Nodos:**

- **`tracker_node`** - Convierte detecciones de objetos en comandos de velocidad
  - Suscribe: `/max/detection`
  - Publica: `/cmd_vel` (geometry_msgs/Twist)
  - Control proporcional: error normalizado → angular.z, área → linear.x
  - Modo búsqueda opcional (rotar cuando no hay target)
  - Soporta `output_mode: 'motion'` para publicar acciones a `/max/motion_cmd`

- **`line_tracker_node`** - Convierte detecciones de línea en comandos de velocidad
  - Suscribe: `/max/line_detection`
  - Publica: `/cmd_vel`
  - Soporta `output_mode: 'motion'` para publicar acciones a `/max/motion_cmd`

- **`joint_teleop_node`** - Teleop por teclado que publica `sensor_msgs/JointState` en `/max/joint_command` (humanoide Engineer)
  - Úsalo junto a `engineer_joint_node`; parámetros en `engineer_max_e2.yaml` (`joint_teleop_node`)

- **`action_executor_node`** - Mapea AprilTag IDs a acciones del robot
  - Suscribe: `/max/apriltag_detections`
  - Publica: `/cmd_vel`, `/max/current_action` (std_msgs/String)
  - Acciones predefinidas: `follow`, `stop`, `sprint`, `reverse`, `spin_left`, `spin_right`, `dance`
  - Mapeo configurable vía YAML: `tag_action_map: '0:follow,1:stop,2:spin_left,...'`
  - Selecciona el tag más grande (cercano) cuando hay múltiples
  - Soporta `output_mode: 'motion'` para publicar directamente a `/max/motion_cmd`

- **`apriltag_head_search_node`** - Barrido de cabeza + recentrado de cuerpo con AprilTag
  - Suscribe: `/max/apriltag_detections`
  - Publica: `/max/head_cmd_raw`, `/max/head_preset`, `/max/motion_cmd`, `/max/head_search_status`
  - Modo búsqueda: barre la cabeza de izquierda a derecha hasta encontrar un tag
  - Modo centrado: recentra la cabeza y manda `turn_left` / `turn_right` / `stop` al cuerpo
  - Parámetros en `config/apriltag_head_search.yaml`

### max_driver

**Nodo principal (despliegue Remocon):**

- **`cm550_remocon_bridge_node`** — ROS 2 → paquetes **Remocon** hacia la CM-550 (`rc.read()` en firmware).
  - Entradas típicas: `/max/motion_cmd`, `/max/motion_page_cmd`, `/max/head_*`, `/max/led_*`
  - Salidas de estado: `/max/motion_status`, `/max/motion_last_page`, etc.
  - Un solo puerto serie (USB o UART) para cuerpo, cabeza OLLO y LEDs.

**Nodos legacy (siguen en el repo; no son el flujo documentado):**

- **`dynamixel_node`** — `/cmd_vel` → ruedas por protocolo DYNAMIXEL (sin Remocon).
- **`engineer_joint_node`** — articulaciones por `/max/joint_command` (no usar junto a `dynamixel_node` en el mismo bus).

### max_bringup

Índice detallado: [`src/max_bringup/doc/LAUNCHERS.md`](src/max_bringup/doc/LAUNCHERS.md).

**Remocon (uso soportado):**

- **`cm550_motion_bridge_launch.py`** — solo puente → CM-550
- **`preflight_launch.py`** — comprobar cámara y puerto antes de arrancar
- **`motion_mux_launch.py`** — una fuente activa entre `/max/motion_cmd_teleop`, `…_tracker`, etc.
- **`teleop_cm550_launch.py`** — teclado → `/cmd_vel` → `twist_to_motion_node` → `/max/motion_cmd_teleop` → puente (usar `teleop_prefix:='xterm -hold -e '` si falla termios)
- **`line_follow_motion_launch.py`**, **`shape_track_motion_launch.py`**, **`apriltag_action_motion_launch.py`** — visión + acciones como **motions**
- **`apriltag_head_search_launch.py`** — AprilTag + cabeza + cuerpo por Remocon
- **`head_ollo_bridge_launch.py`**, **`led_ollo_bridge_launch.py`** — cabeza / LEDs vía el mismo puente

**Legacy (no documentados como despliegue actual; `dynamixel_node` + `/cmd_vel`):**

- `max_launch.py`, `line_follow_launch.py`, `shape_track_launch.py`, `apriltag_action_launch.py`, `teleop_launch.py`, `vision_only_launch.py`

**Opcional (articulaciones por DYNAMIXEL, no Remocon):**

- `engineer_joint_launch.py`, `engineer_joints_teleop_launch.py`

**Configuración principal:**

- **`config/cm550_motion_bridge_max_e2.yaml`** — puente serial y `command_map`
- **`config/max_params_motion.yaml`** — visión + `output_mode: motion` hacia `/max/motion_cmd`
- **`config/max_params.yaml`** / **`max_params_jetson.yaml`** — cámara (Jetson: pipeline GStreamer en el YAML)
- **`config/apriltag_head_search.yaml`**, **`head_ollo_bridge.yaml`**, **`led_ollo_bridge.yaml`**

#### Teleoperación (teclado → motions)

Flujo recomendado:

```bash
ros2 launch max_bringup teleop_cm550_launch.py teleop_prefix:='xterm -hold -e '
```

`twist_to_motion_node` traduce `/cmd_vel` a comandos discretos en `/max/motion_cmd_teleop`; el puente los envía por Remocon. No mezcles fuentes de motion sin `motion_mux_node` o reglas claras.

#### Articulaciones Engineer (opcional, fuera de Remocon)

Si necesitas `engineer_joint_node` + `joint_teleop_node`, ver comentarios en [`LAUNCHERS.md`](src/max_bringup/doc/LAUNCHERS.md); no es el camino Remocon del cuerpo.

### Build y ejecución

```bash
# Prerrequisitos ROS
sudo apt install ros-humble-cv-bridge ros-humble-image-transport ros-humble-teleop-twist-keyboard
pip3 install dynamixel-sdk pupil-apriltags

cd /ruta/al/workspace
colcon build --symlink-install
source install/setup.bash

# --- Flujo Remocon (recomendado) ---
ros2 launch max_bringup cm550_motion_bridge_launch.py

ros2 launch max_bringup preflight_launch.py

ros2 launch max_bringup teleop_cm550_launch.py teleop_prefix:='xterm -hold -e '

ros2 launch max_bringup line_follow_motion_launch.py
ros2 launch max_bringup shape_track_motion_launch.py
ros2 launch max_bringup apriltag_action_motion_launch.py

ros2 launch max_bringup apriltag_head_search_launch.py
ros2 launch max_bringup head_ollo_bridge_launch.py
ros2 launch max_bringup led_ollo_bridge_launch.py

# Jetson: misma launch con YAML de cámara CSI
ros2 launch max_bringup apriltag_action_motion_launch.py \
  config_file:=$(ros2 pkg prefix max_bringup)/share/max_bringup/config/max_params_jetson.yaml

# Puente solo (prueba manual)
ros2 run max_driver cm550_remocon_bridge_node --ros-args \
  --params-file $(ros2 pkg prefix max_bringup)/share/max_bringup/config/cm550_motion_bridge_max_e2.yaml

# Depuración de imagen
ros2 run rqt_image_view rqt_image_view /max/debug_view
```

Comandos **legacy** (`max_launch.py`, `teleop_launch.py`, `dynamixel_node`, …) siguen en el árbol de fuentes pero no se listan como despliegue actual.

### Depuración (ROS 2, Remocon)

```bash
ros2 topic list

ros2 topic echo /max/motion_cmd
ros2 topic echo /max/detection
ros2 topic echo /max/apriltag_detections
ros2 topic echo /max/current_action

# Publicar una motion por nombre (debe existir en command_map)
ros2 topic pub --once /max/motion_cmd std_msgs/msg/String "{data: walk}"

ros2 param set /detector_node lower_h 100
ros2 param set /action_executor_node tag_action_map '0:follow,1:stop,2:spin_left'
```

Para pruebas con stack legacy que usan **`/cmd_vel`**, ver código y comentarios en los launches `*_launch.py` sin `motion`.
