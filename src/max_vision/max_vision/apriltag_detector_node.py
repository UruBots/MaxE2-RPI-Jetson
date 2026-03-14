import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from cv_bridge import CvBridge

from max_interfaces.msg import AprilTagDetection, AprilTagArray

try:
    from pupil_apriltags import Detector as AprilTagDetector
except ImportError:
    AprilTagDetector = None


COLOR_TAG = (0, 255, 0)
COLOR_ID = (255, 255, 0)
FONT = cv2.FONT_HERSHEY_SIMPLEX


class AprilTagDetectorNode(Node):
    """Detects AprilTags using pupil-apriltags and publishes their IDs and positions."""

    def __init__(self):
        super().__init__('apriltag_detector_node')

        self.declare_parameter('camera_index', 0)
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('fps', 30.0)
        self.declare_parameter('gstreamer_pipeline', '')
        self.declare_parameter('use_camera_topic', False)
        self.declare_parameter('publish_debug_image', True)

        self.declare_parameter('tag_family', 'tag36h11')
        self.declare_parameter('nthreads', 2)
        self.declare_parameter('quad_decimate', 2.0)
        self.declare_parameter('quad_sigma', 0.0)
        self.declare_parameter('decode_sharpening', 0.25)
        self.declare_parameter('refine_edges', True)

        self.bridge = CvBridge()
        self.cap = None
        self._detector = None

        self._init_detector()

        use_topic = self.get_parameter('use_camera_topic').get_parameter_value().bool_value
        if use_topic:
            self.create_subscription(Image, '/max/camera/image_raw', self._on_image, 10)
        else:
            self._init_camera()
            fps = self.get_parameter('fps').get_parameter_value().double_value
            self.create_timer(1.0 / fps, self._timer_callback)

        self._detections_pub = self.create_publisher(
            AprilTagArray, '/max/apriltag_detections', 10
        )
        self._raw_pub = self.create_publisher(Image, '/max/camera/image_raw', 10)
        self._debug_pub = self.create_publisher(Image, '/max/apriltag_debug_image', 10)

        self.get_logger().info('AprilTag detector ready')

    def _init_detector(self):
        if AprilTagDetector is None:
            self.get_logger().error(
                'pupil-apriltags not installed — run: pip install pupil-apriltags'
            )
            return

        family = self.get_parameter('tag_family').get_parameter_value().string_value
        nthreads = self.get_parameter('nthreads').get_parameter_value().integer_value
        quad_decimate = self.get_parameter('quad_decimate').get_parameter_value().double_value
        quad_sigma = self.get_parameter('quad_sigma').get_parameter_value().double_value
        decode_sharpening = self.get_parameter('decode_sharpening').get_parameter_value().double_value
        refine_edges = self.get_parameter('refine_edges').get_parameter_value().bool_value

        self._detector = AprilTagDetector(
            families=family,
            nthreads=nthreads,
            quad_decimate=quad_decimate,
            quad_sigma=quad_sigma,
            decode_sharpening=decode_sharpening,
            refine_edges=1 if refine_edges else 0,
        )
        self.get_logger().info(f'AprilTag detector initialized — family: {family}')

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

    def _on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self._process_frame(frame)

    def _timer_callback(self):
        if self.cap is None or not self.cap.isOpened():
            return
        ret, frame = self.cap.read()
        if not ret:
            return

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'camera'
        raw_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        raw_msg.header = header
        self._raw_pub.publish(raw_msg)

        self._process_frame(frame)

    def _process_frame(self, frame):
        if self._detector is None:
            return

        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        results = self._detector.detect(gray)

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'camera'

        array_msg = AprilTagArray()
        array_msg.header = header

        for r in results:
            cx = int(r.center[0])
            cy = int(r.center[1])

            corners_flat = []
            for corner in r.corners:
                corners_flat.extend([float(corner[0]), float(corner[1])])

            xs = [r.corners[i][0] for i in range(4)]
            ys = [r.corners[i][1] for i in range(4)]
            size_px = float(max(max(xs) - min(xs), max(ys) - min(ys)))

            tag_msg = AprilTagDetection()
            tag_msg.tag_id = int(r.tag_id)
            tag_msg.tag_family = r.tag_family.decode() if isinstance(r.tag_family, bytes) else str(r.tag_family)
            tag_msg.cx = cx
            tag_msg.cy = cy
            tag_msg.size_px = size_px
            tag_msg.decision_margin = float(r.decision_margin)
            tag_msg.hamming = int(r.hamming)
            tag_msg.corners = corners_flat
            tag_msg.frame_width = w
            tag_msg.frame_height = h
            array_msg.detections.append(tag_msg)

        self._detections_pub.publish(array_msg)

        if self.get_parameter('publish_debug_image').get_parameter_value().bool_value:
            debug = frame.copy()
            for r in results:
                pts = r.corners.astype(int)
                for i in range(4):
                    p1 = tuple(pts[i])
                    p2 = tuple(pts[(i + 1) % 4])
                    cv2.line(debug, p1, p2, COLOR_TAG, 2)
                cx = int(r.center[0])
                cy = int(r.center[1])
                cv2.circle(debug, (cx, cy), 5, COLOR_TAG, -1)
                cv2.putText(debug, f'ID:{r.tag_id}', (cx + 10, cy - 10),
                            FONT, 0.6, COLOR_ID, 2)
            debug_msg = self.bridge.cv2_to_imgmsg(debug, encoding='bgr8')
            debug_msg.header = header
            self._debug_pub.publish(debug_msg)

    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = AprilTagDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
