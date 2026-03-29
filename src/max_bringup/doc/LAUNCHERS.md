# Launchers (`max_bringup`)

Tabla de los archivos en `launch/` y qué hace cada uno.  
Config por defecto suele estar en `config/` (argumento `config_file`).

| Launcher | Acción principal | Nodos / notas |
|----------|------------------|-----------------|
| `preflight_launch.py` | Comprobar cámara y puerto serial antes de arrancar el resto | `preflight_check_node` (max_vision). YAML típico: `cm550_motion_bridge_max_e2.yaml`. |
| `motion_mux_launch.py` | Elegir **una** fuente de comandos hacia motions | `motion_mux_node`: parámetro `active_source` = `teleop` \| `tracker` \| `apriltag` \| `line` (multiplexa `/max/motion_cmd`). |
| `teleop_cm550_launch.py` | Teclado → `/cmd_vel` → comandos discretos → CM-550 | `teleop_twist_keyboard`, `twist_to_motion_node` (salida `/max/motion_cmd_teleop`), `cm550_remocon_bridge_node`. Si `teleop_twist_keyboard` falla con `termios` / “Inappropriate ioctl for device”, el stdin no es TTY: usa `teleop_prefix:='xterm -hold -e '` (con espacio al final) o ejecuta el teleop en otra terminal. |
| `debug_image_view_launch.py` | Abrir ventanas `image_view` para depuración | Cuatro `image_view` remapeados a `/max/line_debug_image`, `/max/shape_debug_image`, `/max/debug_image`, `/max/apriltag_debug_image`. |
| `led_ollo_bridge_launch.py` | Solo puente LED (y mismo nodo puede llevar head si el YAML lo define) | `cm550_remocon_bridge_node` con `led_ollo_bridge.yaml`. |
| `head_ollo_bridge_launch.py` | Puente de comandos de **cabeza** OLLO vía remocon | `cm550_remocon_bridge_node` con `head_ollo_bridge.yaml`. |
| `cm550_motion_bridge_launch.py` | Puente **general** ROS → paquetes remocon → CM-550 (motions, LED, cabeza según YAML) | `cm550_remocon_bridge_node` con `cm550_motion_bridge_max_e2.yaml`. |
| `line_follow_motion_launch.py` | Seguimiento de **línea** con acciones como **motions** en CM-550 | `line_detector_node`, `line_tracker_node` (`output_mode: motion`), `cm550_remocon_bridge_node`, `debug_view_node`. Config: `max_params_motion.yaml`. |
| `shape_track_motion_launch.py` | Seguimiento por **forma/color** + motions CM-550 | `shape_detector_node`, `tracker_node`, `cm550_remocon_bridge_node`, `debug_view_node`. Config: `max_params_motion.yaml`. |
| `apriltag_action_motion_launch.py` | **AprilTag** → acciones mapeadas + motions CM-550 | `apriltag_detector_node`, `action_executor_node`, `cm550_remocon_bridge_node`, `debug_view_node`. Config: `max_params_motion.yaml`. |
| `apriltag_head_search_launch.py` | Barrido de cabeza buscando tag; luego centrar | `apriltag_detector_node`, `cm550_remocon_bridge_node`, `apriltag_head_search_node`, `debug_view_node`. Config: `apriltag_head_search.yaml`. |
| `max_launch.py` | Stack “clásico” visión + seguimiento + **ruedas** Dynamixel | `detector_node`, `tracker_node`, `dynamixel_node`, `debug_view_node`. Argumento `platform` (`rpi` / `jetson`). Config: `max_params.yaml`. |
| `vision_only_launch.py` | Solo visión + tracker, **sin** base con ruedas | `detector_node`, `tracker_node`, `debug_view_node`. |
| `line_follow_launch.py` | Línea + tracker + **ruedas** | `line_detector_node`, `line_tracker_node`, `dynamixel_node`, `debug_view_node`. |
| `shape_track_launch.py` | Forma/color + tracker + **ruedas** | `shape_detector_node`, `tracker_node`, `dynamixel_node`, `debug_view_node`. |
| `apriltag_action_launch.py` | AprilTag + acciones + **ruedas** | `apriltag_detector_node`, `action_executor_node`, `dynamixel_node`, `debug_view_node`. |
| `teleop_launch.py` | Teleop teclado → `/cmd_vel` → **ruedas** | `dynamixel_node`, `teleop_twist_keyboard`. **No** combinar con otros nodos que publiquen `/cmd_vel` a la vez. |
| `engineer_joint_launch.py` | Control **articulaciones** Engineer/MAX-E2 (Dynamixel por CM-550) | Solo `engineer_joint_node`. Config: `engineer_max_e2.yaml`. |
| `engineer_joints_teleop_launch.py` | Driver de joints + teleop teclado a `JointState` | `engineer_joint_node`, `joint_teleop_node`. |

## Cómo elegir entre variantes

- **Motions en CM-550 (remocon, sin `joint_command` por joint):** launches `*_motion_*`, `cm550_motion_bridge_launch.py`, `teleop_cm550_launch.py`, puentes `head_ollo_bridge` / `led_ollo_bridge`.
- **Base con ruedas (`dynamixel_node` + `/cmd_vel`):** `max_launch.py`, `line_follow_launch.py`, `shape_track_launch.py`, `apriltag_action_launch.py`, `teleop_launch.py`, `vision_only_launch.py`.
- **Humanoide por articulaciones (`/max/joint_command`):** `engineer_joint_launch.py`, `engineer_joints_teleop_launch.py`.

## Ejemplos de uso

```bash
# Puente remocon + YAML por defecto
ros2 launch max_bringup cm550_motion_bridge_launch.py

# Línea → motion pages
ros2 launch max_bringup line_follow_motion_launch.py

# Preflight antes de conectar hardware
ros2 launch max_bringup preflight_launch.py

# Teleop CM-550 con ventana xterm (evita error termios al lanzar todo con ros2 launch)
ros2 launch max_bringup teleop_cm550_launch.py teleop_prefix:='xterm -hold -e '
```
