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

## 3.1 Estado real de la CM-550

Antes de culpar a `ROS 2`, confirma que la `CM-550` realmente está ejecutando el script.

Checklist:

1. desconecta `R+ Task 3.0` y `R+ Manager 2.0`
2. apaga la `CM-550`
3. aliméntala con batería o fuente normal
4. enciéndela
5. presiona `MODE` hasta dejar el LED en verde
6. presiona `START`
7. verifica que el verde deje de parpadear

Interpretación práctica:

- `MODE` rojo: `Manage`, el script no está corriendo
- `MODE` verde parpadeando: `Play`, esperando `START`
- `MODE` verde fijo o deja de parpadear: el script debería estar ejecutándose

Recién después de eso conecta el USB a la PC/RPi y prueba `ROS 2`.

Importante:
- si `R+ Task` o `R+ Manager` están conectados, la `CM-550` puede volver a `Manage`
- si el script no está corriendo, `rc.read()` no va a reaccionar aunque el bridge ROS funcione bien

## 4. Probar motions del cuerpo

La estrategia recomendada es:

`ROS 2 -> Remocon packet serial -> rc.read() en CM-550 -> motion.play(...)`

El transporte práctico recomendado es:

`PC/RPi -> micro-USB -> paquete tipo RC-100 -> CM-550`

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
- [`max_e2_cm550_ros2_usb_bridge.py`](/Users/sebastian/Desarrollo/max/docs/max_e2_cm550_ros2_usb_bridge.py)

Control de velocidad desde ROS:
- publica `UInt16` en `/max/profile_velocity`
- el bridge envía `50000 + vel` y el script hace `DXL(254).write32(112, vel)` (Profile Velocity global)
- valores típicos: `20..80` para marcha lenta, `0` = sin límite

Orden correcto de prueba:

1. cargar el `.py`
2. cargar el `.mtn3`
3. apagar la `CM-550`
4. encenderla
5. poner `Play` (`MODE` verde)
6. presionar `START`
7. recién ahí conectar USB y lanzar `ROS 2`

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

## 11. Seguimiento de pelota por color

Esta ruta usa solo visión + bridge CM-550, sin joystick:

```bash
ros2 launch max_bringup shape_track_motion_launch.py
```

Lo que corre:
- `shape_detector_node`: detecta la pelota por color (HSV) y publica en `/max/detection`.
- `tracker_node`: centra la pelota con giros y avanza/retrocede según área, publicando `walk/turn_left/turn_right/reverse/stop` en `/max/motion_cmd`.
- `cm550_remocon_bridge_node`: traduce esos comandos a remocon packets para la CM-550.

### Colores preconfigurados

Ambos nodos de visión aceptan el parámetro `color_preset`:
- Valores: `red`, `orange`, `yellow`, `blue`, `green`, `custom`
- Por defecto: `orange`
- Cambio en caliente (sin relanzar):
  ```bash
  ros2 param set /shape_detector_node color_preset blue
  ros2 param set /detector_node color_preset blue
  ```

### Ajuste fino (modo custom)

Si necesitas otro color, pon `color_preset:=custom` y ajusta rangos HSV:
- `lower_h`, `lower_s`, `lower_v`
- `upper_h`, `upper_s`, `upper_v`
- Segundo rango opcional (útil para rojo): `lower_h2`, `upper_h2`, `use_second_range`

Archivos de configuración:
- Con motions: `src/max_bringup/config/max_params_motion.yaml`
- Solo visión: `src/max_bringup/config/max_params.yaml`

### Notas de control
- Distancia: `tracker_node` usa el área de la pelota para avanzar (`forward_command: walk`) o retroceder (`reverse_command: reverse`) según `target_area` y `area_tolerance`.
- Búsqueda: si se pierde la pelota y `search_enabled` está en `false` (default), el cuerpo se queda quieto; ponlo en `true` si quieres giro de búsqueda.
- Cabeza: este pipeline no mueve la cabeza; si necesitas tracking con cabeza, habilita `head_tracking_enabled` y ajusta `head_*` en `max_params_motion.yaml`.

## 12. Teleoperación por teclado hacia la CM-550

Controla el robot con el teclado y mapea a motions discretas (remocon) sin depender de /cmd_vel continuo.

