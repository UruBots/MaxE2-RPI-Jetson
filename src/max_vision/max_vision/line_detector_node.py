import math
import numpy as np
import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from cv_bridge import CvBridge
from max_interfaces.msg import LineDetection


class LineDetectorNode(Node):
    """Detects lines in the lower portion of the camera frame for line following."""

    def __init__(self):
        super().__init__('line_detector_node')

        self.declare_parameter('camera_index', 0)
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('fps', 30.0)
        self.declare_parameter('gstreamer_pipeline', '')
        self.declare_parameter('publish_debug_image', True)
        self.declare_parameter('use_camera_topic', False)

        self.declare_parameter('roi_height_ratio', 0.35)
        self.declare_parameter('threshold_mode', 'adaptive')
        self.declare_parameter('binary_threshold', 60)
        self.declare_parameter('adaptive_block_size', 25)
        self.declare_parameter('adaptive_c', 8)
        self.declare_parameter('invert_binary', True)
        self.declare_parameter('blur_kernel', 5)
        self.declare_parameter('morph_kernel', 5)
        self.declare_parameter('min_line_area', 200)
        self.declare_parameter('use_hsv', False)
        self.declare_parameter('line_lower_h', 0)
        self.declare_parameter('line_lower_s', 0)
        self.declare_parameter('line_lower_v', 0)
        self.declare_parameter('line_upper_h', 180)
        self.declare_parameter('line_upper_s', 50)
        self.declare_parameter('line_upper_v', 80)

        self.bridge = CvBridge()
        self.cap = None

        use_topic = self.get_parameter('use_camera_topic').get_parameter_value().bool_value
        if use_topic:
            self.image_sub = self.create_subscription(
                Image, '/max/camera/image_raw', self._image_callback, 10
            )
        else:
            self._init_camera()

        self.line_pub = self.create_publisher(LineDetection, '/max/line_detection', 10)
        self.debug_pub = self.create_publisher(Image, '/max/line_debug_image', 10)

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

    def _create_mask(self, roi):
        use_hsv = self.get_parameter('use_hsv').get_parameter_value().bool_value
        blur_k = self.get_parameter('blur_kernel').get_parameter_value().integer_value
        blur_k = blur_k if blur_k % 2 == 1 else blur_k + 1

        blurred = cv2.GaussianBlur(roi, (blur_k, blur_k), 0)

        if use_hsv:
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
            lower = np.array([
                self.get_parameter('line_lower_h').get_parameter_value().integer_value,
                self.get_parameter('line_lower_s').get_parameter_value().integer_value,
                self.get_parameter('line_lower_v').get_parameter_value().integer_value,
            ])
            upper = np.array([
                self.get_parameter('line_upper_h').get_parameter_value().integer_value,
                self.get_parameter('line_upper_s').get_parameter_value().integer_value,
                self.get_parameter('line_upper_v').get_parameter_value().integer_value,
            ])
            mask = cv2.inRange(hsv, lower, upper)
        else:
            gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
            mode = self.get_parameter('threshold_mode').get_parameter_value().string_value

            if mode == 'adaptive':
                block = self.get_parameter('adaptive_block_size').get_parameter_value().integer_value
                block = block if block % 2 == 1 else block + 1
                c = self.get_parameter('adaptive_c').get_parameter_value().integer_value
                mask = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY_INV, block, c
                )
            else:
                thresh = self.get_parameter('binary_threshold').get_parameter_value().integer_value
                invert = self.get_parameter('invert_binary').get_parameter_value().bool_value
                flag = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
                _, mask = cv2.threshold(gray, thresh, 255, flag)

        morph_k = self.get_parameter('morph_kernel').get_parameter_value().integer_value
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_k, morph_k))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        return mask

    def _process_frame(self, frame):
        fh, fw = frame.shape[:2]
        roi_ratio = self.get_parameter('roi_height_ratio').get_parameter_value().double_value
        min_area = self.get_parameter('min_line_area').get_parameter_value().integer_value

        roi_y = int(fh * (1.0 - roi_ratio))
        roi = frame[roi_y:fh, :]

        mask = self._create_mask(roi)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid = [c for c in contours if cv2.contourArea(c) >= min_area]

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'camera'

        msg = LineDetection()
        msg.header = header
        msg.frame_width = fw
        msg.frame_height = fh
        msg.roi_y_start = roi_y

        if valid:
            largest = max(valid, key=cv2.contourArea)
            M = cv2.moments(largest)
            if M['m00'] > 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                msg.detected = True
                msg.cx = cx
                msg.cy = cy + roi_y
                msg.offset_x = (cx - fw / 2.0) / (fw / 2.0)

                if len(largest) >= 5:
                    (_, _), (_, _), angle = cv2.fitEllipse(largest)
                    msg.angle = float(angle - 90.0)
                else:
                    _, _, w_rect, h_rect, angle = cv2.minAreaRect(largest)
                    msg.angle = float(angle) if w_rect < h_rect else float(angle - 90.0)

                x, y, bw, bh = cv2.boundingRect(largest)
                msg.line_width = bw
            else:
                msg.detected = False
        else:
            msg.detected = False

        self.line_pub.publish(msg)

        if self.get_parameter('publish_debug_image').get_parameter_value().bool_value:
            debug = frame.copy()
            cv2.line(debug, (0, roi_y), (fw, roi_y), (255, 255, 0), 1)
            cv2.line(debug, (fw // 2, roi_y), (fw // 2, fh), (128, 128, 128), 1)

            if msg.detected:
                cv2.circle(debug, (msg.cx, msg.cy), 8, (0, 0, 255), -1)
                cv2.putText(
                    debug, f'off:{msg.offset_x:.2f} ang:{msg.angle:.1f}',
                    (10, roi_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2
                )
                roi_debug = debug[roi_y:fh, :]
                mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
                mask_color[:, :, 0] = 0
                mask_color[:, :, 2] = 0
                cv2.addWeighted(roi_debug, 1.0, mask_color, 0.4, 0, roi_debug)

            debug_msg = self.bridge.cv2_to_imgmsg(debug, encoding='bgr8')
            debug_msg.header = header
            self.debug_pub.publish(debug_msg)

    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = LineDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
