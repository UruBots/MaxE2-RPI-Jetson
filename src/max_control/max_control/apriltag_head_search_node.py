import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt16

from max_interfaces.msg import AprilTagArray


class AprilTagHeadSearchNode(Node):
    """Sweep the head until an AprilTag is found, then center body and head."""

    STATE_SEARCH = 'search'
    STATE_CENTER = 'center'

    def __init__(self):
        super().__init__('apriltag_head_search_node')

        self.declare_parameter('detections_topic', '/max/apriltag_detections')
        self.declare_parameter('head_raw_topic', '/max/head_cmd_raw')
        self.declare_parameter('head_preset_topic', '/max/head_preset')
        self.declare_parameter('motion_topic', '/max/motion_cmd')
        self.declare_parameter('status_topic', '/max/head_search_status')

        self.declare_parameter('target_tag_id', -1)
        self.declare_parameter('detection_timeout', 0.5)
        self.declare_parameter('control_rate', 8.0)
        self.declare_parameter('body_dead_zone', 0.12)
        self.declare_parameter('center_head_on_detect', True)

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
        self._motion_topic = self.get_parameter('motion_topic').get_parameter_value().string_value
        self._status_topic = self.get_parameter('status_topic').get_parameter_value().string_value

        self._target_tag_id = self.get_parameter('target_tag_id').get_parameter_value().integer_value
        self._detection_timeout = self.get_parameter(
            'detection_timeout'
        ).get_parameter_value().double_value
        self._body_dead_zone = self.get_parameter(
            'body_dead_zone'
        ).get_parameter_value().double_value
        self._center_head_on_detect = self.get_parameter(
            'center_head_on_detect'
        ).get_parameter_value().bool_value

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
        self._head_center_sent = False

        self._head_raw_pub = self.create_publisher(UInt16, self._head_raw_topic, 10)
        self._head_preset_pub = self.create_publisher(String, self._head_preset_topic, 10)
        self._motion_pub = self.create_publisher(String, self._motion_topic, 10)
        self._status_pub = self.create_publisher(String, self._status_topic, 10)

        self.create_subscription(
            AprilTagArray, self._detections_topic, self._on_detections, 10
        )

        rate = max(1.0, self.get_parameter('control_rate').get_parameter_value().double_value)
        self.create_timer(1.0 / rate, self._control_loop)

        self.get_logger().info(
            f'apriltag_head_search_node listo: detect={self._detections_topic}, '
            f'head={self._head_raw_topic}, motion={self._motion_topic}'
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

    def _set_state(self, new_state):
        if new_state == self._state:
            return
        self._state = new_state
        self._publish_status('transition')
        if new_state == self.STATE_SEARCH:
            self._head_center_sent = False
            self._set_motion('stop')
        elif new_state == self.STATE_CENTER and self._center_head_on_detect:
            msg = String()
            msg.data = 'center'
            self._head_preset_pub.publish(msg)
            self._head_center_sent = True

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

        self._head_raw_pub.publish(UInt16(data=self._scan_position))
        self._last_scan_publish_time = now
        self._publish_status(f'scan:{self._scan_position}')

    def _control_loop(self):
        target = self._get_recent_target()

        if target is None:
            self._set_state(self.STATE_SEARCH)
            self._publish_scan_position()
            return

        self._set_state(self.STATE_CENTER)

        half_w = target.frame_width / 2.0
        if half_w <= 0:
            self._set_motion('stop')
            return

        error = (target.cx - half_w) / half_w
        self._publish_status(f'tag:{target.tag_id}:error={error:.3f}')

        if abs(error) <= self._body_dead_zone:
            self._set_motion('stop')
            if not self._head_center_sent and self._center_head_on_detect:
                msg = String()
                msg.data = 'center'
                self._head_preset_pub.publish(msg)
                self._head_center_sent = True
            return

        if self._center_head_on_detect and not self._head_center_sent:
            msg = String()
            msg.data = 'center'
            self._head_preset_pub.publish(msg)
            self._head_center_sent = True

        if error < 0.0:
            self._set_motion('turn_left')
        else:
            self._set_motion('turn_right')


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
