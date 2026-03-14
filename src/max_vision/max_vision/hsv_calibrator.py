import cv2
import rclpy
from rclpy.node import Node


class HSVCalibrator(Node):
    """Standalone ROS2 node with OpenCV trackbars for HSV range calibration."""

    def __init__(self):
        super().__init__('hsv_calibrator')
        self.declare_parameter('camera_index', 0)
        self.camera_index = self.get_parameter('camera_index').get_parameter_value().integer_value
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            self.get_logger().error('Failed to open camera')
            return

        self.lh, self.ls, self.lv = 0, 120, 70
        self.uh, self.us, self.uv = 10, 255, 255

        cv2.namedWindow('HSV Calibrator')
        cv2.createTrackbar('L-H', 'HSV Calibrator', self.lh, 179, self._on_lh)
        cv2.createTrackbar('L-S', 'HSV Calibrator', self.ls, 255, self._on_ls)
        cv2.createTrackbar('L-V', 'HSV Calibrator', self.lv, 255, self._on_lv)
        cv2.createTrackbar('U-H', 'HSV Calibrator', self.uh, 179, self._on_uh)
        cv2.createTrackbar('U-S', 'HSV Calibrator', self.us, 255, self._on_us)
        cv2.createTrackbar('U-V', 'HSV Calibrator', self.uv, 255, self._on_uv)

    def _on_lh(self, v):
        self.lh = v

    def _on_ls(self, v):
        self.ls = v

    def _on_lv(self, v):
        self.lv = v

    def _on_uh(self, v):
        self.uh = v

    def _on_us(self, v):
        self.us = v

    def _on_uv(self, v):
        self.uv = v

    def run(self):
        while rclpy.ok():
            ret, frame = self.cap.read()
            if not ret:
                break

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower = (self.lh, self.ls, self.lv)
            upper = (self.uh, self.us, self.uv)
            mask = cv2.inRange(hsv, lower, upper)
            result = cv2.bitwise_and(frame, frame, mask=mask)

            cv2.imshow('Frame', frame)
            cv2.imshow('Mask', mask)
            cv2.imshow('Result', result)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.get_logger().info(
            f'HSV calibration: lower_h={self.lh}, lower_s={self.ls}, lower_v={self.lv}, '
            f'upper_h={self.uh}, upper_s={self.us}, upper_v={self.uv}'
        )
        self.cap.release()
        cv2.destroyAllWindows()


def main(args=None):
    rclpy.init(args=args)
    node = HSVCalibrator()
    if node.cap is not None and node.cap.isOpened():
        node.run()
    node.destroy_node()
    rclpy.shutdown()
