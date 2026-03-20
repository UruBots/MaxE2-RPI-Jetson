from __future__ import annotations

"""Teleop por teclado: publica sensor_msgs/JointState en /max/joint_command.

Usar con engineer_joint_node. Requiere TTY (terminal interactivo), p. ej.:
  ros2 run max_control joint_teleop_node
"""

from typing import Optional

import select
import sys
import threading
import termios
import tty

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header


HELP_TEXT = """
=== joint_teleop ===
  [ / ]     Articulación anterior / siguiente
  = / -     Mover +step / -step (radianes)
  0         Poner articulación actual en 0 rad
  g         Copiar posiciones actuales desde /joint_states
  h         Esta ayuda
  q         Salir
==================
"""


class JointTeleopNode(Node):
    def __init__(self):
        super().__init__('joint_teleop_node')

        self.declare_parameter('command_topic', '/max/joint_command')
        self.declare_parameter('joint_states_topic', '/joint_states')
        self.declare_parameter('joint_names', [])
        self.declare_parameter('step_rad', 0.05)
        self.declare_parameter('republish_rate_hz', 0.0)
        # Si joint_names viene del YAML y es true, espera el primer /joint_states para copiar pose inicial.
        self.declare_parameter('seed_from_joint_states', True)

        self._cmd_topic = self.get_parameter('command_topic').get_parameter_value().string_value
        self._states_topic = self.get_parameter('joint_states_topic').get_parameter_value().string_value
        param_names = list(self.get_parameter('joint_names').get_parameter_value().string_array_value)
        self._step = self.get_parameter('step_rad').get_parameter_value().double_value
        republish = self.get_parameter('republish_rate_hz').get_parameter_value().double_value
        self._seed_from_feedback = (
            self.get_parameter('seed_from_joint_states').get_parameter_value().bool_value
        )

        self._lock = threading.Lock()
        self._joint_names: list = []
        self._positions: dict = {}
        self._index = 0
        self._ready = False
        self._running = True
        self._exit_requested = False
        self._latest_feedback: Optional[JointState] = None
        self._param_names = param_names

        self._pub = self.create_publisher(JointState, self._cmd_topic, 10)

        self.create_subscription(
            JointState, self._states_topic, self._on_joint_states, 10
        )

        if self._param_names:
            self._joint_names = list(self._param_names)
            self._positions = {n: 0.0 for n in self._joint_names}
            if self._seed_from_feedback:
                self._ready = False
                self.get_logger().info(
                    f'Esperando primer {self._states_topic} para copiar pose ({len(self._joint_names)} joints)…'
                )
            else:
                self._ready = True
                self.get_logger().info(f'Articulaciones: {self._joint_names}')
        else:
            self.get_logger().info(
                f'Esperando {self._states_topic} para obtener nombres de articulaciones…'
            )

        if republish > 0:
            self.create_timer(1.0 / republish, self._republish)

        self.create_timer(0.2, self._poll_exit_request)

        self._kb_thread = threading.Thread(target=self._keyboard_loop, daemon=True)
        self._kb_thread.start()

        self.get_logger().info(f'Publicando en {self._cmd_topic} — pulsa h para ayuda')

    def _poll_exit_request(self):
        if self._exit_requested:
            rclpy.shutdown()

    def _on_joint_states(self, msg: JointState):
        if not msg.name:
            return
        with self._lock:
            self._latest_feedback = msg
            if self._ready:
                return
            if self._param_names:
                pos_map = {n: float(p) for n, p in zip(msg.name, msg.position)}
                for n in self._joint_names:
                    if n in pos_map:
                        self._positions[n] = pos_map[n]
                missing = [n for n in self._joint_names if n not in pos_map]
                self._ready = True
                if missing:
                    self.get_logger().warn(
                        f'Sin datos en /joint_states para: {missing} (se deja 0 rad)'
                    )
                self.get_logger().info('Pose inicial cargada desde el robot.')
            else:
                self._joint_names = list(msg.name)
                self._positions = {
                    n: float(p) for n, p in zip(msg.name, msg.position)
                }
                self._index = 0
                self._ready = True
                self.get_logger().info(f'Articulaciones desde feedback: {len(self._joint_names)} joints')

    def _grab_from_feedback(self):
        with self._lock:
            if self._latest_feedback is None:
                self.get_logger().warn(f'Sin mensajes en {self._states_topic} todavía')
                return
            msg = self._latest_feedback
            pos_map = {n: float(p) for n, p in zip(msg.name, msg.position)}
            updated = 0
            for n in self._joint_names:
                if n in pos_map:
                    self._positions[n] = pos_map[n]
                    updated += 1
        self.get_logger().info(f'g: sincronizado {updated} articulaciones desde feedback')
        self._publish()

    def _publish(self):
        if not self._ready or not self._joint_names:
            return
        with self._lock:
            msg = JointState()
            msg.header = Header()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.name = list(self._joint_names)
            msg.position = [float(self._positions[n]) for n in self._joint_names]
            msg.velocity = []
            msg.effort = []
        self._pub.publish(msg)

    def _republish(self):
        self._publish()

    def _apply_key(self, ch: str):
        if ch == 'q':
            self._running = False
            self._exit_requested = True
            self.get_logger().info('Saliendo…')
            return

        if ch == 'h' or ch == '?':
            print(HELP_TEXT, flush=True)
            return

        if ch == 'g':
            self._grab_from_feedback()
            return

        if not self._ready:
            self.get_logger().warn('Esperando /joint_states…')
            return

        with self._lock:
            n = len(self._joint_names)
            if n == 0:
                return
            name = self._joint_names[self._index]

            if ch == '[':
                self._index = (self._index - 1) % n
            elif ch == ']':
                self._index = (self._index + 1) % n
            elif ch == '=' or ch == '+':
                self._positions[name] = self._positions.get(name, 0.0) + self._step
            elif ch == '-' or ch == '_':
                self._positions[name] = self._positions.get(name, 0.0) - self._step
            elif ch == '0':
                self._positions[name] = 0.0
            else:
                return

        sel = self._joint_names[self._index]
        self.get_logger().info(
            f'[{self._index + 1}/{n}] {sel} = {self._positions[sel]:.4f} rad'
        )
        self._publish()

    def _keyboard_loop(self):
        old_settings = None
        try:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except termios.error:
            self.get_logger().error(
                'stdin no es una TTY. Ejecuta en una terminal: '
                'ros2 run max_control joint_teleop_node'
            )
            return

        try:
            print(HELP_TEXT, flush=True)
            while self._running and rclpy.ok():
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if r:
                    ch = sys.stdin.read(1)
                    if ch:
                        self._apply_key(ch)
        finally:
            if old_settings is not None:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def destroy_node(self):
        self._running = False
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = JointTeleopNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
