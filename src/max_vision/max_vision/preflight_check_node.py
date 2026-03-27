import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
import cv2

try:
    import serial
    from serial import SerialException
except ImportError:
    serial = None
    SerialException = Exception


class PreflightCheckNode(Node):
    """Checks camera availability and optional CM-550 serial port before bring-up."""

    def __init__(self):
        super().__init__('preflight_check_node')
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('gstreamer_pipeline', '')
        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('serial_baudrate', 57600)
        self.declare_parameter('check_serial', True)

        ok_camera = self._check_camera()
        ok_serial = self._check_serial()

        if ok_camera and ok_serial:
            self.get_logger().info('Preflight OK: camera y serial disponibles')
        else:
            self.get_logger().error('Preflight falló; revisa errores anteriores')

        # End process after logging once
        rclpy.shutdown()

    def _check_camera(self):
        gst = self.get_parameter('gstreamer_pipeline').get_parameter_value().string_value
        if gst:
            cap = cv2.VideoCapture(gst, cv2.CAP_GSTREAMER)
        else:
            idx = self.get_parameter('camera_index').get_parameter_value().integer_value
            cap = cv2.VideoCapture(idx)
        if not cap.isOpened():
            self.get_logger().error('Cámara: no se pudo abrir')
            return False
        w = self.get_parameter('frame_width').get_parameter_value().integer_value
        h = self.get_parameter('frame_height').get_parameter_value().integer_value
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        ret, _ = cap.read()
        cap.release()
        if not ret:
            self.get_logger().error('Cámara: no entrega frames')
            return False
        self.get_logger().info('Cámara OK')
        return True

    def _check_serial(self):
        if not self.get_parameter('check_serial').get_parameter_value().bool_value:
            return True
        if serial is None:
            self.get_logger().warning('Serial: pyserial no instalado, omitiendo chequeo')
            return True
        port = self.get_parameter('serial_port').get_parameter_value().string_value
        baud = self.get_parameter('serial_baudrate').get_parameter_value().integer_value
        try:
            ser = serial.Serial(port=port, baudrate=baud, timeout=0.1)
            ser.close()
            self.get_logger().info(f'Serial OK: {port} @ {baud}')
            return True
        except SerialException as exc:
            self.get_logger().error(f'Serial: no se pudo abrir {port} ({exc})')
            return False


def main(args=None):
    rclpy.init(args=args)
    PreflightCheckNode()
    rclpy.spin(rclpy.create_node('dummy_shutdown'))  # never reached

