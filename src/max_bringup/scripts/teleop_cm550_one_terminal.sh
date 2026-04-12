#!/usr/bin/env bash
# Teleop CM-550 en una sola sesión SSH con TTY real: arranca mapper + puente en segundo plano
# y deja teleop_twist_keyboard en primer plano (stdin del terminal).
#
# Uso en la robot (después de source ROS + workspace):
#   source /opt/ros/humble/setup.bash   # o jazzy
#   source ~/tu_ws/install/setup.bash
#   bash $(ros2 pkg prefix max_bringup)/share/max_bringup/scripts/teleop_cm550_one_terminal.sh

set -euo pipefail

if [[ -z "${ROS_DISTRO:-}" ]]; then
  echo "ERROR: ROS no cargado. Ejecuta antes:" >&2
  echo "  source /opt/ros/humble/setup.bash   # o jazzy" >&2
  echo "  source install/setup.bash            # tu workspace" >&2
  exit 1
fi

YAML="$(ros2 pkg prefix max_bringup)/share/max_bringup/config/cm550_motion_bridge_max_e2.yaml"
if [[ ! -f "$YAML" ]]; then
  echo "ERROR: No existe el YAML: $YAML (¿colcon install max_bringup?)" >&2
  exit 1
fi

cleanup() {
  if [[ -n "${LAUNCH_PID:-}" ]] && kill -0 "$LAUNCH_PID" 2>/dev/null; then
    kill "$LAUNCH_PID" 2>/dev/null || true
    wait "$LAUNCH_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Arrancando twist_to_motion + cm550_remocon_bridge (sin teclado en el launch)…" >&2
ros2 launch max_bringup teleop_cm550_launch.py include_teleop:=false &
LAUNCH_PID=$!

# Esperar a que el launch levante mapper y puente (/cmd_vel no existe hasta que arranca el teleop)
for _ in $(seq 1 30); do
  if ros2 node list 2>/dev/null | grep -q 'twist_to_motion_node'; then
    break
  fi
  sleep 0.2
done
sleep 0.3

echo "Teleop en esta terminal (foco aquí). Teclas: i , j l k; Ctrl+C termina todo." >&2
exec ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --params-file "$YAML"
