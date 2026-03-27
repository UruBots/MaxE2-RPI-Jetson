# Launches rápidos (MAX-E2)

| Tarea | Comando | YAML por defecto | Publica a /max/motion_cmd | Notas |
|-------|---------|------------------|---------------------------|-------|
| Preflight HW (cámara + serial) | `ros2 launch max_bringup preflight_launch.py` | `cm550_motion_bridge_max_e2.yaml` | No | Solo chequea y termina |
| Teleop teclado → CM-550 | `ros2 launch max_bringup teleop_cm550_launch.py` | `cm550_motion_bridge_max_e2.yaml` | Sí (vía `twist_to_motion_node`) | Publica en `/max/motion_cmd_teleop` para usar con el mux |
| AprilTag (barrido+centro+caminar) | `ros2 launch max_bringup apriltag_head_search_launch.py` | `apriltag_head_search.yaml` | Sí | Evitar que corra teleop simultáneo |
| Línea con motions | `ros2 launch max_bringup line_follow_motion_launch.py` | `max_params_motion.yaml` | Sí | Usa `line_detector_node` + `line_tracker_node` |
| Pelota/objeto por color | `ros2 launch max_bringup shape_track_motion_launch.py` | `max_params_motion.yaml` | Sí | Configura `color_preset` en detector/shape_detector |
| Visión + tracker sin cuerpo | `ros2 launch max_bringup vision_only_launch.py` | `max_params.yaml` | No | Solo detección/visualización |
| Ver debug images (image_view) | `ros2 launch max_bringup debug_image_view_launch.py` | N/A | No | Abre 4 viewers: línea, objeto/forma, color (detector), AprilTag |
| Seleccionar fuente de motion (mux) | `ros2 launch max_bringup motion_mux_launch.py active_source:=teleop` | N/A | Sí (reemite) | Activa una de: teleop, tracker, apriltag, line. Controladores deben publicar en `/max/motion_cmd_<source>`. |

Consejos de uso:
- No ejecutes simultáneamente dos lanzadores que publiquen en `/max/motion_cmd`; si necesitas alternar, detén uno antes de iniciar el otro.
- Para motions personalizadas, agrega páginas en el YAML correspondiente y ajusta `twist_to_motion_node` si las usarás con teclado.
- Si usas cámara distinta o pipeline GStreamer, cambia `camera_index` o `gstreamer_pipeline` en el YAML.
