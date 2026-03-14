import time
from collections import deque

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
from std_msgs.msg import String
from max_interfaces.msg import Detection, LineDetection, AprilTagArray


COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_YELLOW = (0, 255, 255)
COLOR_CYAN = (255, 255, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (160, 160, 160)
COLOR_DARK = (40, 40, 40)
COLOR_ORANGE = (0, 165, 255)
COLOR_MAGENTA = (255, 0, 255)

SHAPE_COLORS = {
    'ball': COLOR_GREEN,
    'cube': (255, 0, 0),
    'rectangle': COLOR_ORANGE,
    'triangle': COLOR_YELLOW,
    'object': COLOR_GRAY,
}

PANEL_H = 140
FONT = cv2.FONT_HERSHEY_SIMPLEX


class DebugViewNode(Node):
    """Composites detection data onto the camera image for rqt_image_view."""

    def __init__(self):
        super().__init__('debug_view_node')

        self.declare_parameter('output_topic', '/max/debug_view')
        self.declare_parameter('show_fps', True)
        self.declare_parameter('show_panel', True)
        self.declare_parameter('show_crosshair', True)
        self.declare_parameter('show_cmd_vel', True)
        self.declare_parameter('panel_opacity', 0.7)
        self.declare_parameter('detection_timeout', 1.0)

        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        self.bridge = CvBridge()

        self._last_frame = None
        self._last_detection = None
        self._last_detection_time = None
        self._last_line = None
        self._last_line_time = None
        self._last_twist = None
        self._last_twist_time = None
        self._last_tags = None
        self._last_tags_time = None
        self._current_action = ''

        self._fps_times = deque(maxlen=60)
        self._frame_count = 0

        self.create_subscription(Image, '/max/camera/image_raw', self._on_image, 10)
        self.create_subscription(Detection, '/max/detection', self._on_detection, 10)
        self.create_subscription(LineDetection, '/max/line_detection', self._on_line, 10)
        self.create_subscription(Twist, '/cmd_vel', self._on_twist, 10)
        self.create_subscription(AprilTagArray, '/max/apriltag_detections', self._on_tags, 10)
        self.create_subscription(String, '/max/current_action', self._on_action, 10)

        self._pub = self.create_publisher(Image, output_topic, 10)

        self.get_logger().info(
            f'Debug view publishing on {output_topic} — open with: '
            f'ros2 run rqt_image_view rqt_image_view {output_topic}'
        )

    def _on_image(self, msg):
        self._last_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self._render()

    def _on_detection(self, msg):
        self._last_detection = msg
        self._last_detection_time = time.monotonic()

    def _on_line(self, msg):
        self._last_line = msg
        self._last_line_time = time.monotonic()

    def _on_twist(self, msg):
        self._last_twist = msg
        self._last_twist_time = time.monotonic()

    def _on_tags(self, msg):
        self._last_tags = msg
        self._last_tags_time = time.monotonic()

    def _on_action(self, msg):
        self._current_action = msg.data

    def _calc_fps(self):
        now = time.monotonic()
        self._fps_times.append(now)
        if len(self._fps_times) < 2:
            return 0.0
        elapsed = self._fps_times[-1] - self._fps_times[0]
        if elapsed <= 0:
            return 0.0
        return (len(self._fps_times) - 1) / elapsed

    def _is_recent(self, t):
        if t is None:
            return False
        timeout = self.get_parameter('detection_timeout').get_parameter_value().double_value
        return (time.monotonic() - t) < timeout

    def _draw_crosshair(self, canvas):
        h, w = canvas.shape[:2]
        cx, cy = w // 2, h // 2
        length = 20
        cv2.line(canvas, (cx - length, cy), (cx + length, cy), COLOR_GRAY, 1)
        cv2.line(canvas, (cx, cy - length), (cx, cy + length), COLOR_GRAY, 1)

    def _draw_detection(self, canvas, det):
        if not det.detected:
            return

        color = SHAPE_COLORS.get(det.label, COLOR_GREEN) if det.label else COLOR_GREEN
        cv2.circle(canvas, (det.cx, det.cy), 12, color, 2)
        cv2.circle(canvas, (det.cx, det.cy), 3, color, -1)

        h, w = canvas.shape[:2]
        cv2.line(canvas, (w // 2, h // 2), (det.cx, det.cy), color, 1)

        label = det.label if det.label else 'color'
        txt = f'{label} ({det.cx},{det.cy}) a:{det.area}'
        cv2.putText(canvas, txt, (det.cx + 15, det.cy - 5), FONT, 0.45, color, 1)

    def _draw_line_detection(self, canvas, line):
        if not line.detected:
            return

        h, w = canvas.shape[:2]
        cv2.line(canvas, (0, line.roi_y_start), (w, line.roi_y_start), COLOR_CYAN, 1)
        cv2.circle(canvas, (line.cx, line.cy), 8, COLOR_RED, -1)

        angle_rad = np.radians(line.angle)
        dx = int(40 * np.sin(angle_rad))
        dy = int(40 * np.cos(angle_rad))
        cv2.line(canvas, (line.cx - dx, line.cy + dy),
                 (line.cx + dx, line.cy - dy), COLOR_YELLOW, 2)

        txt = f'line off:{line.offset_x:+.2f} ang:{line.angle:.1f}'
        cv2.putText(canvas, txt, (line.cx + 12, line.cy + 15),
                    FONT, 0.42, COLOR_YELLOW, 1)

    def _draw_apriltags(self, canvas, tags):
        for tag in tags.detections:
            pts = []
            for i in range(4):
                px = int(tag.corners[i * 2])
                py = int(tag.corners[i * 2 + 1])
                pts.append((px, py))
            for i in range(4):
                cv2.line(canvas, pts[i], pts[(i + 1) % 4], COLOR_MAGENTA, 2)
            cv2.circle(canvas, (tag.cx, tag.cy), 5, COLOR_MAGENTA, -1)
            cv2.putText(canvas, f'ID:{tag.tag_id}', (tag.cx + 10, tag.cy - 10),
                        FONT, 0.55, COLOR_MAGENTA, 2)

    def _draw_panel(self, canvas):
        h, w = canvas.shape[:2]
        opacity = self.get_parameter('panel_opacity').get_parameter_value().double_value

        overlay = canvas.copy()
        cv2.rectangle(overlay, (0, 0), (w, PANEL_H), COLOR_DARK, -1)
        cv2.addWeighted(overlay, opacity, canvas, 1.0 - opacity, 0, canvas)

        y = 16

        fps = self._calc_fps()
        fps_color = COLOR_GREEN if fps >= 20 else COLOR_YELLOW if fps >= 10 else COLOR_RED
        cv2.putText(canvas, f'FPS: {fps:.1f}', (8, y), FONT, 0.5, fps_color, 1)
        cv2.putText(canvas, f'{w}x{h}', (130, y), FONT, 0.4, COLOR_GRAY, 1)

        y += 22
        det = self._last_detection
        det_active = self._is_recent(self._last_detection_time) and det is not None
        if det_active and det.detected:
            label = det.label if det.label else 'color'
            cv2.putText(canvas, f'DET: {label} ({det.cx},{det.cy}) area={det.area} '
                        f'conf={det.confidence:.2f}',
                        (8, y), FONT, 0.42, COLOR_GREEN, 1)
        else:
            cv2.putText(canvas, 'DET: ---', (8, y), FONT, 0.42, COLOR_RED, 1)

        y += 20
        line = self._last_line
        line_active = self._is_recent(self._last_line_time) and line is not None
        if line_active and line.detected:
            cv2.putText(canvas, f'LINE: offset={line.offset_x:+.2f} angle={line.angle:.1f} '
                        f'w={line.line_width}',
                        (8, y), FONT, 0.42, COLOR_CYAN, 1)
        else:
            cv2.putText(canvas, 'LINE: ---', (8, y), FONT, 0.42, COLOR_GRAY, 1)

        y += 20
        tw = self._last_twist
        tw_active = self._is_recent(self._last_twist_time) and tw is not None
        if tw_active:
            cv2.putText(canvas, f'CMD: lin={tw.linear.x:+.3f} ang={tw.angular.z:+.3f}',
                        (8, y), FONT, 0.42, COLOR_ORANGE, 1)
            bar_cx = w - 70
            bar_cy = 50
            bar_len = 40
            lin_px = int(np.clip(tw.linear.x, -1.0, 1.0) * bar_len)
            ang_px = int(np.clip(tw.angular.z, -1.0, 1.0) * bar_len)
            cv2.rectangle(canvas, (bar_cx - 1, bar_cy - bar_len - 1),
                          (bar_cx + 1, bar_cy + bar_len + 1), COLOR_GRAY, 1)
            cv2.rectangle(canvas, (bar_cx - bar_len - 1, bar_cy - 1),
                          (bar_cx + bar_len + 1, bar_cy + 1), COLOR_GRAY, 1)
            if lin_px != 0:
                cv2.line(canvas, (bar_cx, bar_cy), (bar_cx, bar_cy - lin_px), COLOR_GREEN, 3)
            if ang_px != 0:
                cv2.line(canvas, (bar_cx, bar_cy), (bar_cx - ang_px, bar_cy), COLOR_YELLOW, 3)
            cv2.circle(canvas, (bar_cx, bar_cy), 3, COLOR_WHITE, -1)
            cv2.putText(canvas, 'vel', (bar_cx - 10, bar_cy + bar_len + 15),
                        FONT, 0.35, COLOR_GRAY, 1)
        else:
            cv2.putText(canvas, 'CMD: ---', (8, y), FONT, 0.42, COLOR_GRAY, 1)

        y += 20
        tags = self._last_tags
        tags_active = self._is_recent(self._last_tags_time) and tags is not None
        if tags_active and tags.detections:
            ids = [str(t.tag_id) for t in tags.detections]
            cv2.putText(canvas, f'TAGS: [{", ".join(ids)}]',
                        (8, y), FONT, 0.42, COLOR_MAGENTA, 1)
        else:
            cv2.putText(canvas, 'TAGS: ---', (8, y), FONT, 0.42, COLOR_GRAY, 1)

        y += 20
        mode_parts = []
        if det_active and det.detected:
            mode_parts.append('TRACKING')
        if line_active and line.detected:
            mode_parts.append('LINE')
        if tags_active and tags.detections:
            mode_parts.append('APRILTAG')
        mode_str = ' + '.join(mode_parts) if mode_parts else 'IDLE'
        mode_color = COLOR_GREEN if mode_parts else COLOR_GRAY

        if self._current_action and self._current_action != 'idle':
            mode_str += f'  ACTION: {self._current_action}'
            mode_color = COLOR_MAGENTA

        cv2.putText(canvas, f'MODE: {mode_str}', (8, y), FONT, 0.42, mode_color, 1)

    def _render(self):
        if self._last_frame is None:
            return

        canvas = self._last_frame.copy()

        show_crosshair = self.get_parameter('show_crosshair').get_parameter_value().bool_value
        if show_crosshair:
            self._draw_crosshair(canvas)

        if self._is_recent(self._last_detection_time) and self._last_detection is not None:
            self._draw_detection(canvas, self._last_detection)

        if self._is_recent(self._last_line_time) and self._last_line is not None:
            self._draw_line_detection(canvas, self._last_line)

        if self._is_recent(self._last_tags_time) and self._last_tags is not None:
            self._draw_apriltags(canvas, self._last_tags)

        show_panel = self.get_parameter('show_panel').get_parameter_value().bool_value
        if show_panel:
            self._draw_panel(canvas)

        msg = self.bridge.cv2_to_imgmsg(canvas, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera'
        self._pub.publish(msg)

    def destroy_node(self):
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DebugViewNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
