import math
import numpy as np
import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from cv_bridge import CvBridge
from max_interfaces.msg import Detection


SHAPE_CIRCLE = 'ball'
SHAPE_SQUARE = 'cube'
SHAPE_RECTANGLE = 'rectangle'
SHAPE_TRIANGLE = 'triangle'
SHAPE_UNKNOWN = 'object'


class ShapeDetectorNode(Node):
    """Detects geometric shapes (balls, cubes, etc.) using contour analysis."""

    def __init__(self):
        super().__init__('shape_detector_node')

        self.declare_parameter('camera_index', 0)
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('fps', 30.0)
        self.declare_parameter('gstreamer_pipeline', '')
        self.declare_parameter('publish_debug_image', True)
        self.declare_parameter('use_camera_topic', False)

        self.declare_parameter('lower_h', 0)
        self.declare_parameter('lower_s', 80)
        self.declare_parameter('lower_v', 80)
        self.declare_parameter('upper_h', 180)
        self.declare_parameter('upper_s', 255)
        self.declare_parameter('upper_v', 255)
        self.declare_parameter('lower_h2', 0)
        self.declare_parameter('upper_h2', 0)
        self.declare_parameter('use_second_range', False)
        self.declare_parameter('color_preset', 'custom')
        self.declare_parameter('min_contour_area', 800)
        self.declare_parameter('max_contour_area', 100000)
        self.declare_parameter('blur_kernel', 5)
        self.declare_parameter('morph_kernel', 5)
        self.declare_parameter('circularity_threshold', 0.7)
        self.declare_parameter('square_aspect_threshold', 0.25)
        self.declare_parameter('approx_epsilon_ratio', 0.03)
        self.declare_parameter('target_shape', '')

        self.bridge = CvBridge()
        self.cap = None

        use_topic = self.get_parameter('use_camera_topic').get_parameter_value().bool_value
        if use_topic:
            self.image_sub = self.create_subscription(
                Image, '/max/camera/image_raw', self._image_callback, 10
            )
        else:
            self._init_camera()

        self.detection_pub = self.create_publisher(Detection, '/max/detection', 10)
        self.debug_pub = self.create_publisher(Image, '/max/shape_debug_image', 10)

        if not use_topic:
            fps = self.get_parameter('fps').get_parameter_value().double_value
            self.timer = self.create_timer(1.0 / fps, self._timer_callback)

    def _init_camera(self):
        gst = self.get_parameter('gstreamer_pipeline').get_parameter_value().string_value
        if gst:
            self.cap = cv2.VideoCapture(gst, cv2.CAP_GSTREAMER)
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

    def _image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self._process_frame(frame)

    def _timer_callback(self):
        if self.cap is None or not self.cap.isOpened():
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        self._process_frame(frame)

    def _classify_shape(self, contour):
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            return SHAPE_UNKNOWN, 0.0

        area = cv2.contourArea(contour)
        circularity = (4.0 * math.pi * area) / (perimeter * perimeter)

        circ_thresh = self.get_parameter('circularity_threshold').get_parameter_value().double_value
        sq_thresh = self.get_parameter('square_aspect_threshold').get_parameter_value().double_value
        eps_ratio = self.get_parameter('approx_epsilon_ratio').get_parameter_value().double_value

        if circularity >= circ_thresh:
            return SHAPE_CIRCLE, circularity

        epsilon = eps_ratio * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        vertices = len(approx)

        if vertices == 3:
            return SHAPE_TRIANGLE, circularity

        if vertices == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h if h > 0 else 0.0
            if abs(aspect_ratio - 1.0) < sq_thresh:
                return SHAPE_SQUARE, circularity
            return SHAPE_RECTANGLE, circularity

        if circularity >= 0.5:
            return SHAPE_CIRCLE, circularity

        return SHAPE_UNKNOWN, circularity

    def _process_frame(self, frame):
        fh, fw = frame.shape[:2]
        min_area = self.get_parameter('min_contour_area').get_parameter_value().integer_value
        max_area = self.get_parameter('max_contour_area').get_parameter_value().integer_value
        blur_k = self.get_parameter('blur_kernel').get_parameter_value().integer_value
        blur_k = blur_k if blur_k % 2 == 1 else blur_k + 1
        morph_k = self.get_parameter('morph_kernel').get_parameter_value().integer_value
        target = self.get_parameter('target_shape').get_parameter_value().string_value

        blurred = cv2.GaussianBlur(frame, (blur_k, blur_k), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        color_preset = self.get_parameter('color_preset').get_parameter_value().string_value.lower()
        presets = {
            'red': ((0, 120, 70), (10, 255, 255), (170, 120, 70), (180, 255, 255), True),
            'orange': ((5, 150, 120), (25, 255, 255), (0, 0, 0), (0, 0, 0), False),
            'yellow': ((25, 120, 120), (40, 255, 255), (0, 0, 0), (0, 0, 0), False),
            'blue': ((90, 120, 70), (125, 255, 255), (0, 0, 0), (0, 0, 0), False),
            'green': ((40, 70, 70), (85, 255, 255), (0, 0, 0), (0, 0, 0), False),
        }

        if color_preset in presets:
            lower1, upper1, lower2, upper2, use_second = presets[color_preset]
        else:
            lower1 = (
                self.get_parameter('lower_h').get_parameter_value().integer_value,
                self.get_parameter('lower_s').get_parameter_value().integer_value,
                self.get_parameter('lower_v').get_parameter_value().integer_value,
            )
            upper1 = (
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

        lower = np.array(lower1)
        upper = np.array(upper1)
        mask = cv2.inRange(hsv, lower, upper)
        if use_second:
            mask2 = cv2.inRange(hsv, np.array(lower2), np.array(upper2))
            mask = cv2.bitwise_or(mask, mask2)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_k, morph_k))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < min_area or area > max_area:
                continue
            shape, confidence = self._classify_shape(c)
            M = cv2.moments(c)
            if M['m00'] == 0:
                continue
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            detections.append((cx, cy, int(area), shape, confidence, c))

        if target:
            detections = [d for d in detections if d[3] == target]

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'camera'

        if detections:
            best = max(detections, key=lambda d: d[2])
            cx, cy, area, shape, confidence, contour = best

            msg = Detection()
            msg.header = header
            msg.detected = True
            msg.cx = cx
            msg.cy = cy
            msg.area = area
            msg.frame_width = fw
            msg.frame_height = fh
            msg.confidence = float(confidence)
            msg.label = shape
            self.detection_pub.publish(msg)
        else:
            msg = Detection()
            msg.header = header
            msg.detected = False
            msg.cx = 0
            msg.cy = 0
            msg.area = 0
            msg.frame_width = fw
            msg.frame_height = fh
            msg.confidence = 0.0
            msg.label = ''
            self.detection_pub.publish(msg)

        if self.get_parameter('publish_debug_image').get_parameter_value().bool_value:
            debug = frame.copy()
            cv2.line(debug, (fw // 2, 0), (fw // 2, fh), (128, 128, 128), 1)

            shape_colors = {
                SHAPE_CIRCLE: (0, 255, 0),
                SHAPE_SQUARE: (255, 0, 0),
                SHAPE_RECTANGLE: (255, 128, 0),
                SHAPE_TRIANGLE: (0, 255, 255),
                SHAPE_UNKNOWN: (128, 128, 128),
            }

            for cx, cy, area, shape, conf, contour in detections:
                color = shape_colors.get(shape, (255, 255, 255))
                cv2.drawContours(debug, [contour], -1, color, 2)
                cv2.circle(debug, (cx, cy), 6, color, -1)
                cv2.putText(
                    debug, f'{shape} {conf:.2f}',
                    (cx + 10, cy - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
                )

            debug_msg = self.bridge.cv2_to_imgmsg(debug, encoding='bgr8')
            debug_msg.header = header
            self.debug_pub.publish(debug_msg)

    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ShapeDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
