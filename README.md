# MAX - SBC + CM-550 Object Tracking Robot

Proyecto para controlar un robot basado en ROBOTIS CM-550 y servos Dynamixel desde una Raspberry Pi 4B o NVIDIA Jetson Nano, usando una cámara y OpenCV para tracking de objetos en tiempo real.

## Tabla de contenidos

- [Elección de SBC: RPi 4B vs Jetson Nano](#elección-de-sbc-rpi-4b-vs-jetson-nano)
- [Hardware](#hardware)
- [Conexión SBC - CM-550](#conexión-sbc---cm-550)
  - [Método 1: USB (recomendado)](#método-1-usb-recomendado)
  - [Método 2: UART Serial (GPIO)](#método-2-uart-serial-gpio)
  - [Método 3: BLE inalámbrico](#método-3-ble-inalámbrico)
- [Arquitecturas de control](#arquitecturas-de-control)
- [Instalación](#instalación)
  - [Raspberry Pi 4B](#raspberry-pi-4b)
  - [Jetson Nano](#jetson-nano)
- [Configuración](#configuración)
  - [Conexión USB](#conexión-usb)
  - [Conexión UART (RPi)](#conexión-uart-rpi)
  - [Conexión UART (Jetson Nano)](#conexión-uart-jetson-nano)
  - [Servos Dynamixel](#servos-dynamixel)
- [Object Tracking](#object-tracking)
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

## Arquitecturas de control

### Arquitectura A: SBC → CM-550 bypass → Servos (recomendada)

El SBC envía paquetes DYNAMIXEL Protocol 2.0 por USB al CM-550, que los reenvía a los servos.

```
SBC (cámara + OpenCV + DYNAMIXEL SDK)
    │ USB (micro USB)
    ▼
CM-550 (bypass mode, ID=200)
    │ TTL 3-pin (6 puertos)
    ▼
Dynamixel servos (daisy-chain)
```

El CM-550 tiene un registro **Bypass Port** (address 20):
- `0`: BLE
- `1`: UART
- `2`: USB

**Ventajas:** no necesita hardware extra, el CM-550 alimenta los servos.

### Arquitectura B: SBC → U2D2 → Servos (alternativa)

Bypass completo del CM-550 usando un U2D2 (convertidor USB-a-TTL half-duplex, ~$30).

```
SBC (cámara + OpenCV + DYNAMIXEL SDK)
    │ USB
    ▼
U2D2 + U2D2 Power Hub
    │ TTL 3-pin
    ▼
Dynamixel servos (daisy-chain)
```

- El U2D2 aparece como `/dev/ttyUSB0` en ambas plataformas
- **Ventajas:** control directo, probado y documentado. El usuario "newGUy" en el foro de ROBOTIS confirmó que *"U2D2 + Dynamixel SDK solved my whole problem"*.

### Arquitectura C: SBC → CM-550 (remocon packets)

El SBC envía comandos de alto nivel (remocon data) al CM-550, que ejecuta un Task code preloaded.

```
SBC (cámara + OpenCV + pySerial)
    │ UART o BLE
    ▼
CM-550 (Task code lee remocon data en address 61)
    │ TTL
    ▼
Dynamixel servos
```

Registros relevantes:
- **Address 59** (`Transmitting Remocon Data`): dato remoto a transmitir (0 ~ 65535)
- **Address 61** (`Received Remocon Data`): dato remoto recibido (0 ~ 65535)
- **Address 63** (`Remocon Data Arrived`): flag de nuevo dato (0/1)

**Ventajas:** permite usar motions pregrabadas del ROBOTIS ENGINEER Kit.

### Comparación

| Criterio | A (CM-550 bypass) | B (U2D2) | C (Remocon) |
|---|---|---|---|
| Hardware extra | Ninguno | U2D2 (~$30) | Ninguno |
| Control granular | Servo a servo | Servo a servo | Comandos de alto nivel |
| Complejidad | Media | Baja | Alta (Task code) |
| Latencia | Baja | Muy baja | Media |
| Motions pregrabadas | No | No | Sí |

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

# DYNAMIXEL SDK y pySerial
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

# DYNAMIXEL SDK
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

### Servos Dynamixel

Los servos deben estar en **Velocity Mode** (Operating Mode = 1) para control de ruedas, o **Position Mode** (Operating Mode = 3) para articulaciones.

Verificar IDs de los servos con DYNAMIXEL Wizard 2.0 o con este script:

```python
from dynamixel_sdk import *

# RPi: '/dev/ttyACM0' (USB) o '/dev/ttyAMA0' (UART)
# Jetson: '/dev/ttyACM0' (USB) o '/dev/ttyTHS1' (UART)
PORT = '/dev/ttyACM0'
BAUDRATE = 1000000

port_handler = PortHandler(PORT)
packet_handler = PacketHandler(2.0)

port_handler.openPort()
port_handler.setBaudRate(BAUDRATE)

for dxl_id in range(1, 20):
    model_number, result, error = packet_handler.ping(port_handler, dxl_id)
    if result == COMM_SUCCESS:
        print(f"ID {dxl_id}: model {model_number}")

port_handler.closePort()
```

#### Direcciones de la tabla de control (Dynamixel X-series)

| Address | Nombre | Tamaño | Acceso | Descripción |
|---|---|---|---|---|
| 11 | Operating Mode | 1 byte | RW | 1: Velocity, 3: Position, 4: Extended Position |
| 64 | Torque Enable | 1 byte | RW | 0: Off, 1: On |
| 104 | Goal Velocity | 4 bytes | RW | Velocidad objetivo (velocity mode) |
| 116 | Goal Position | 4 bytes | RW | Posición objetivo (position mode) |
| 128 | Present Velocity | 4 bytes | R | Velocidad actual |
| 132 | Present Position | 4 bytes | R | Posición actual |

---

## Object Tracking

### Concepto

```
┌──────────────┐    USB     ┌─────────┐    TTL    ┌──────────┐
│  SBC         │───────────▶│ CM-550  │──────────▶│ Dynamixel│
│  (RPi/Jetson)│            │(bypass) │           │ Servos   │
│  ┌────────┐  │            └─────────┘           └──────────┘
│  │ Camera │  │
│  └───┬────┘  │
│      │       │
│  OpenCV      │
│  detect obj  │
│      │       │
│  compute     │
│  velocity    │
│      │       │
│  DXL SDK ────┘
│  send cmd    │
└──────────────┘
```

### Flujo del algoritmo

1. **Captura**: leer frame de la cámara
2. **Detección**: convertir a HSV, aplicar máscara de color, encontrar contornos (RPi/Jetson) o inferencia con TensorRT (Jetson)
3. **Localización**: calcular centroide del contorno / bounding box más grande
4. **Control**: calcular error respecto al centro del frame
5. **Actuación**: enviar velocidades a los motores según el error
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
| `LOWER_COLOR` / `UPPER_COLOR` | Rango HSV del objeto a trackear | Usar script de calibración HSV (ver abajo) |
| `MIN_CONTOUR_AREA` | Área mínima para considerar un contorno válido | Ajustar según tamaño/distancia del objeto |
| `DEAD_ZONE` | Zona central donde el robot no gira (pixels) | Mayor = más estable, menor = más reactivo |
| `BASE_SPEED` | Velocidad de avance | Según velocidad deseada del robot |
| `TURN_SPEED` | Intensidad del giro | Según agilidad deseada |
| `DXL_ID_LEFT` / `DXL_ID_RIGHT` | IDs de los servos de tracción | Verificar con Dynamixel Wizard 2.0 |

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
- [U2D2](https://emanual.robotis.com/docs/en/parts/interface/u2d2/)

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
- [jetsonDynamixel - Control directo por UART](https://github.com/Maik93/jetsonDynamixel)

### Libros

- [Projects Guide to ROBOTIS ENGINEER Vol. 2 (CM-550 + RPi4B + Jetson Nano)](https://www.amazon.com/Projects-Guide-ROBOTIS-ENGINEER-Combined-ebook/dp/B09KQCH2FV) - cubre explícitamente Hexápodo con Jetson Nano y pan-tilt camera
- [Using ARDUINO with ROBOTIS Systems](https://www.amazon.com/Using-ARDUINO-ROBOTIS-Systems-Ngoc-ebook/dp/B0BPXGQ6YX)

### Videos

- [Communications & Control Options: Bioloid Premium Humanoid + RPi-4B](https://www.youtube.com/watch?v=e9VN78SFuE8)
- [Remocon Packet entre CM-530 y RPi](https://www.youtube.com/watch?v=uLiYTpxfRCE)

---

## Paquetes ROS2

El proyecto está estructurado como un workspace ROS2 con 5 paquetes:

```
max/                          # Workspace root
├── README.md
└── src/
    ├── max_interfaces/       # Mensajes y servicios custom (CMake)
    ├── max_vision/           # Captura de cámara + detección (Python)
    ├── max_control/          # Controlador de tracking (Python)
    ├── max_driver/           # Driver Dynamixel/CM-550 (Python)
    └── max_bringup/          # Launch files y configuración (Python)
```

### Arquitectura de nodos y topics

```
                                   /max/camera/image_raw
                                   (sensor_msgs/Image)
                                          │
┌──────────────┐  /max/detection  ┌───────┴──────┐  /cmd_vel   ┌────────────────┐
│ detector_node├─────────────────►│ tracker_node ├────────────►│ dynamixel_node │
│ (max_vision) │  (Detection)     │(max_control) │  (Twist)    │  (max_driver)  │
└──────┬───────┘                  └──────────────┘             └───────┬────────┘
       │                                                               │
       │ /max/debug_image                                    ┌─────────┴─────────┐
       │ (sensor_msgs/Image)                                 │  CM-550 / U2D2    │
       │                                                     │  (serial USB/UART)│
  [Camera]                                                   └─────────┬─────────┘
                                                                       │ TTL
                                                               [Dynamixel Servos]
```

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

- **`line_tracker_node`** - Convierte detecciones de línea en comandos de velocidad
  - Suscribe: `/max/line_detection`
  - Publica: `/cmd_vel`

- **`joint_teleop_node`** - Teleop por teclado que publica `sensor_msgs/JointState` en `/max/joint_command` (humanoide Engineer)
  - Úsalo junto a `engineer_joint_node`; parámetros en `engineer_max_e2.yaml` (`joint_teleop_node`)

- **`action_executor_node`** - Mapea AprilTag IDs a acciones del robot
  - Suscribe: `/max/apriltag_detections`
  - Publica: `/cmd_vel`, `/max/current_action` (std_msgs/String)
  - Acciones predefinidas: `follow`, `stop`, `sprint`, `reverse`, `spin_left`, `spin_right`, `dance`
  - Mapeo configurable vía YAML: `tag_action_map: '0:follow,1:stop,2:spin_left,...'`
  - Selecciona el tag más grande (cercano) cuando hay múltiples

### max_driver

**Nodos:**

- **`dynamixel_node`** - Interfaz con servos Dynamixel vía CM-550
  - Suscribe: `/cmd_vel`
  - Publica: `/max/dynamixel_states`
  - Servicios: `/max/set_torque`, `/max/set_operating_mode`
  - Cinemática diferencial: Twist → velocidades de rueda izquierda/derecha
  - Graceful degradation: puede correr sin hardware (para testing)

- **`engineer_joint_node`** - Control multi-articular para humanoides **ROBOTIS Engineer** (p. ej. **MAX-E2**) y otros brazos/piernas con XL430/2XL430
  - Suscribe: `/max/joint_command` (`sensor_msgs/JointState`, usa el campo **`position`** como objetivo)
  - Publica: `/joint_states` (`sensor_msgs/JointState` con posición/velocidad leídas del bus)
  - Servicios: `/max/engineer/set_torque`, `/max/engineer/set_operating_mode`
  - Por defecto: modo **Position** (3), torque ON, conversión **radianes ↔ ticks** (4096/rev)
  - **No** ejecutes a la vez `dynamixel_node` y `engineer_joint_node` sobre el mismo CM-550 (conflicto de bus / comandos).
  - Debes alinear **`joint_ids`** y **`joint_names`** con tu ensamblaje (Dynamixel Wizard 2.0); la plantilla está en `config/engineer_max_e2.yaml`.

### max_bringup

**Launch files:**

- **`max_launch.py`** - Tracking por color (detector + tracker + dynamixel + debug_view)
- **`shape_track_launch.py`** - Tracking por formas (shape_detector + tracker + dynamixel + debug_view)
- **`line_follow_launch.py`** - Seguimiento de línea (line_detector + line_tracker + dynamixel + debug_view)
- **`apriltag_action_launch.py`** - Acciones por AprilTag (apriltag_detector + action_executor + dynamixel + debug_view)
- **`teleop_launch.py`** - Teleoperación por teclado (`teleop_twist_keyboard` + `dynamixel_node`)
- **`engineer_joint_launch.py`** - Solo control articulaciones Engineer / MAX-E2 (`engineer_joint_node`)
- **`engineer_joints_teleop_launch.py`** - `engineer_joint_node` + `joint_teleop_node` (mismo `engineer_max_e2.yaml`)
- **`vision_only_launch.py`** - Solo visión y control (sin hardware, para testing)

**Configuración:**

- **`config/max_params.yaml`** - Parámetros para RPi 4B
- **`config/max_params_jetson.yaml`** - Parámetros para Jetson Nano (incluye GStreamer pipeline)
- **`config/engineer_max_e2.yaml`** - Plantilla `joint_ids` / `joint_names` para humanoide Engineer (ajustar a tu robot)

#### Teleoperación (teclado)

`dynamixel_node` ya escucha `/cmd_vel`. El paquete estándar `teleop_twist_keyboard` publica en ese mismo topic, así que basta con lanzar:

```bash
ros2 launch max_bringup teleop_launch.py
```

Velocidades iniciales en YAML (`teleop_twist_keyboard`: `speed`, `turn`). En el nodo puedes ajustar con **q/z** (±10% todo), **w/x** (solo lineal), **e/c** (solo angular). Layout típico: **i** avanza, **,** retrocede, **j**/**l** giran, **k** para.

**Importante:** no ejecutes a la vez `teleop_launch` y nodos autónomos (`tracker_node`, `line_tracker_node`, `action_executor_node`): se pisan en `/cmd_vel`. Para mezclar manual + autónomo habría que usar algo como `twist_mux` y topics distintos (`cmd_vel_teleop`, `cmd_vel_nav`).

Para mando (joystick), instala `ros-humble-teleop-twist-joy`, configura un `joy_node` y remapea su salida a `/cmd_vel` (o al topic que use un mux).

#### Control ROS2 del humanoide Engineer (MAX-E2)

```bash
# Tras calibrar IDs/nombres en config/engineer_max_e2.yaml
ros2 launch max_bringup engineer_joint_launch.py

# En otra terminal: teleop por teclado (publica JointState en /max/joint_command)
ros2 run max_control joint_teleop_node --ros-args \
  --params-file $(ros2 pkg prefix max_bringup)/share/max_bringup/config/engineer_max_e2.yaml

# O driver + teleop en un solo launch (misma TTY: el teclado va al teleop)
ros2 launch max_bringup engineer_joints_teleop_launch.py

# Ver estado de articulaciones
ros2 topic echo /joint_states

# Enviar objetivo (ejemplo: un solo joint; nombres deben coincidir con el YAML)
ros2 topic pub --once /max/joint_command sensor_msgs/msg/JointState \
  "{name: ['l_knee'], position: [0.5], velocity: [], effort: []}"
```

**`joint_teleop_node`** (teclas `[` `]` cambiar articulación, `=` / `-` paso en rad, `0` cero, `g` copiar desde `/joint_states`, `h` ayuda, `q` salir). Requiere **terminal interactivo** (TTY). Con `joint_names: []` en el YAML, toma nombres y pose inicial del primer `/joint_states` que publica `engineer_joint_node`.

Para teleop más avanzado: **RViz**, **MoveIt 2**, **joint_trajectory_controller**. El driver `engineer_joint_node` es la capa **hardware → ROS**.

### Build y ejecución

```bash
# Prerequisitos
sudo apt install ros-humble-cv-bridge ros-humble-image-transport ros-humble-teleop-twist-keyboard
pip3 install dynamixel-sdk pupil-apriltags

# Build
cd /path/to/max
colcon build --symlink-install
source install/setup.bash

# Lanzar tracking por color (RPi)
ros2 launch max_bringup max_launch.py

# Lanzar seguimiento de línea
ros2 launch max_bringup line_follow_launch.py

# Lanzar tracking por formas
ros2 launch max_bringup shape_track_launch.py

# Lanzar acciones por AprilTag
ros2 launch max_bringup apriltag_action_launch.py

# Lanzar con config Jetson Nano
ros2 launch max_bringup apriltag_action_launch.py \
  config_file:=$(ros2 pkg prefix max_bringup)/share/max_bringup/config/max_params_jetson.yaml

# Solo visión (sin hardware)
ros2 launch max_bringup vision_only_launch.py

# Teleoperación manual (teclado → /cmd_vel → ruedas)
# No combines con tracker/line_tracker/action_executor: todos publican /cmd_vel.
ros2 launch max_bringup teleop_launch.py

# Humanoide Engineer / MAX-E2 (articulaciones → /max/joint_command)
ros2 launch max_bringup engineer_joint_launch.py

# Nodos individuales
ros2 run max_vision detector_node
ros2 run max_vision apriltag_detector_node
ros2 run max_vision hsv_calibrator
ros2 run max_control tracker_node
ros2 run max_control action_executor_node
ros2 run max_control joint_teleop_node
ros2 run max_driver dynamixel_node --ros-args -p port:=/dev/ttyACM0
ros2 run max_driver engineer_joint_node --ros-args \
  --params-file $(ros2 pkg prefix max_bringup)/share/max_bringup/config/engineer_max_e2.yaml
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Visualizar debug view
ros2 run rqt_image_view rqt_image_view /max/debug_view
```

### Debugging con ROS2

```bash
# Ver topics activos
ros2 topic list

# Monitorear detecciones
ros2 topic echo /max/detection

# Monitorear comandos de velocidad
ros2 topic echo /cmd_vel

# Ver estado de servos
ros2 topic echo /max/dynamixel_states

# Monitorear AprilTags
ros2 topic echo /max/apriltag_detections

# Monitorear acción actual
ros2 topic echo /max/current_action

# Cambiar parámetros en runtime
ros2 param set /detector_node lower_h 100
ros2 param set /tracker_node linear_speed 0.2
ros2 param set /action_executor_node tag_action_map '0:follow,1:sprint,2:dance'

# Enviar cmd_vel manual (testing)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}"

# Llamar servicios
ros2 service call /max/set_torque max_interfaces/srv/SetTorque \
  "{id: 1, enable: true}"
```
