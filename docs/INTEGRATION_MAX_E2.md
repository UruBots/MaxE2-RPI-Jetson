# Integración MAX-E2 con ROS 2 y CM-550

Guía operativa corta para dejar el `MAX-E2` funcionando con:
- motions oficiales en la `CM-550`
- control de cabeza OLLO
- búsqueda y recentrado por `AprilTag`

## 1. Prerrequisitos

Necesitas:
- `CM-550` encendida y alimentada
- motions oficiales cargadas en la `CM-550`
- Python oficial del `MAX-E2` cargado en la `CM-550`
- cámara funcionando
- `ROS 2` instalado en la Raspberry Pi 4

Archivos oficiales relevantes:
- [`01_ENG2_Max_E2_PY.py`](/Users/sebastian/Downloads/01_ENG2_Max_E2_PY.py)
- [`01_ENG2_Max_E2_MO.mtn3`](/Users/sebastian/Downloads/01_ENG2_Max_E2_MO.mtn3)

## 2. Qué corre en cada lado

### En la `CM-550`

La `CM-550` debe tener:
- las motions `.mtn3` del `MAX-E2`
- un script Python o lógica equivalente que lea `rc.read()`
- manejo de motions, cabeza OLLO y LEDs desde ese `rc.read()`

Referencia local:
- [`cm550_head_ollo_receiver_example.py`](/Users/sebastian/Desarrollo/max/docs/cm550_head_ollo_receiver_example.py)
- [`cm550_motion_remocon_receiver_example.py`](/Users/sebastian/Desarrollo/max/docs/cm550_motion_remocon_receiver_example.py)

### En `ROS 2`

`ROS 2` corre:
- detector de `AprilTag`
- un único puente serial de `Remocon packet` hacia la `CM-550`
- lógica de búsqueda y recentrado

## 3. Orden recomendado de bring-up

Haz las pruebas en este orden:

1. comprobar que la `CM-550` responde por USB
2. comprobar que una motion simple funciona
3. comprobar que la cabeza OLLO responde
4. comprobar detección de `AprilTag`
5. comprobar barrido de cabeza
6. comprobar recentrado del cuerpo

## 4. Probar motions del cuerpo

La estrategia recomendada es:

`ROS 2 -> Remocon packet serial -> rc.read() en CM-550 -> motion.play(...)`

No dependas de escribir `Motion Index Number (66)` directamente sobre el firmware oficial del `MAX-E2`.

Lanza:

```bash
ros2 launch max_bringup cm550_motion_bridge_launch.py
```

Prueba motions simples:

```bash
ros2 topic pub --once /max/motion_cmd std_msgs/msg/String "{data: stand}"
ros2 topic pub --once /max/motion_cmd std_msgs/msg/String "{data: hello}"
ros2 topic pub --once /max/motion_cmd std_msgs/msg/String "{data: turn_left}"
ros2 topic pub --once /max/motion_cmd std_msgs/msg/String "{data: turn_right}"
```

Config:
- [`cm550_motion_bridge_max_e2.yaml`](/Users/sebastian/Desarrollo/max/src/max_bringup/config/cm550_motion_bridge_max_e2.yaml)

Script listo para la `CM-550`:
- [`01_ENG2_Max_E2_PY_ros2_ready.py`](/Users/sebastian/Desarrollo/max/docs/01_ENG2_Max_E2_PY_ros2_ready.py)

## 5. Probar cabeza OLLO

La cabeza no se controla como `XL430`; usa `OLLO(1, const.OLLO_JOINT_POSITION)`.

Lanza:

```bash
ros2 launch max_bringup head_ollo_bridge_launch.py
```

Pruebas:

```bash
ros2 topic pub --once /max/head_preset std_msgs/msg/String "{data: center}"
ros2 topic pub --once /max/head_cmd_raw std_msgs/msg/UInt16 "{data: 680}"
ros2 topic pub --once /max/head_cmd_raw std_msgs/msg/UInt16 "{data: 344}"
```

Config:
- [`head_ollo_bridge.yaml`](/Users/sebastian/Desarrollo/max/src/max_bringup/config/head_ollo_bridge.yaml)

Para que esto funcione, la `CM-550` tiene que estar ejecutando el script listo que usa `rc.read()`.

## 6. Probar detección de AprilTag

Lanza:

```bash
ros2 run max_vision apriltag_detector_node
```

Y verifica:

```bash
ros2 topic echo /max/apriltag_detections
```

Si no hay detección:
- revisa cámara
- revisa iluminación
- revisa familia de tag

## 7. Probar barrido de cabeza + recentrado

Lanza:

```bash
ros2 launch max_bringup apriltag_head_search_launch.py
```

Esto hace:
- barrer cabeza izquierda-derecha
- parar barrido cuando detecta un tag
- recentrar la cabeza
- mandar `turn_left`, `turn_right` o `stop` al cuerpo

Config:
- [`apriltag_head_search.yaml`](/Users/sebastian/Desarrollo/max/src/max_bringup/config/apriltag_head_search.yaml)

## 8. Ajustes que casi seguro tendrás que tocar

### Cabeza

Ajusta:
- `center_raw`
- `min_raw`
- `max_raw`
- `preset_map`

Archivo:
- [`head_ollo_bridge.yaml`](/Users/sebastian/Desarrollo/max/src/max_bringup/config/head_ollo_bridge.yaml)

### Cuerpo

Ajusta:
- `command_map`
- `command_sequences`
- `sequence_step_delay_sec`

Archivo:
- [`cm550_motion_bridge_max_e2.yaml`](/Users/sebastian/Desarrollo/max/src/max_bringup/config/cm550_motion_bridge_max_e2.yaml)

### Búsqueda con AprilTag

Ajusta:
- `scan_min_raw`
- `scan_max_raw`
- `scan_step_raw`
- `body_dead_zone`
- `detection_timeout`

Archivo:
- [`apriltag_head_search.yaml`](/Users/sebastian/Desarrollo/max/src/max_bringup/config/apriltag_head_search.yaml)

## 9. Limitaciones actuales

Esta integración actual:
- usa motions discretas para el cuerpo
- no hace control continuo de marcha
- no hace tracking fino simultáneo cabeza+cuerpo
- depende de que la `CM-550` tenga ya cargadas las motions y el script de cabeza

Es una base buena para:
- detección
- búsqueda visual
- recentrado
- disparo de motions oficiales

## 10. Siguiente mejora recomendada

La mejora más útil después de esto es una de estas:

1. calibrar valores de `target_size_px` / `target_area`
2. hacer seguimiento fino con la cabeza después de encontrar el tag
3. encadenar motions de cuerpo más suaves para recentrado
