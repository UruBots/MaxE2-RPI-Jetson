import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String, UInt16

try:
    from dynamixel_sdk import COMM_SUCCESS, PacketHandler, PortHandler
except ImportError:
    COMM_SUCCESS = 0
    PacketHandler = None
    PortHandler = None


ADDR_REMOCON_TX_DATA = 59


class HeadOlloBridgeNode(Node):
    """Bridge ROS 2 head commands to a CM-550 remocon-style value."""

    def __init__(self):
        super().__init__('head_ollo_bridge_node')
        self._declare_parameters()
        self._port_handler = None
        self._packet_handler = None
        self._port_open = False
        self._last_value = None

        if PortHandler is None or PacketHandler is None:
            self.get_logger().error('dynamixel_sdk no instalado: pip install dynamixel-sdk')
        else:
            self._open_port()

        self._status_pub = self.create_publisher(UInt16, self._status_topic, 10)
        self.create_subscription(UInt16, self._raw_topic, self._on_raw_cmd, 10)
        self.create_subscription(Float32, self._angle_topic, self._on_angle_cmd, 10)
        self.create_subscription(String, self._preset_topic, self._on_preset_cmd, 10)

        self.get_logger().info(
            f'head_ollo_bridge_node listo: raw={self._raw_topic}, angle={self._angle_topic}, '
            f'preset={self._preset_topic}, controller_id={self._controller_id}'
        )

    def _declare_parameters(self):
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 57600)
        self.declare_parameter('protocol_version', 2.0)
        self.declare_parameter('controller_id', 200)
        self.declare_parameter('raw_topic', '/max/head_cmd_raw')
        self.declare_parameter('angle_topic', '/max/head_cmd')
        self.declare_parameter('preset_topic', '/max/head_preset')
        self.declare_parameter('status_topic', '/max/head_cmd_sent')
        self.declare_parameter('center_raw', 512)
        self.declare_parameter('min_raw', 0)
        self.declare_parameter('max_raw', 1023)
        self.declare_parameter('radians_per_range', math.pi)
        self.declare_parameter('preset_map', 'center:512,left:700,right:324')
        self.declare_parameter('resend_same_value', False)

        self._port = self.get_parameter('port').get_parameter_value().string_value
        self._baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        self._protocol_version = self.get_parameter('protocol_version').get_parameter_value().double_value
        self._controller_id = self.get_parameter('controller_id').get_parameter_value().integer_value
        self._raw_topic = self.get_parameter('raw_topic').get_parameter_value().string_value
        self._angle_topic = self.get_parameter('angle_topic').get_parameter_value().string_value
        self._preset_topic = self.get_parameter('preset_topic').get_parameter_value().string_value
        self._status_topic = self.get_parameter('status_topic').get_parameter_value().string_value
        self._center_raw = self.get_parameter('center_raw').get_parameter_value().integer_value
        self._min_raw = self.get_parameter('min_raw').get_parameter_value().integer_value
        self._max_raw = self.get_parameter('max_raw').get_parameter_value().integer_value
        self._radians_per_range = max(
            0.001, self.get_parameter('radians_per_range').get_parameter_value().double_value
        )
        self._preset_map_raw = self.get_parameter('preset_map').get_parameter_value().string_value
        self._resend_same_value = (
            self.get_parameter('resend_same_value').get_parameter_value().bool_value
        )
        self._preset_map = self._parse_preset_map(self._preset_map_raw)

    def _parse_preset_map(self, raw_map):
        mapping = {}
        for entry in raw_map.split(','):
            entry = entry.strip()
            if not entry or ':' not in entry:
                continue
            key, value = entry.split(':', 1)
            try:
                mapping[key.strip().lower()] = int(value.strip())
            except ValueError:
                self.get_logger().warn(f'preset_map invalido: {entry}')
        return mapping

    def _format_sdk_error(self, comm, err):
        parts = []
        if comm != COMM_SUCCESS:
            try:
                parts.append(self._packet_handler.getTxRxResult(comm))
            except Exception:
                parts.append(f'comm={comm}')
        if err != 0:
            try:
                parts.append(self._packet_handler.getRxPacketError(err))
            except Exception:
                parts.append(f'err={err}')
        return ', '.join(parts) if parts else 'ok'

    def _open_port(self):
        self._port_handler = PortHandler(self._port)
        self._packet_handler = PacketHandler(self._protocol_version)
        if not self._port_handler.openPort():
            self.get_logger().error(f'No se pudo abrir {self._port}')
            return
        if not self._port_handler.setBaudRate(self._baudrate):
            self.get_logger().error(f'No se pudo fijar baudrate {self._baudrate}')
            self._port_handler.closePort()
            return
        self._port_open = True

    def _clamp_raw(self, value):
        return max(self._min_raw, min(self._max_raw, int(value)))

    def _angle_to_raw(self, angle_rad):
        half_range = (self._max_raw - self._min_raw) / 2.0
        scaled = self._center_raw + (float(angle_rad) / self._radians_per_range) * half_range
        return self._clamp_raw(round(scaled))

    def _send_value(self, value, source):
        raw = self._clamp_raw(value)
        if not self._resend_same_value and raw == self._last_value:
            return
        if not self._port_open or self._packet_handler is None:
            self.get_logger().error('Puerto no abierto; no se puede enviar head command')
            return

        comm, err = self._packet_handler.write2ByteTxRx(
            self._port_handler, self._controller_id, ADDR_REMOCON_TX_DATA, raw
        )
        if comm != COMM_SUCCESS or err != 0:
            self.get_logger().error(
                f'Fallo al escribir head command {raw} desde {source}: '
                f'{self._format_sdk_error(comm, err)}'
            )
            return

        self._last_value = raw
        self._status_pub.publish(UInt16(data=raw))
        self.get_logger().info(f'Head command enviado: {raw} ({source})')

    def _on_raw_cmd(self, msg):
        self._send_value(msg.data, 'raw')

    def _on_angle_cmd(self, msg):
        self._send_value(self._angle_to_raw(msg.data), 'angle')

    def _on_preset_cmd(self, msg):
        key = msg.data.strip().lower()
        if not key:
            return
        if key not in self._preset_map:
            self.get_logger().warn(f'Preset desconocido: {key}')
            return
        self._send_value(self._preset_map[key], f'preset:{key}')

    def destroy_node(self):
        if self._port_open and self._port_handler is not None:
            self._port_handler.closePort()
            self._port_open = False
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HeadOlloBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
