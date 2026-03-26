import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt16

try:
    from dynamixel_sdk import COMM_SUCCESS, PacketHandler, PortHandler
except ImportError:
    COMM_SUCCESS = 0
    PacketHandler = None
    PortHandler = None


ADDR_MOTION_PLAY_SPEED = 64
ADDR_MOTION_INDEX_NUMBER = 66


class Cm550MotionBridgeNode(Node):
    """Bridge high-level ROS 2 commands to CM-550 motion pages."""

    def __init__(self):
        super().__init__('cm550_motion_bridge_node')
        self._declare_parameters()
        self._port_handler = None
        self._packet_handler = None
        self._port_open = False
        self._last_command = None
        self._last_page = None
        self._command_map = self._parse_command_map(self._command_map_raw)
        self._command_sequences = self._parse_command_sequences(self._command_sequences_raw)
        self._active_sequence = []
        self._sequence_timer = None

        if PortHandler is None or PacketHandler is None:
            self.get_logger().error('dynamixel_sdk no instalado: pip install dynamixel-sdk')
        else:
            self._open_port()

        self._motion_status_pub = self.create_publisher(String, self._status_topic, 10)
        self._last_page_pub = self.create_publisher(UInt16, self._last_page_topic, 10)

        self.create_subscription(String, self._command_topic, self._on_motion_command, 10)
        self.create_subscription(UInt16, self._page_topic, self._on_motion_page, 10)

        self.get_logger().info(
            f'cm550_motion_bridge_node listo: cmd={self._command_topic}, '
            f'page={self._page_topic}, controller_id={self._controller_id}'
        )

    def _declare_parameters(self):
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 57600)
        self.declare_parameter('protocol_version', 2.0)
        self.declare_parameter('controller_id', 200)
        self.declare_parameter('motion_speed', 100)
        self.declare_parameter('command_topic', '/max/motion_cmd')
        self.declare_parameter('page_topic', '/max/motion_page_cmd')
        self.declare_parameter('status_topic', '/max/motion_status')
        self.declare_parameter('last_page_topic', '/max/motion_last_page')
        self.declare_parameter('command_map', '')
        self.declare_parameter('command_sequences', '')
        self.declare_parameter('sequence_step_delay_sec', 0.6)
        self.declare_parameter('ignore_unknown_commands', True)
        self.declare_parameter('strip_action_metadata', True)
        self.declare_parameter('resend_same_command', False)

        self._port = self.get_parameter('port').get_parameter_value().string_value
        self._baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        self._protocol_version = self.get_parameter('protocol_version').get_parameter_value().double_value
        self._controller_id = self.get_parameter('controller_id').get_parameter_value().integer_value
        self._motion_speed = self.get_parameter('motion_speed').get_parameter_value().integer_value
        self._command_topic = self.get_parameter('command_topic').get_parameter_value().string_value
        self._page_topic = self.get_parameter('page_topic').get_parameter_value().string_value
        self._status_topic = self.get_parameter('status_topic').get_parameter_value().string_value
        self._last_page_topic = self.get_parameter('last_page_topic').get_parameter_value().string_value
        self._command_map_raw = self.get_parameter('command_map').get_parameter_value().string_value
        self._command_sequences_raw = (
            self.get_parameter('command_sequences').get_parameter_value().string_value
        )
        self._sequence_step_delay_sec = max(
            0.0, self.get_parameter('sequence_step_delay_sec').get_parameter_value().double_value
        )
        self._ignore_unknown = (
            self.get_parameter('ignore_unknown_commands').get_parameter_value().bool_value
        )
        self._strip_action_metadata = (
            self.get_parameter('strip_action_metadata').get_parameter_value().bool_value
        )
        self._resend_same_command = (
            self.get_parameter('resend_same_command').get_parameter_value().bool_value
        )

    def _parse_command_map(self, raw_map):
        mapping = {}
        for entry in raw_map.split(','):
            entry = entry.strip()
            if not entry or ':' not in entry:
                continue
            command, page = entry.split(':', 1)
            command = command.strip().lower()
            try:
                mapping[command] = int(page.strip())
            except ValueError:
                self.get_logger().warn(f'command_map invalido: {entry}')
        return mapping

    def _parse_command_sequences(self, raw_sequences):
        sequences = {}
        for entry in raw_sequences.split(','):
            entry = entry.strip()
            if not entry or ':' not in entry:
                continue
            command, raw_pages = entry.split(':', 1)
            command = command.strip().lower()
            pages = []
            for token in raw_pages.split('|'):
                token = token.strip()
                if not token:
                    continue
                try:
                    pages.append(int(token))
                except ValueError:
                    self.get_logger().warn(f'command_sequences invalido: {entry}')
                    pages = []
                    break
            if pages:
                sequences[command] = pages
        return sequences

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
        if 20 <= self._motion_speed <= 200:
            comm, err = self._packet_handler.write1ByteTxRx(
                self._port_handler, self._controller_id, ADDR_MOTION_PLAY_SPEED, self._motion_speed
            )
            if comm != COMM_SUCCESS or err != 0:
                self.get_logger().warn(
                    'No se pudo fijar Motion Play Speed: '
                    f'{self._format_sdk_error(comm, err)}'
                )

    def _normalize_command(self, raw_command):
        command = raw_command.strip().lower()
        if self._strip_action_metadata and '[' in command:
            command = command.split('[', 1)[0].strip()
        return command

    def _write_motion_page(self, page, source_label):
        if not self._port_open or self._packet_handler is None:
            self.get_logger().error('Puerto no abierto; no se puede enviar motion')
            return False
        if not 0 <= page <= 65535:
            self.get_logger().error(f'Pagina fuera de rango: {page}')
            return False

        comm, err = self._packet_handler.write2ByteTxRx(
            self._port_handler, self._controller_id, ADDR_MOTION_INDEX_NUMBER, page
        )
        if comm != COMM_SUCCESS or err != 0:
            self.get_logger().error(
                f'Fallo al escribir motion page {page} desde {source_label}: '
                f'{self._format_sdk_error(comm, err)}'
            )
            return False

        self._last_page = page
        status_msg = String()
        status_msg.data = f'{source_label}:{page}'
        self._motion_status_pub.publish(status_msg)
        self._last_page_pub.publish(UInt16(data=page))
        self.get_logger().info(f'Motion page enviada: {page} ({source_label})')
        return True

    def _cancel_sequence(self):
        self._active_sequence = []
        if self._sequence_timer is not None:
            self._sequence_timer.cancel()
            self.destroy_timer(self._sequence_timer)
            self._sequence_timer = None

    def _start_sequence(self, command, pages):
        self._cancel_sequence()
        if not pages:
            return False

        if not self._write_motion_page(pages[0], f'{command}[1/{len(pages)}]'):
            return False

        remaining = list(pages[1:])
        if not remaining:
            return True

        self._active_sequence = [(command, idx + 2, len(pages), page) for idx, page in enumerate(remaining)]
        self._sequence_timer = self.create_timer(
            max(0.01, self._sequence_step_delay_sec), self._on_sequence_timer
        )
        return True

    def _on_sequence_timer(self):
        if not self._active_sequence:
            self._cancel_sequence()
            return

        command, step_idx, total_steps, page = self._active_sequence.pop(0)
        if not self._write_motion_page(page, f'{command}[{step_idx}/{total_steps}]'):
            self._cancel_sequence()
            return

        if not self._active_sequence:
            self._cancel_sequence()

    def _on_motion_command(self, msg):
        command = self._normalize_command(msg.data)
        if not command:
            return
        if not self._resend_same_command and command == self._last_command:
            return

        if command in self._command_sequences:
            if self._start_sequence(command, self._command_sequences[command]):
                self._last_command = command
            return

        if command not in self._command_map:
            if self._ignore_unknown:
                self.get_logger().debug(f'Ignorando comando sin mapa: {command}')
                self._last_command = command
                return
            self.get_logger().warn(f'Comando sin mapa: {command}')
            return

        page = self._command_map[command]
        if self._write_motion_page(page, command):
            self._last_command = command

    def _on_motion_page(self, msg):
        page = int(msg.data)
        if not self._resend_same_command and self._last_page == page:
            return
        self._cancel_sequence()
        if self._write_motion_page(page, 'direct_page'):
            self._last_command = None

    def destroy_node(self):
        self._cancel_sequence()
        if self._port_open and self._port_handler is not None:
            self._port_handler.closePort()
            self._port_open = False
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Cm550MotionBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
