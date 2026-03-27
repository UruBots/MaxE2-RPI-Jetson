import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt16


class FailsafeNode(Node):
    """Envía stop/stand y velocidad 0 si no hay comandos recientes en /max/motion_cmd."""

    def __init__(self):
        super().__init__('failsafe_node')
        self.declare_parameter('motion_topic', '/max/motion_cmd')
        self.declare_parameter('speed_topic', '/max/profile_velocity')
        self.declare_parameter('timeout_sec', 2.0)
        self.declare_parameter('stop_command', 'stop')
        self.declare_parameter('fallback_command', 'stand')

        self.motion_topic = self.get_parameter('motion_topic').get_parameter_value().string_value
        self.speed_topic = self.get_parameter('speed_topic').get_parameter_value().string_value
        self.timeout = max(0.1, self.get_parameter('timeout_sec').get_parameter_value().double_value)
        self.stop_cmd = self.get_parameter('stop_command').get_parameter_value().string_value
        self.fallback_cmd = self.get_parameter('fallback_command').get_parameter_value().string_value

        self.motion_pub = self.create_publisher(String, self.motion_topic, 10)
        self.speed_pub = self.create_publisher(UInt16, self.speed_topic, 10)
        self.create_subscription(String, self.motion_topic, self._on_motion, 10)

        self._last_time = time.monotonic()
        self.create_timer(0.2, self._check_timeout)

        self.get_logger().info(f'failsafe_node listo: timeout={self.timeout}s topic={self.motion_topic}')

    def _on_motion(self, _msg: String):
        self._last_time = time.monotonic()

    def _publish(self, cmd):
        self.motion_pub.publish(String(data=cmd))
        self.speed_pub.publish(UInt16(data=0))

    def _check_timeout(self):
        if (time.monotonic() - self._last_time) < self.timeout:
            return
        self._publish(self.stop_cmd)
        if self.fallback_cmd and self.fallback_cmd != self.stop_cmd:
            self._publish(self.fallback_cmd)
        self._last_time = time.monotonic()


def main(args=None):
    rclpy.init(args=args)
    node = FailsafeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

