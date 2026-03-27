import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String, UInt16
from max_interfaces.msg import Detection


class TrackerNode(Node):
    """Track objects using head, LEDs and optional body motions."""

    def __init__(self):
        super().__init__('tracker_node')

        self.declare_parameter('linear_speed', 0.15)
        self.declare_parameter('angular_gain', 1.0)
        self.declare_parameter('dead_zone', 0.08)
        self.declare_parameter('min_area', 1000)
        self.declare_parameter('max_area', 50000)
        self.declare_parameter('distance_control_enabled', True)
        self.declare_parameter('target_area', 12000)
        self.declare_parameter('area_tolerance', 2500)
        self.declare_parameter('control_rate', 30.0)
        self.declare_parameter('timeout', 0.5)
        self.declare_parameter('search_enabled', False)
        self.declare_parameter('search_angular_speed', 0.3)
        self.declare_parameter('output_mode', 'twist')
        self.declare_parameter('motion_topic', '/max/motion_cmd')
        self.declare_parameter('head_raw_topic', '/max/head_cmd_raw')
        self.declare_parameter('led_topic', '/max/led_preset')
        self.declare_parameter('forward_command', 'walk')
        self.declare_parameter('left_command', 'turn_left')
        self.declare_parameter('right_command', 'turn_right')
        self.declare_parameter('reverse_command', 'reverse')
        self.declare_parameter('stop_command', 'stop')
        self.declare_parameter('search_command', 'turn_left')
        self.declare_parameter('head_tracking_enabled', False)
        self.declare_parameter('search_head_enabled', False)
        self.declare_parameter('search_led_command', 'red')
        self.declare_parameter('tracking_led_command', 'blue')
        self.declare_parameter('centered_led_command', 'magenta')
        self.declare_parameter('lost_led_command', 'off')
        self.declare_parameter('head_dead_zone_px', 20.0)
        self.declare_parameter('head_step_raw', 8)
        self.declare_parameter('head_min_raw', 344)
        self.declare_parameter('head_max_raw', 680)
        self.declare_parameter('head_center_raw', 512)
        self.declare_parameter('head_search_step_raw', 18)
        self.declare_parameter('head_search_pause_sec', 0.15)
        self.declare_parameter('body_assist_threshold', 120)
        self.declare_parameter('body_motion_cooldown_sec', 1.2)
        self.declare_parameter('center_head_when_body_turns', True)

        self.last_detection = None
        self.last_detection_time = None
        self.last_motion_command = None
        self.output_mode = self.get_parameter('output_mode').get_parameter_value().string_value
        self.motion_topic = self.get_parameter('motion_topic').get_parameter_value().string_value
        self.distance_control_enabled = (
            self.get_parameter('distance_control_enabled').get_parameter_value().bool_value
        )
        self.target_area = self.get_parameter('target_area').get_parameter_value().integer_value
        self.area_tolerance = max(
            0, self.get_parameter('area_tolerance').get_parameter_value().integer_value
        )
        self.head_raw_topic = self.get_parameter('head_raw_topic').get_parameter_value().string_value
        self.led_topic = self.get_parameter('led_topic').get_parameter_value().string_value
        self.head_tracking_enabled = (
            self.get_parameter('head_tracking_enabled').get_parameter_value().bool_value
        )
        self.search_head_enabled = (
            self.get_parameter('search_head_enabled').get_parameter_value().bool_value
        )
        self.search_led_command = self.get_parameter(
            'search_led_command'
        ).get_parameter_value().string_value
        self.tracking_led_command = self.get_parameter(
            'tracking_led_command'
        ).get_parameter_value().string_value
        self.centered_led_command = self.get_parameter(
            'centered_led_command'
        ).get_parameter_value().string_value
        self.lost_led_command = self.get_parameter(
            'lost_led_command'
        ).get_parameter_value().string_value
        self.head_dead_zone_px = self.get_parameter(
            'head_dead_zone_px'
        ).get_parameter_value().double_value
        self.head_step_raw = max(
            1, self.get_parameter('head_step_raw').get_parameter_value().integer_value
        )
        self.head_min_raw = self.get_parameter('head_min_raw').get_parameter_value().integer_value
        self.head_max_raw = self.get_parameter('head_max_raw').get_parameter_value().integer_value
        self.head_center_raw = self.get_parameter(
            'head_center_raw'
        ).get_parameter_value().integer_value
        self.head_search_step_raw = max(
            1, self.get_parameter('head_search_step_raw').get_parameter_value().integer_value
        )
        self.head_search_pause_sec = max(
            0.0, self.get_parameter('head_search_pause_sec').get_parameter_value().double_value
        )
        self.body_assist_threshold = max(
            1, self.get_parameter('body_assist_threshold').get_parameter_value().integer_value
        )
        self.body_motion_cooldown_sec = max(
            0.0,
            self.get_parameter('body_motion_cooldown_sec').get_parameter_value().double_value,
        )
        self.center_head_when_body_turns = (
            self.get_parameter('center_head_when_body_turns').get_parameter_value().bool_value
        )
        self.last_led_command = None
        self.head_raw_position = self.head_center_raw
        self.head_scan_direction = 1
        self.last_head_scan_time = 0.0
        self.last_body_motion_time = 0.0

        self.detection_sub = self.create_subscription(
            Detection,
            '/max/detection',
            self._detection_callback,
            10,
        )
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.motion_pub = self.create_publisher(String, self.motion_topic, 10)
        self.head_pub = self.create_publisher(UInt16, self.head_raw_topic, 10)
        self.led_pub = self.create_publisher(String, self.led_topic, 10)

        control_rate = self.get_parameter('control_rate').get_parameter_value().double_value
        self.control_timer = self.create_timer(1.0 / control_rate, self._control_callback)

    def _detection_callback(self, msg: Detection):
        self.last_detection = msg
        self.last_detection_time = self.get_clock().now()

    def _publish_motion(self, command):
        if command == self.last_motion_command:
            return
        msg = String()
        msg.data = command
        self.motion_pub.publish(msg)
        self.last_motion_command = command

    def _publish_led(self, command):
        if not command or command == self.last_led_command:
            return
        msg = String()
        msg.data = command
        self.led_pub.publish(msg)
        self.last_led_command = command

    def _publish_head_raw(self, value):
        raw = int(max(self.head_min_raw, min(self.head_max_raw, value)))
        self.head_raw_position = raw
        self.head_pub.publish(UInt16(data=raw))

    def _body_motion_allowed(self):
        now_sec = self.get_clock().now().nanoseconds / 1e9
        return (now_sec - self.last_body_motion_time) >= self.body_motion_cooldown_sec

    def _track_head(self, detection):
        if not self.head_tracking_enabled or detection.frame_width <= 0:
            return 0.0, False

        half_width = detection.frame_width / 2.0
        pixel_error = detection.cx - half_width
        normalized_error = pixel_error / half_width
        turning_head = False

        if pixel_error < -self.head_dead_zone_px:
            self._publish_head_raw(self.head_raw_position + self.head_step_raw)
            turning_head = True
        elif pixel_error > self.head_dead_zone_px:
            self._publish_head_raw(self.head_raw_position - self.head_step_raw)
            turning_head = True

        return normalized_error, turning_head

    def _search_with_head(self):
        now_sec = self.get_clock().now().nanoseconds / 1e9
        if (now_sec - self.last_head_scan_time) < self.head_search_pause_sec:
            return

        self.head_raw_position += self.head_scan_direction * self.head_search_step_raw
        if self.head_raw_position >= self.head_max_raw:
            self.head_raw_position = self.head_max_raw
            self.head_scan_direction = -1
        elif self.head_raw_position <= self.head_min_raw:
            self.head_raw_position = self.head_min_raw
            self.head_scan_direction = 1

        self._publish_head_raw(self.head_raw_position)
        self.last_head_scan_time = now_sec

    def _publish_stop(self):
        stop_command = self.get_parameter('stop_command').get_parameter_value().string_value
        if self.output_mode == 'motion':
            self._publish_motion(stop_command)
        else:
            self.cmd_vel_pub.publish(Twist())

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
            self._publish_led(self.lost_led_command)
            if self.search_head_enabled:
                self._search_with_head()
            if search_enabled:
                twist.angular.z = search_angular_speed
            if self.output_mode == 'motion':
                search_command = self.get_parameter(
                    'search_command'
                ).get_parameter_value().string_value
                self._publish_motion(search_command if search_enabled else self.get_parameter(
                    'stop_command'
                ).get_parameter_value().string_value)
            else:
                self.cmd_vel_pub.publish(twist)
            return

        if not self.last_detection.detected:
            self._publish_led(self.search_led_command)
            if self.search_head_enabled:
                self._search_with_head()
            if search_enabled:
                twist.angular.z = search_angular_speed
            if self.output_mode == 'motion':
                search_command = self.get_parameter(
                    'search_command'
                ).get_parameter_value().string_value
                self._publish_motion(search_command if search_enabled else self.get_parameter(
                    'stop_command'
                ).get_parameter_value().string_value)
            else:
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

        head_error_x, turning_head = self._track_head(detection)
        if self.head_tracking_enabled:
            error_x = head_error_x
            self._publish_led(self.tracking_led_command if turning_head else self.centered_led_command)

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

        if self.output_mode == 'motion':
            head_offset = self.head_raw_position - self.head_center_raw
            if (
                self.head_tracking_enabled
                and abs(head_offset) >= self.body_assist_threshold
                and self._body_motion_allowed()
            ):
                if self.center_head_when_body_turns:
                    self._publish_head_raw(self.head_center_raw)
                if head_offset > 0:
                    command = self.get_parameter('left_command').get_parameter_value().string_value
                else:
                    command = self.get_parameter('right_command').get_parameter_value().string_value
                self.last_body_motion_time = self.get_clock().now().nanoseconds / 1e9
            elif abs(error_x) < dead_zone:
                if self.distance_control_enabled:
                    area_error = detection.area - self.target_area
                    if area_error < -self.area_tolerance:
                        command = self.get_parameter(
                            'forward_command'
                        ).get_parameter_value().string_value
                    elif area_error > self.area_tolerance:
                        command = self.get_parameter(
                            'reverse_command'
                        ).get_parameter_value().string_value
                    else:
                        command = self.get_parameter(
                            'stop_command'
                        ).get_parameter_value().string_value
                elif detection.area > min_area and detection.area <= max_area:
                    command = self.get_parameter(
                        'forward_command'
                    ).get_parameter_value().string_value
                else:
                    command = self.get_parameter(
                        'stop_command'
                    ).get_parameter_value().string_value
            elif error_x < -dead_zone:
                command = self.get_parameter('left_command').get_parameter_value().string_value
            elif error_x > dead_zone:
                command = self.get_parameter('right_command').get_parameter_value().string_value
            else:
                command = self.get_parameter('stop_command').get_parameter_value().string_value
            self._publish_motion(command)
        else:
            self.cmd_vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = TrackerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
