import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from cv_bridge import CvBridge
from max_interfaces.msg import Detection


class DetectorNode(Node):
    """ROS2 node for camera capture and HSV-based object detection."""

    def __init__(self):
        super().__init__('detector_node')

        self.declare_parameter('camera_index', 0)
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('fps', 30.0)
        self.declare_parameter('lower_h', 0)
        self.declare_parameter('lower_s', 120)
        self.declare_parameter('lower_v', 70)
        self.declare_parameter('upper_h', 10)
        self.declare_parameter('upper_s', 255)
        self.declare_parameter('upper_v', 255)
        self.declare_parameter('lower_h2', 170)
        self.declare_parameter('upper_h2', 180)
        self.declare_parameter('use_second_range', True)
        self.declare_parameter('color_preset', 'custom')
        self.declare_parameter('min_contour_area', 500)
        self.declare_parameter('publish_debug_image', True)
        self.declare_parameter('gstreamer_pipeline', '')

        self.bridge = CvBridge()
        self.cap = None
        self._init_camera()

        self.detection_pub = self.create_publisher(Detection, '/max/detection', 10)
        self.debug_pub = self.create_publisher(Image, '/max/debug_image', 10)
        self.raw_pub = self.create_publisher(Image, '/max/camera/image_raw', 10)

        fps = self.get_parameter('fps').get_parameter_value().double_value
        self.timer = self.create_timer(1.0 / fps, self.timer_callback)

    def _init_camera(self):
        gstreamer = self.get_parameter('gstreamer_pipeline').get_parameter_value().string_value
        if gstreamer:
            self.cap = cv2.VideoCapture(gstreamer, cv2.CAP_GSTREAMER)
        else:
            idx = self.get_parameter('camera_index').get_parameter_value().integer_value
            self.cap = cv2.VideoCapture(idx)

        if not self.cap.isOpened():
            self.get_logger().error('Failed to open camera')
            return

        w = self.get_parameter('frame_width').get_parameter_value().integer_value
        h = self.get_parameter('frame_height').get_parameter_value().integer_value
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    def _get_hsv_params(self):
        preset = self.get_parameter('color_preset').get_parameter_value().string_value.lower()
        presets = {
            'red': ((0, 120, 70), (10, 255, 255), (170, 120, 70), (180, 255, 255), True),
            'orange': ((5, 150, 120), (25, 255, 255), (0, 0, 0), (0, 0, 0), False),
            'yellow': ((25, 120, 120), (40, 255, 255), (0, 0, 0), (0, 0, 0), False),
            'blue': ((90, 120, 70), (125, 255, 255), (0, 0, 0), (0, 0, 0), False),
            'green': ((40, 70, 70), (85, 255, 255), (0, 0, 0), (0, 0, 0), False),
        }

        if preset in presets:
            lower, upper, lower2, upper2, use_second = presets[preset]
        else:
            lower = (
                self.get_parameter('lower_h').get_parameter_value().integer_value,
                self.get_parameter('lower_s').get_parameter_value().integer_value,
                self.get_parameter('lower_v').get_parameter_value().integer_value,
            )
            upper = (
                self.get_parameter('upper_h').get_parameter_value().integer_value,
                self.get_parameter('upper_s').get_parameter_value().integer_value,
                self.get_parameter('upper_v').get_parameter_value().integer_value,
            )
            lower2 = (
                self.get_parameter('lower_h2').get_parameter_value().integer_value,
                self.get_parameter('lower_s').get_parameter_value().integer_value,
                self.get_parameter('lower_v').get_parameter_value().integer_value,
            )
            upper2 = (
                self.get_parameter('upper_h2').get_parameter_value().integer_value,
                self.get_parameter('upper_s').get_parameter_value().integer_value,
                self.get_parameter('upper_v').get_parameter_value().integer_value,
            )
            use_second = self.get_parameter('use_second_range').get_parameter_value().bool_value

        return {
            'lower': lower,
            'upper': upper,
            'lower2': lower2,
            'upper2': upper2,
            'use_second': use_second,
        }

    def _detect(self, frame):
        hsv_params = self._get_hsv_params()
        min_area = self.get_parameter('min_contour_area').get_parameter_value().integer_value

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, hsv_params['lower'], hsv_params['upper'])

        if hsv_params['use_second']:
            mask2 = cv2.inRange(hsv, hsv_params['lower2'], hsv_params['upper2'])
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = mask1

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.erode(mask, kernel)
        mask = cv2.dilate(mask, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid = [c for c in contours if cv2.contourArea(c) >= min_area]

        if not valid:
            return None, mask

        largest = max(valid, key=cv2.contourArea)
        M = cv2.moments(largest)
        if M['m00'] == 0:
            return None, mask

        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        area = int(cv2.contourArea(largest))

        return (cx, cy, area), mask

    def timer_callback(self):
        if self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        h, w = frame.shape[:2]
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'camera'

        raw_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        raw_msg.header = header
        self.raw_pub.publish(raw_msg)

        result, mask = self._detect(frame)

        if result is None:
            msg = Detection()
            msg.header = header
            msg.detected = False
            msg.cx = 0
            msg.cy = 0
            msg.area = 0
            msg.frame_width = w
            msg.frame_height = h
            msg.confidence = 0.0
            msg.label = ''
            self.detection_pub.publish(msg)
        else:
            cx, cy, area = result
            msg = Detection()
            msg.header = header
            msg.detected = True
            msg.cx = cx
            msg.cy = cy
            msg.area = area
            msg.frame_width = w
            msg.frame_height = h
            msg.confidence = 1.0
            msg.label = ''
            self.detection_pub.publish(msg)

        if self.get_parameter('publish_debug_image').get_parameter_value().bool_value:
            debug = frame.copy()
            cv2.line(debug, (w // 2, 0), (w // 2, h), (128, 128, 128), 1)
            if result is not None:
                cx, cy, area = result
                cv2.circle(debug, (cx, cy), 10, (0, 255, 0), 2)
                cv2.putText(debug, f'({cx},{cy}) {area}', (cx + 15, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            debug_msg = self.bridge.cv2_to_imgmsg(debug, encoding='bgr8')
            debug_msg.header = header
            self.debug_pub.publish(debug_msg)

    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DetectorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