Lanzar:
```bash
ros2 launch max_bringup teleop_cm550_launch.py
```

Nodos:
- `teleop_twist_keyboard`: publica `/cmd_vel` con las teclas estándar (i/k/j/l, etc.).
- `twist_to_motion_node`: convierte `/cmd_vel` en comandos discretos (`walk`, `reverse`, `turn_left`, `turn_right`, `stop`) y los publica en `/max/motion_cmd`, y además escala la velocidad lineal a `/max/profile_velocity`.
- `cm550_remocon_bridge_node`: traduce esos comandos a paquetes remocon para la CM-550.

Config principal:
- Archivo: `src/max_bringup/config/cm550_motion_bridge_max_e2.yaml`
- Sección `twist_to_motion_node`:
  - `forward_command`: `walk`
  - `backward_command`: `reverse`
  - `left_command`: `turn_left`
  - `right_command`: `turn_right`
  - `stop_command`: `stop`
  - `linear_threshold`, `angular_threshold`: umbrales de activación.
  - `prefer_turn_over_forward`: si `true`, prioriza giro cuando hay giro y avance a la vez.
  - `speed_topic`: `/max/profile_velocity` (ya consumido por el bridge).
  - `profile_velocity_max`, `profile_velocity_min`: rango de Profile Velocity que se enviará.
  - `linear_speed_full_scale`: velocidad lineal (m/s) que corresponde a `profile_velocity_max`.
- Sección `teleop_twist_keyboard`:
  - `speed`, `turn`: ganancias de velocidad lineal/angulares del nodo de teclado.

Ajustes en caliente:
```bash
ros2 param set /twist_to_motion_node forward_command run          # usar otra motion
ros2 param set /twist_to_motion_node prefer_turn_over_forward false
ros2 param set /twist_to_motion_node profile_velocity_max 150
ros2 param set /twist_to_motion_node linear_speed_full_scale 0.3
ros2 param set /teleop_twist_keyboard speed 0.3
```

Notas:
- No mezcles este launch con otros que también publiquen en `/cmd_vel` o `/max/motion_cmd` (tracker, line_tracker, action_executor) para evitar que se pisen.
- El mapping a motions depende de que esas motions existan en la CM-550 (ver `command_map` en `cm550_motion_bridge_max_e2.yaml`).

### Evitar colisiones de control
- Usa un único launch que publique en `/max/motion_cmd` a la vez (teleop o trackers). Si necesitas alternar, cierra uno antes de abrir otro.
- Alternativa: usa el mux incluido:
  ```bash
  ros2 launch max_bringup motion_mux_launch.py active_source:=teleop   # o tracker | apriltag | line
  ```
  Publica en `/max/motion_cmd` solo lo que venga de `/max/motion_cmd_<source>`.
- Otra opción: remapear topics de controladores a `/max/motion_cmd_<source>` y dejar que el mux seleccione.

### Motions personalizadas (run/down/etc.)
- Añade las páginas a `command_map` y `command_sequences` en `cm550_motion_bridge_max_e2.yaml` o `max_params_motion.yaml`. Ejemplo:
  - `command_map: '...,run:153,down:60'`
  - `command_sequences: '...,run:151|153'`
- Ajusta también `twist_to_motion_node` si quieres que el teclado dispare esas motions:
  ```bash
  ros2 param set /twist_to_motion_node forward_command run
  ```

### Preflight rápido (cámara + serial)
- Chequea hardware antes de lanzar control:
  ```bash
  ros2 launch max_bringup preflight_launch.py
  ```
- Usa los parámetros del YAML para `camera_index`/`gstreamer_pipeline` y `serial_port`. Si `pyserial` falta, el chequeo de serial se omite con warning.

### Ver debug de visión con image_view
- Publicaciones actuales:
  - Línea: `/max/line_debug_image`
  - Objeto/forma (shape): `/max/shape_debug_image`
  - Color HSV (detector): `/max/debug_image`
  - AprilTag: `/max/apriltag_debug_image`
- Launch para abrir viewers:
  ```bash
  ros2 launch max_bringup debug_image_view_launch.py
  ```
- O manual:
  ```bash
  ros2 run image_view image_view --ros-args -r image:=/max/line_debug_image
  ```
