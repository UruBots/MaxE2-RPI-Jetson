# Launchers (`max_bringup`)

Este proyecto se usa **por Remocon** (`cm550_remocon_bridge_node` → CM-550). La tabla prioriza ese flujo; los launches que arrancan `dynamixel_node` y `/cmd_vel` se listan como **legacy**.

**Teleop por SSH / TTY / xterm:** [TELEOP_SSH.md](TELEOP_SSH.md). **Cadena tecla → página motion (101/103):** [MOTION_TELEOP.md](MOTION_TELEOP.md).

## Stack Remocon (soportado)

| Launcher | Acción principal | Nodos / notas |
|----------|------------------|---------------|
| `preflight_launch.py` | Comprobar cámara y puerto serial | `preflight_check_node`. YAML típico: `cm550_motion_bridge_max_e2.yaml`. |
| `cm550_motion_bridge_launch.py` | Solo puente ROS → paquetes Remocon → CM-550 | `cm550_remocon_bridge_node` + `cm550_motion_bridge_max_e2.yaml`. |
| `motion_mux_launch.py` | Una fuente activa hacia `/max/motion_cmd` | `motion_mux_node`: `active_source` = `teleop` \| `tracker` \| `apriltag` \| `line`. |
| `teleop_cm550_launch.py` | Teclado → `/cmd_vel` → motions → Remocon | `teleop_twist_keyboard`, `twist_to_motion_node` → `/max/motion_cmd` (mismo topic que el puente), `cm550_remocon_bridge_node`. Si mezclas con tracker/línea, usa `motion_mux_launch` y entonces publica cada fuente en `/max/motion_cmd_*` según mux. Por **SSH**: `include_teleop:=false` + `ssh -t` para el teclado; `teleop_prefix` con `DISPLAY`. |
| `line_follow_motion_launch.py` | Línea → acciones **motion** | `line_detector_node`, `line_tracker_node` (motion), `cm550_remocon_bridge_node`, `debug_view_node`. `max_params_motion.yaml`. |
| `shape_track_motion_launch.py` | Forma/color → motions | `shape_detector_node`, `tracker_node`, `cm550_remocon_bridge_node`, `debug_view_node`. `max_params_motion.yaml`. |
| `apriltag_action_motion_launch.py` | AprilTag → acciones **motion** | `apriltag_detector_node`, `action_executor_node`, `cm550_remocon_bridge_node`, `debug_view_node`. `max_params_motion.yaml`. |
| `apriltag_head_search_launch.py` | Barrido cabeza + cuerpo por Remocon | `apriltag_detector_node`, `cm550_remocon_bridge_node`, `apriltag_head_search_node`, `debug_view_node`. `apriltag_head_search.yaml`. |
| `head_ollo_bridge_launch.py` | Cabeza OLLO vía Remocon | `cm550_remocon_bridge_node` + `head_ollo_bridge.yaml`. |
| `led_ollo_bridge_launch.py` | LEDs OLLO vía Remocon | `cm550_remocon_bridge_node` + `led_ollo_bridge.yaml`. |
| `debug_image_view_launch.py` | Cuatro `image_view` en topics debug | Requiere paquete ROS `image_view`. |

## Legacy (`dynamixel_node`, `/cmd_vel`, sin Remocon de cuerpo)

| Launcher | Notas |
|----------|--------|
| `max_launch.py` | Visión + `dynamixel_node` (ruedas por Twist). |
| `vision_only_launch.py` | Sin actuadores de base. |
| `line_follow_launch.py` | Línea + ruedas Dynamixel. |
| `shape_track_launch.py` | Forma/color + ruedas. |
| `apriltag_action_launch.py` | AprilTag + ruedas. |
| `teleop_launch.py` | Teclado → `/cmd_vel` → `dynamixel_node`. `teleop_prefix` si hace falta TTY. |

## Opcional (articulaciones por bus DYNAMIXEL, no Remocon del cuerpo)

| Launcher | Notas |
|----------|--------|
| `engineer_joint_launch.py` | Solo `engineer_joint_node`. |
| `engineer_joints_teleop_launch.py` | `engineer_joint_node` + `joint_teleop_node`; `teleop_prefix` para TTY. |

## Ejemplos

```bash
ros2 launch max_bringup cm550_motion_bridge_launch.py

ros2 launch max_bringup line_follow_motion_launch.py

ros2 launch max_bringup preflight_launch.py

ros2 launch max_bringup teleop_cm550_launch.py teleop_prefix:='xterm -hold -e '

# Solo bridge + mapper; teleop en otra terminal (ssh -t) con el mismo params-file
ros2 launch max_bringup teleop_cm550_launch.py include_teleop:=false
```
