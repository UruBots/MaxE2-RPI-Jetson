import time
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

from max_interfaces.msg import AprilTagArray


KNOWN_ACTIONS = {
    'follow', 'stop', 'sprint', 'reverse',
    'spin_left', 'spin_right', 'dance', 'idle',
}


class ActionExecutorNode(Node):
    """Maps AprilTag IDs to robot actions and publishes velocity commands."""

    def __init__(self):
        super().__init__('action_executor_node')

        self.declare_parameter('tag_action_map',
                               '0:follow,1:stop,2:spin_left,3:spin_right,4:reverse,5:sprint,6:dance')
        self.declare_parameter('default_action', 'stop')
        self.declare_parameter('action_timeout', 2.0)
        self.declare_parameter('control_rate', 30.0)
        self.declare_parameter('output_mode', 'twist')
        self.declare_parameter('motion_topic', '/max/motion_cmd')

        self.declare_parameter('follow_linear_speed', 0.15)
        self.declare_parameter('follow_angular_gain', 1.0)
        self.declare_parameter('follow_dead_zone', 0.08)
        self.declare_parameter('follow_min_size', 30.0)
        self.declare_parameter('follow_max_size', 200.0)

        self.declare_parameter('sprint_speed', 0.4)
        self.declare_parameter('reverse_speed', 0.15)
        self.declare_parameter('spin_speed', 0.5)
        self.declare_parameter('dance_speed', 0.6)
        self.declare_parameter('dance_period', 0.5)

        self._tag_action_map = self._parse_tag_map()
        self._default_action = (
            self.get_parameter('default_action').get_parameter_value().string_value
        )

        self._last_tags = None
        self._last_tags_time = None
        self._current_action = 'idle'
        self._current_tag_id = -1
        self._output_mode = self.get_parameter('output_mode').get_parameter_value().string_value

        self._action_start_time = time.monotonic()

        self.create_subscription(
            AprilTagArray, '/max/apriltag_detections', self._on_tags, 10
        )

        self._cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self._action_pub = self.create_publisher(String, '/max/current_action', 10)
        self._motion_pub = self.create_publisher(
            String, self.get_parameter('motion_topic').get_parameter_value().string_value, 10
        )

        rate = self.get_parameter('control_rate').get_parameter_value().double_value
        self.create_timer(1.0 / rate, self._control_loop)

        self.get_logger().info(f'Action executor ready — map: {self._tag_action_map}')

    def _parse_tag_map(self):
        raw = self.get_parameter('tag_action_map').get_parameter_value().string_value
        mapping = {}
        for pair in raw.split(','):
            pair = pair.strip()
            if ':' not in pair:
                continue
            k, v = pair.split(':', 1)
            try:
                tag_id = int(k.strip())
            except ValueError:
                self.get_logger().warn(f'Invalid tag id in map: {k}')
                continue
            action = v.strip().lower()
            if action not in KNOWN_ACTIONS:
                self.get_logger().warn(
                    f'Unknown action "{action}" for tag {tag_id}, will publish as custom'
                )
            mapping[tag_id] = action
        return mapping

    def _on_tags(self, msg: AprilTagArray):
        self._last_tags = msg
        self._last_tags_time = time.monotonic()

    def _tags_recent(self):
        if self._last_tags_time is None:
            return False
        timeout = self.get_parameter('action_timeout').get_parameter_value().double_value
        return (time.monotonic() - self._last_tags_time) < timeout

    def _pick_primary_tag(self):
        """Select the largest (closest) detected tag."""
        if self._last_tags is None or not self._last_tags.detections:
            return None
        return max(self._last_tags.detections, key=lambda t: t.size_px)

    def _control_loop(self):
        twist = Twist()
        now = time.monotonic()

        if not self._tags_recent():
            self._current_action = 'idle'
            self._current_tag_id = -1
            if self._output_mode == 'motion':
                self._motion_pub.publish(String(data='idle'))
            else:
                self._cmd_pub.publish(twist)
            self._publish_action()
            return

        tag = self._pick_primary_tag()
        if tag is None:
            self._current_action = 'idle'
            self._current_tag_id = -1
            if self._output_mode == 'motion':
                self._motion_pub.publish(String(data='idle'))
            else:
                self._cmd_pub.publish(twist)
            self._publish_action()
            return

        action = self._tag_action_map.get(tag.tag_id, self._default_action)

        if tag.tag_id != self._current_tag_id or action != self._current_action:
            self._action_start_time = now
            self._current_tag_id = tag.tag_id
            self._current_action = action
            self.get_logger().info(f'Tag {tag.tag_id} → action: {action}')

        if action == 'follow':
            twist = self._action_follow(tag)
        elif action == 'sprint':
            twist = self._action_sprint(tag)
        elif action == 'reverse':
            twist = self._action_reverse()
        elif action == 'spin_left':
            twist = self._action_spin(1.0)
        elif action == 'spin_right':
            twist = self._action_spin(-1.0)
        elif action == 'dance':
            twist = self._action_dance(now)
        elif action == 'stop':
            pass  # zero twist
        else:
            pass

        if self._output_mode == 'motion':
            self._motion_pub.publish(String(data=action))
        else:
            self._cmd_pub.publish(twist)
        self._publish_action()

    def _publish_action(self):
        msg = String()
        if self._current_tag_id >= 0:
            msg.data = f'{self._current_action}[tag:{self._current_tag_id}]'
        else:
            msg.data = self._current_action
        self._action_pub.publish(msg)

    def _angular_correction(self, tag):
        """Proportional angular correction to center the tag horizontally."""
        gain = self.get_parameter('follow_angular_gain').get_parameter_value().double_value
        dead_zone = self.get_parameter('follow_dead_zone').get_parameter_value().double_value
        half_w = tag.frame_width / 2.0
        if half_w <= 0:
            return 0.0
        error = (tag.cx - half_w) / half_w
        if abs(error) < dead_zone:
            return 0.0
        return -gain * error

    def _action_follow(self, tag):
        twist = Twist()
        speed = self.get_parameter('follow_linear_speed').get_parameter_value().double_value
        min_size = self.get_parameter('follow_min_size').get_parameter_value().double_value
        max_size = self.get_parameter('follow_max_size').get_parameter_value().double_value

        twist.angular.z = self._angular_correction(tag)

        if tag.size_px > max_size:
            twist.linear.x = 0.0
        elif tag.size_px > min_size:
            twist.linear.x = speed
        return twist

    def _action_sprint(self, tag):
        twist = Twist()
        speed = self.get_parameter('sprint_speed').get_parameter_value().double_value
        twist.angular.z = self._angular_correction(tag)
        twist.linear.x = speed
        return twist

    def _action_reverse(self):
        twist = Twist()
        speed = self.get_parameter('reverse_speed').get_parameter_value().double_value
        twist.linear.x = -speed
        return twist

    def _action_spin(self, direction):
        twist = Twist()
        speed = self.get_parameter('spin_speed').get_parameter_value().double_value
        twist.angular.z = speed * direction
        return twist

    def _action_dance(self, now):
        twist = Twist()
        speed = self.get_parameter('dance_speed').get_parameter_value().double_value
        period = self.get_parameter('dance_period').get_parameter_value().double_value
        elapsed = now - self._action_start_time
        phase = math.sin(2.0 * math.pi * elapsed / period)
        twist.angular.z = speed * phase
        return twist


def main(args=None):
    rclpy.init(args=args)
    node = ActionExecutorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
