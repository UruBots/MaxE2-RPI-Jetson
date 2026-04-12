import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt16

from max_interfaces.msg import AprilTagArray


def _sanitize_led_preset(raw: str, fallback: str) -> str:
    s = (raw or '').strip().lower()
    if s in ('', 'false', 'true', 'none', 'null'):
        return fallback
    return s


class AprilTagHeadSearchNode(Node):
    """Search and track an AprilTag using head, LEDs and body motions."""

    STATE_SEARCH = 'search'
    STATE_CENTER = 'center'

    def __init__(self):
        super().__init__('apriltag_head_search_node')

        self.declare_parameter('detections_topic', '/max/apriltag_detections')
        self.declare_parameter('head_raw_topic', '/max/head_cmd_raw')
        self.declare_parameter('head_preset_topic', '/max/head_preset')
        self.declare_parameter('led_topic', '/max/led_preset')
        self.declare_parameter('motion_topic', '/max/motion_cmd')
        self.declare_parameter('status_topic', '/max/head_search_status')

        self.declare_parameter('target_tag_id', -1)
        self.declare_parameter('detection_timeout', 0.5)
        self.declare_parameter('control_rate', 8.0)
        self.declare_parameter('head_dead_zone_px', 20.0)
        self.declare_parameter('head_step_raw', 8)
        self.declare_parameter('body_dead_zone', 0.12)
        self.declare_parameter('body_assist_threshold', 120)
        self.declare_parameter('body_motion_cooldown_sec', 1.2)
        self.declare_parameter('center_head_on_detect', False)
        self.declare_parameter('center_head_when_body_turns', True)
        self.declare_parameter('search_motion_enabled', False)
        self.declare_parameter('search_motion_command', 'turn_left')
        self.declare_parameter('distance_control_enabled', True)
        self.declare_parameter('target_size_px', 90.0)
        self.declare_parameter('size_tolerance_px', 15.0)
        self.declare_parameter('forward_motion_command', 'walk')
        self.declare_parameter('reverse_motion_command', 'reverse')
        self.declare_parameter('search_led_command', 'red')
        self.declare_parameter('tracking_led_command', 'blue')
        self.declare_parameter('centered_led_command', 'magenta')
        self.declare_parameter('lost_led_command', 'off')

        self.declare_parameter('scan_min_raw', 344)
        self.declare_parameter('scan_max_raw', 680)
        self.declare_parameter('scan_step_raw', 20)
        self.declare_parameter('scan_start_raw', 512)
        self.declare_parameter('scan_pause_sec', 0.15)

        self._detections_topic = self.get_parameter(
            'detections_topic'
        ).get_parameter_value().string_value
        self._head_raw_topic = self.get_parameter(
            'head_raw_topic'
        ).get_parameter_value().string_value
        self._head_preset_topic = self.get_parameter(
            'head_preset_topic'
        ).get_parameter_value().string_value
        self._led_topic = self.get_parameter('led_topic').get_parameter_value().string_value
        self._motion_topic = self.get_parameter('motion_topic').get_parameter_value().string_value
        self._status_topic = self.get_parameter('status_topic').get_parameter_value().string_value

        self._target_tag_id = self.get_parameter('target_tag_id').get_parameter_value().integer_value
        self._detection_timeout = self.get_parameter(
            'detection_timeout'
        ).get_parameter_value().double_value
        self._head_dead_zone_px = self.get_parameter(
            'head_dead_zone_px'
        ).get_parameter_value().double_value
        self._head_step_raw = max(
            1, self.get_parameter('head_step_raw').get_parameter_value().integer_value
        )
        self._body_dead_zone = self.get_parameter(
            'body_dead_zone'
        ).get_parameter_value().double_value
        self._body_assist_threshold = max(
            1, self.get_parameter('body_assist_threshold').get_parameter_value().integer_value
        )
        self._body_motion_cooldown_sec = max(
            0.0,
            self.get_parameter('body_motion_cooldown_sec').get_parameter_value().double_value,
        )
        self._center_head_on_detect = self.get_parameter(
            'center_head_on_detect'
        ).get_parameter_value().bool_value
        self._center_head_when_body_turns = self.get_parameter(
            'center_head_when_body_turns'
        ).get_parameter_value().bool_value
        self._search_motion_enabled = self.get_parameter(
            'search_motion_enabled'
        ).get_parameter_value().bool_value
        self._search_motion_command = self.get_parameter(
            'search_motion_command'
        ).get_parameter_value().string_value
        self._distance_control_enabled = self.get_parameter(
            'distance_control_enabled'
        ).get_parameter_value().bool_value
        self._target_size_px = self.get_parameter(
            'target_size_px'
        ).get_parameter_value().double_value
        self._size_tolerance_px = max(
            0.0, self.get_parameter('size_tolerance_px').get_parameter_value().double_value
        )
        self._forward_motion_command = self.get_parameter(
            'forward_motion_command'
        ).get_parameter_value().string_value
        self._reverse_motion_command = self.get_parameter(
            'reverse_motion_command'
        ).get_parameter_value().string_value
        self._search_led_command = _sanitize_led_preset(
            self.get_parameter('search_led_command').get_parameter_value().string_value,
            'red',
        )
        self._tracking_led_command = _sanitize_led_preset(
            self.get_parameter('tracking_led_command').get_parameter_value().string_value,
            'blue',
        )
        self._centered_led_command = _sanitize_led_preset(
            self.get_parameter('centered_led_command').get_parameter_value().string_value,
            'magenta',
        )
        self._lost_led_command = _sanitize_led_preset(
            self.get_parameter('lost_led_command').get_parameter_value().string_value,
            'off',
        )

        self._scan_min_raw = self.get_parameter('scan_min_raw').get_parameter_value().integer_value
        self._scan_max_raw = self.get_parameter('scan_max_raw').get_parameter_value().integer_value
        self._scan_step_raw = max(
            1, self.get_parameter('scan_step_raw').get_parameter_value().integer_value
        )
        self._scan_position = self.get_parameter(
            'scan_start_raw'
        ).get_parameter_value().integer_value
        self._scan_direction = 1
        self._scan_pause_sec = max(
            0.0, self.get_parameter('scan_pause_sec').get_parameter_value().double_value
        )
        self._last_scan_publish_time = 0.0

        self._last_detections = None
        self._last_detection_time = None
        self._state = self.STATE_SEARCH
        self._last_motion_cmd = None
        self._last_led_cmd = None
        self._head_center_sent = False
        self._last_body_motion_time = 0.0

        self._head_raw_pub = self.create_publisher(UInt16, self._head_raw_topic, 10)
        self._head_preset_pub = self.create_publisher(String, self._head_preset_topic, 10)
        self._led_pub = self.create_publisher(String, self._led_topic, 10)
        self._motion_pub = self.create_publisher(String, self._motion_topic, 10)
        self._status_pub = self.create_publisher(String, self._status_topic, 10)

        self.create_subscription(
            AprilTagArray, self._detections_topic, self._on_detections, 10
        )

        rate = max(1.0, self.get_parameter('control_rate').get_parameter_value().double_value)
        self.create_timer(1.0 / rate, self._control_loop)

        self.get_logger().info(
            f'apriltag_head_search_node listo: detect={self._detections_topic}, '
            f'head={self._head_raw_topic}, led={self._led_topic}, motion={self._motion_topic}'
        )

    def _publish_status(self, detail):
        msg = String()
        msg.data = f'{self._state}:{detail}'
        self._status_pub.publish(msg)

    def _set_motion(self, command):
        if command == self._last_motion_cmd:
            return
        msg = String()
        msg.data = command
        self._motion_pub.publish(msg)
        self._last_motion_cmd = command

    def _set_led(self, command):
        if not command or command == self._last_led_cmd:
            return
        msg = String()
        msg.data = command
        self._led_pub.publish(msg)
        self._last_led_cmd = command

    def _publish_head_raw(self, value):
        raw = int(max(self._scan_min_raw, min(self._scan_max_raw, value)))
        self._scan_position = raw
        self._head_raw_pub.publish(UInt16(data=raw))

    def _set_state(self, new_state):
        if new_state == self._state:
            return
        self._state = new_state
        self._publish_status('transition')
        if new_state == self.STATE_SEARCH:
            self._head_center_sent = False
            self._set_motion('stop')
            self._set_led(self._search_led_command)
        elif new_state == self.STATE_CENTER and self._center_head_on_detect:
            msg = String()
            msg.data = 'center'
            self._head_preset_pub.publish(msg)
            self._head_center_sent = True
            self._scan_position = (self._scan_min_raw + self._scan_max_raw) // 2

    def _on_detections(self, msg: AprilTagArray):
        self._last_detections = msg
        self._last_detection_time = time.monotonic()

    def _get_recent_target(self):
        if self._last_detection_time is None:
            return None
        if (time.monotonic() - self._last_detection_time) > self._detection_timeout:
            return None
        if self._last_detections is None or not self._last_detections.detections:
            return None

        detections = list(self._last_detections.detections)
        if self._target_tag_id >= 0:
            detections = [d for d in detections if d.tag_id == self._target_tag_id]
            if not detections:
                return None
        return max(detections, key=lambda d: d.size_px)

    def _publish_scan_position(self):
        now = time.monotonic()
        if (now - self._last_scan_publish_time) < self._scan_pause_sec:
            return

        self._scan_position += self._scan_direction * self._scan_step_raw
        if self._scan_position >= self._scan_max_raw:
            self._scan_position = self._scan_max_raw
            self._scan_direction = -1
        elif self._scan_position <= self._scan_min_raw:
            self._scan_position = self._scan_min_raw
            self._scan_direction = 1

        self._publish_head_raw(self._scan_position)
        self._last_scan_publish_time = now
        self._set_led(self._search_led_command)
        if self._search_motion_enabled:
            self._set_motion(self._search_motion_command)
        self._publish_status(f'scan:{self._scan_position}')

    def _body_motion_allowed(self):
        return (time.monotonic() - self._last_body_motion_time) >= self._body_motion_cooldown_sec

    def _track_head(self, target):
        half_w = target.frame_width / 2.0
        if half_w <= 0:
            return 0.0, False

        pixel_error = target.cx - half_w
        normalized_error = pixel_error / half_w
        turning_head = False

        if pixel_error < -self._head_dead_zone_px:
            self._publish_head_raw(self._scan_position + self._head_step_raw)
            turning_head = True
        elif pixel_error > self._head_dead_zone_px:
            self._publish_head_raw(self._scan_position - self._head_step_raw)
            turning_head = True

        return normalized_error, turning_head

    def _control_loop(self):
        target = self._get_recent_target()

        if target is None:
            self._set_state(self.STATE_SEARCH)
            self._publish_scan_position()
            return

        self._set_state(self.STATE_CENTER)
        error, turning_head = self._track_head(target)
        self._set_led(self._tracking_led_command if turning_head else self._centered_led_command)

        head_offset = self._scan_position - ((self._scan_min_raw + self._scan_max_raw) // 2)
        self._publish_status(
            f'tag:{target.tag_id}:error={error:.3f}:size={target.size_px:.1f}:head={self._scan_position}:offset={head_offset}'
        )

        if abs(error) <= self._body_dead_zone and not turning_head:
            if self._distance_control_enabled:
                size_error = target.size_px - self._target_size_px
                if size_error < -self._size_tolerance_px:
                    self._set_motion(self._forward_motion_command)
                elif size_error > self._size_tolerance_px:
                    self._set_motion(self._reverse_motion_command)
                else:
                    self._set_motion('stop')
            else:
                self._set_motion('stop')
            return

        if abs(head_offset) < self._body_assist_threshold or not self._body_motion_allowed():
            self._set_motion('stop')
            return

        if self._center_head_when_body_turns:
            msg = String()
            msg.data = 'center'
            self._head_preset_pub.publish(msg)
            self._head_center_sent = True
            self._scan_position = (self._scan_min_raw + self._scan_max_raw) // 2

        if head_offset > 0:
            self._set_motion('turn_left')
        else:
            self._set_motion('turn_right')
        self._last_body_motion_time = time.monotonic()


def main(args=None):
    rclpy.init(args=args)
    node = AprilTagHeadSearchNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
