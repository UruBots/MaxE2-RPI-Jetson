import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from max_interfaces.msg import Detection


class TrackerNode(Node):
    """ROS2 node that converts object detections into velocity commands."""

    def __init__(self):
        super().__init__('tracker_node')

        self.declare_parameter('linear_speed', 0.15)
        self.declare_parameter('angular_gain', 1.0)
        self.declare_parameter('dead_zone', 0.08)
        self.declare_parameter('min_area', 1000)
        self.declare_parameter('max_area', 50000)
        self.declare_parameter('control_rate', 30.0)
        self.declare_parameter('timeout', 0.5)
        self.declare_parameter('search_enabled', False)
        self.declare_parameter('search_angular_speed', 0.3)

        self.last_detection = None
        self.last_detection_time = None

        self.detection_sub = self.create_subscription(
            Detection,
            '/max/detection',
            self._detection_callback,
            10,
        )
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        control_rate = self.get_parameter('control_rate').get_parameter_value().double_value
        self.control_timer = self.create_timer(1.0 / control_rate, self._control_callback)

    def _detection_callback(self, msg: Detection):
        self.last_detection = msg
        self.last_detection_time = self.get_clock().now()

    def _control_callback(self):
        twist = Twist()
        twist.linear.x = 0.0
        twist.linear.y = 0.0
        twist.linear.z = 0.0
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = 0.0

        timeout = self.get_parameter('timeout').get_parameter_value().double_value
        search_enabled = self.get_parameter('search_enabled').get_parameter_value().bool_value
        search_angular_speed = self.get_parameter('search_angular_speed').get_parameter_value().double_value

        now = self.get_clock().now()
        is_recent = (
            self.last_detection_time is not None
            and (now - self.last_detection_time).nanoseconds / 1e9 < timeout
        )

        if not is_recent or self.last_detection is None:
            if search_enabled:
                twist.angular.z = search_angular_speed
            self.cmd_vel_pub.publish(twist)
            return

        if not self.last_detection.detected:
            if search_enabled:
                twist.angular.z = search_angular_speed
            self.cmd_vel_pub.publish(twist)
            return

        detection = self.last_detection
        linear_speed = self.get_parameter('linear_speed').get_parameter_value().double_value
        angular_gain = self.get_parameter('angular_gain').get_parameter_value().double_value
        dead_zone = self.get_parameter('dead_zone').get_parameter_value().double_value
        min_area = self.get_parameter('min_area').get_parameter_value().integer_value
        max_area = self.get_parameter('max_area').get_parameter_value().integer_value

        half_width = detection.frame_width / 2.0
        if half_width > 0:
            error_x = (detection.cx - half_width) / half_width
        else:
            error_x = 0.0

        if abs(error_x) < dead_zone:
            twist.angular.z = 0.0
        else:
            twist.angular.z = -angular_gain * error_x

        if detection.area > max_area:
            twist.linear.x = 0.0
        elif detection.area > min_area:
            twist.linear.x = linear_speed
        else:
            twist.linear.x = 0.0

        self.cmd_vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = TrackerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
