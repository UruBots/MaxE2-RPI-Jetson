import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from max_interfaces.msg import LineDetection


class LineTrackerNode(Node):
    """Converts line detections into velocity commands for line following."""

    def __init__(self):
        super().__init__('line_tracker_node')

        self.declare_parameter('linear_speed', 0.12)
        self.declare_parameter('angular_gain', 1.5)
        self.declare_parameter('angle_gain', 0.01)
        self.declare_parameter('dead_zone', 0.05)
        self.declare_parameter('control_rate', 30.0)
        self.declare_parameter('timeout', 0.5)
        self.declare_parameter('lost_angular_speed', 0.4)
        self.declare_parameter('lost_behavior', 'stop')

        self.last_detection = None
        self.last_detection_time = None
        self.last_offset_sign = 1.0

        self.detection_sub = self.create_subscription(
            LineDetection, '/max/line_detection', self._detection_callback, 10
        )
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        rate = self.get_parameter('control_rate').get_parameter_value().double_value
        self.timer = self.create_timer(1.0 / rate, self._control_callback)

    def _detection_callback(self, msg):
        self.last_detection = msg
        self.last_detection_time = self.get_clock().now()
        if msg.detected and abs(msg.offset_x) > 0.01:
            self.last_offset_sign = 1.0 if msg.offset_x > 0 else -1.0

    def _control_callback(self):
        twist = Twist()
        timeout = self.get_parameter('timeout').get_parameter_value().double_value
        lost_behavior = self.get_parameter('lost_behavior').get_parameter_value().string_value
        lost_speed = self.get_parameter('lost_angular_speed').get_parameter_value().double_value

        now = self.get_clock().now()
        is_recent = (
            self.last_detection_time is not None
            and (now - self.last_detection_time).nanoseconds / 1e9 < timeout
        )

        if not is_recent or self.last_detection is None or not self.last_detection.detected:
            if lost_behavior == 'rotate':
                twist.angular.z = lost_speed * self.last_offset_sign
            self.cmd_vel_pub.publish(twist)
            return

        det = self.last_detection
        linear_speed = self.get_parameter('linear_speed').get_parameter_value().double_value
        angular_gain = self.get_parameter('angular_gain').get_parameter_value().double_value
        angle_gain = self.get_parameter('angle_gain').get_parameter_value().double_value
        dead_zone = self.get_parameter('dead_zone').get_parameter_value().double_value

        offset = det.offset_x
        if abs(offset) < dead_zone:
            offset = 0.0

        angular_correction = -angular_gain * offset
        angle_correction = -angle_gain * det.angle
        twist.angular.z = angular_correction + angle_correction
        twist.linear.x = linear_speed

        self.cmd_vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = LineTrackerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
