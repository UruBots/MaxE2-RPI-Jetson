import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String


class TwistToMotionNode(Node):
    """Convierte /cmd_vel (teclado) en comandos discretos para la CM-550."""

    def __init__(self):
        super().__init__('twist_to_motion_node')

        self.declare_parameter('motion_topic', '/max/motion_cmd')
        self.declare_parameter('forward_command', 'walk')
        self.declare_parameter('backward_command', 'reverse')
        self.declare_parameter('left_command', 'turn_left')
        self.declare_parameter('right_command', 'turn_right')
        self.declare_parameter('stop_command', 'stop')
        self.declare_parameter('linear_threshold', 0.05)
        self.declare_parameter('angular_threshold', 0.05)
        self.declare_parameter('prefer_turn_over_forward', True)

        self.motion_topic = self.get_parameter('motion_topic').get_parameter_value().string_value
        self.forward_command = self.get_parameter('forward_command').get_parameter_value().string_value
        self.backward_command = self.get_parameter('backward_command').get_parameter_value().string_value
        self.left_command = self.get_parameter('left_command').get_parameter_value().string_value
        self.right_command = self.get_parameter('right_command').get_parameter_value().string_value
        self.stop_command = self.get_parameter('stop_command').get_parameter_value().string_value
        self.lin_th = self.get_parameter('linear_threshold').get_parameter_value().double_value
        self.ang_th = self.get_parameter('angular_threshold').get_parameter_value().double_value
        self.prefer_turn = (
            self.get_parameter('prefer_turn_over_forward').get_parameter_value().bool_value
        )

        self.pub = self.create_publisher(String, self.motion_topic, 10)
        self.create_subscription(Twist, '/cmd_vel', self._on_twist, 10)

        self._last_cmd = None
        self.get_logger().info(
            f'twist_to_motion_node listo: escucha /cmd_vel y publica {self.motion_topic}'
        )

    def _publish_if_changed(self, command: str):
        if command == self._last_cmd:
            return
        msg = String()
        msg.data = command
        self.pub.publish(msg)
        self._last_cmd = command

    def _on_twist(self, msg: Twist):
        lin = msg.linear.x
        ang = msg.angular.z

        abs_lin = abs(lin)
        abs_ang = abs(ang)

        if abs_lin < self.lin_th and abs_ang < self.ang_th:
            self._publish_if_changed(self.stop_command)
            return

        if self.prefer_turn and abs_ang >= self.ang_th and abs_ang >= abs_lin:
            self._publish_if_changed(self.left_command if ang > 0 else self.right_command)
            return

        if lin > self.lin_th:
            self._publish_if_changed(self.forward_command)
        elif lin < -self.lin_th:
            self._publish_if_changed(self.backward_command)
        elif abs_ang >= self.ang_th:
            self._publish_if_changed(self.left_command if ang > 0 else self.right_command)
        else:
            self._publish_if_changed(self.stop_command)


def main(args=None):
    rclpy.init(args=args)
    node = TwistToMotionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

