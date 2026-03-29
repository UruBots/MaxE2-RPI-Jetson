import math
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String, UInt16

try:
    import serial
    from serial import SerialException
except ImportError:
    serial = None
    SerialException = Exception


REMOCON_HEADER_0 = 0xFF
REMOCON_HEADER_1 = 0x55
MOTION_BASE = 10000
LED_OFF = 20000
LED_RED = 20001
LED_BLUE = 20002
LED_MAGENTA = 20003
HEAD_BASE = 30000
SPEED_BASE = 50000


class Cm550RemoconBridgeNode(Node):
    """Send RC-100 style remocon packets to the CM-550 over serial USB/UART."""

    def __init__(self):
        super().__init__('cm550_remocon_bridge_node')
        self._declare_parameters()
        self._serial = None
        self._command_map = self._parse_command_map(self._command_map_raw)
        self._command_sequences = self._parse_command_sequences(self._command_sequences_raw)
        self._preset_map = self._parse_preset_map(self._preset_map_raw)
        self._led_map = self._parse_preset_map(self._led_preset_map_raw)
        self._last_motion_command = None
        self._last_motion_page = None
        self._last_head_raw = None
        self._last_led_value = None
        self._active_sequence = []
        self._sequence_timer = None

        self._motion_status_pub = self.create_publisher(String, self._motion_status_topic, 10)
        self._motion_last_page_pub = self.create_publisher(UInt16, self._motion_last_page_topic, 10)
        self._head_status_pub = self.create_publisher(UInt16, self._head_status_topic, 10)
        self._led_status_pub = self.create_publisher(UInt16, self._led_status_topic, 10)

        self.create_subscription(String, self._motion_command_topic, self._on_motion_command, 10)
        self.create_subscription(UInt16, self._motion_page_topic, self._on_motion_page, 10)
        self.create_subscription(UInt16, self._head_raw_topic, self._on_head_raw, 10)
        self.create_subscription(Float32, self._head_angle_topic, self._on_head_angle, 10)
        self.create_subscription(String, self._head_preset_topic, self._on_head_preset, 10)
        self.create_subscription(String, self._led_preset_topic, self._on_led_preset, 10)
        self.create_subscription(UInt16, self._led_raw_topic, self._on_led_raw, 10)
        self.create_subscription(UInt16, self._speed_topic, self._on_speed_cmd, 10)

        self._open_serial()
        self.get_logger().info(
            f'cm550_remocon_bridge_node listo: port={self._port}, motion={self._motion_command_topic}, '
            f'head={self._head_raw_topic}, led={self._led_preset_topic}'
        )

    def _declare_parameters(self):
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 57600)
        self.declare_parameter('serial_timeout_sec', 0.05)
        self.declare_parameter('write_delay_sec', 0.02)
        # Permitir reenvío de la misma acción (p.ej. varios "walk" seguidos).
        self.declare_parameter('resend_same_motion_command', True)
        self.declare_parameter('resend_same_aux_command', False)

        self.declare_parameter('command_topic', '/max/motion_cmd')
        self.declare_parameter('page_topic', '/max/motion_page_cmd')
        self.declare_parameter('status_topic', '/max/motion_status')
        self.declare_parameter('last_page_topic', '/max/motion_last_page')
        self.declare_parameter('command_map', '')
        self.declare_parameter('command_sequences', '')
        self.declare_parameter('sequence_step_delay_sec', 0.6)
        self.declare_parameter('ignore_unknown_commands', True)
        self.declare_parameter('strip_action_metadata', True)
        # Repetición opcional de la marcha: walk -> start(101) + N veces go(103)
        self.declare_parameter('walk_repeat_count', 1)

        self.declare_parameter('head_raw_topic', '/max/head_cmd_raw')
        self.declare_parameter('head_angle_topic', '/max/head_cmd')
        self.declare_parameter('head_preset_topic', '/max/head_preset')
        self.declare_parameter('head_status_topic', '/max/head_cmd_sent')
        self.declare_parameter('center_raw', 512)
        self.declare_parameter('min_raw', 344)
        self.declare_parameter('max_raw', 680)
        self.declare_parameter('radians_per_range', math.pi / 2.0)
        self.declare_parameter('preset_map', 'center:512,left:680,right:344')

        self.declare_parameter('led_preset_topic', '/max/led_preset')
        self.declare_parameter('led_raw_topic', '/max/led_cmd_raw')
        self.declare_parameter('led_status_topic', '/max/led_cmd_sent')
        self.declare_parameter('led_preset_map', 'off:20000,red:20001,blue:20002,magenta:20003')
        self.declare_parameter('speed_topic', '/max/profile_velocity')
        self.declare_parameter('profile_velocity_max_limit', 300)

        self._port = self.get_parameter('port').get_parameter_value().string_value
        self._baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        self._serial_timeout_sec = self.get_parameter(
            'serial_timeout_sec'
        ).get_parameter_value().double_value
        self._write_delay_sec = max(
            0.0, self.get_parameter('write_delay_sec').get_parameter_value().double_value
        )
        self._resend_same_motion_command = (
            self.get_parameter('resend_same_motion_command').get_parameter_value().bool_value
        )
        self._resend_same_aux_command = (
            self.get_parameter('resend_same_aux_command').get_parameter_value().bool_value
        )

        self._motion_command_topic = self.get_parameter('command_topic').get_parameter_value().string_value
        self._motion_page_topic = self.get_parameter('page_topic').get_parameter_value().string_value
        self._motion_status_topic = self.get_parameter('status_topic').get_parameter_value().string_value
        self._motion_last_page_topic = self.get_parameter(
            'last_page_topic'
        ).get_parameter_value().string_value
        self._command_map_raw = self.get_parameter('command_map').get_parameter_value().string_value
        self._command_sequences_raw = (
            self.get_parameter('command_sequences').get_parameter_value().string_value
        )
        self._sequence_step_delay_sec = max(
            0.01, self.get_parameter('sequence_step_delay_sec').get_parameter_value().double_value
        )
        self._ignore_unknown = (
            self.get_parameter('ignore_unknown_commands').get_parameter_value().bool_value
        )
        self._strip_action_metadata = (
            self.get_parameter('strip_action_metadata').get_parameter_value().bool_value
        )
        self._walk_repeat_count = max(
            1, self.get_parameter('walk_repeat_count').get_parameter_value().integer_value
        )

        self._head_raw_topic = self.get_parameter('head_raw_topic').get_parameter_value().string_value
        self._head_angle_topic = self.get_parameter('head_angle_topic').get_parameter_value().string_value
        self._head_preset_topic = self.get_parameter(
            'head_preset_topic'
        ).get_parameter_value().string_value
        self._head_status_topic = self.get_parameter(
            'head_status_topic'
        ).get_parameter_value().string_value
        self._center_raw = self.get_parameter('center_raw').get_parameter_value().integer_value
        self._min_raw = self.get_parameter('min_raw').get_parameter_value().integer_value
        self._max_raw = self.get_parameter('max_raw').get_parameter_value().integer_value
        self._radians_per_range = max(
            0.001, self.get_parameter('radians_per_range').get_parameter_value().double_value
        )
        self._preset_map_raw = self.get_parameter('preset_map').get_parameter_value().string_value

        self._led_preset_topic = self.get_parameter(
            'led_preset_topic'
        ).get_parameter_value().string_value
        self._led_raw_topic = self.get_parameter('led_raw_topic').get_parameter_value().string_value
        self._led_status_topic = self.get_parameter(
            'led_status_topic'
        ).get_parameter_value().string_value
        self._led_preset_map_raw = self.get_parameter(
            'led_preset_map'
        ).get_parameter_value().string_value
        self._speed_topic = self.get_parameter('speed_topic').get_parameter_value().string_value
        self._profile_velocity_max_limit = max(
            0,
            self.get_parameter('profile_velocity_max_limit').get_parameter_value().integer_value,
        )

    def _open_serial(self):
        if serial is None:
            self.get_logger().error('pyserial no instalado: pip install pyserial')
            return
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=self._serial_timeout_sec,
                write_timeout=self._serial_timeout_sec,
                rtscts=False,
                dsrdtr=False,
            )
            self._serial.setDTR(False)
            self._serial.setRTS(False)
        except SerialException as exc:
            self.get_logger().error(f'No se pudo abrir puerto serial {self._port}: {exc}')
            self._serial = None

    def _parse_command_map(self, raw_map):
        mapping = {}
        for entry in raw_map.split(','):
            entry = entry.strip()
            if not entry or ':' not in entry:
                continue
            command, page = entry.split(':', 1)
            try:
                mapping[command.strip().lower()] = int(page.strip())
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
                sequences[command.strip().lower()] = pages
        return sequences

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
                self.get_logger().warn(f'mapa invalido: {entry}')
        return mapping

    def _normalize_command(self, raw_command):
        command = raw_command.strip().lower()
        if self._strip_action_metadata and '[' in command:
            command = command.split('[', 1)[0].strip()
        return command

    def _encode_remocon_packet(self, value):
        value = int(max(0, min(65535, value)))
        low = value & 0xFF
        high = (value >> 8) & 0xFF
        return bytes([
            REMOCON_HEADER_0,
            REMOCON_HEADER_1,
            low,
            (~low) & 0xFF,
            high,
            (~high) & 0xFF,
        ])

    def _send_value(self, value, source):
        if self._serial is None:
            self.get_logger().error(f'Puerto serial no disponible; no se puede enviar {source}')
            return False
        packet = self._encode_remocon_packet(value)
        try:
            self._serial.write(packet)
            self._serial.flush()
            if self._write_delay_sec > 0.0:
                time.sleep(self._write_delay_sec)
        except SerialException as exc:
            self.get_logger().error(f'Fallo serial enviando {source}={value}: {exc}')
            return False

        self.get_logger().info(
            f'Remocon enviado: value={value} source={source} packet={packet.hex(" ")}'
        )
        return True

    def _cancel_sequence(self):
        self._active_sequence = []
        if self._sequence_timer is not None:
            self._sequence_timer.cancel()
            self.destroy_timer(self._sequence_timer)
            self._sequence_timer = None

    def _write_motion_page(self, page, source):
        encoded = MOTION_BASE + int(page)
        if not self._send_value(encoded, source):
            return False
        self._last_motion_page = int(page)
        self._motion_status_pub.publish(String(data=f'{source}:{page}'))
        self._motion_last_page_pub.publish(UInt16(data=int(page)))
        return True

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
        self._sequence_timer = self.create_timer(self._sequence_step_delay_sec, self._on_sequence_timer)
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

    def _clamp_head_raw(self, value):
        return max(self._min_raw, min(self._max_raw, int(value)))

    def _angle_to_raw(self, angle_rad):
        half_range = (self._max_raw - self._min_raw) / 2.0
        scaled = self._center_raw + (float(angle_rad) / self._radians_per_range) * half_range
        return self._clamp_head_raw(round(scaled))

    def _publish_head_status(self, raw):
        self._head_status_pub.publish(UInt16(data=int(raw)))

    def _publish_led_status(self, raw):
        self._led_status_pub.publish(UInt16(data=int(raw)))

    def _on_motion_command(self, msg):
        command = self._normalize_command(msg.data)
        if not command:
            return
        if not self._resend_same_motion_command and command == self._last_motion_command:
            return
        # Manejo especial: repetir walk N veces con start+go
        if command == 'walk' and self._walk_repeat_count > 1:
            pages = [101] + [103] * self._walk_repeat_count
            if self._start_sequence('walk', pages):
                self._last_motion_command = command
            return
        if command in self._command_sequences:
            if self._start_sequence(command, self._command_sequences[command]):
                self._last_motion_command = command
            return
        if command not in self._command_map:
            if self._ignore_unknown:
                self.get_logger().warning(f'Comando sin mapa (ignorado): {command}')
                return
            self.get_logger().warn(f'Comando sin mapa: {command}')
            return
        page = self._command_map[command]
        self._cancel_sequence()
        if self._write_motion_page(page, command):
            self._last_motion_command = command

    def _on_motion_page(self, msg):
        page = int(msg.data)
        if not self._resend_same_motion_command and page == self._last_motion_page:
            return
        self._cancel_sequence()
        if self._write_motion_page(page, 'direct_page'):
            self._last_motion_command = None

    def _send_head_raw(self, raw, source):
        raw = self._clamp_head_raw(raw)
        if not self._resend_same_aux_command and raw == self._last_head_raw:
            return
        encoded = HEAD_BASE + raw
        if self._send_value(encoded, source):
            self._last_head_raw = raw
            self._publish_head_status(raw)

    def _on_head_raw(self, msg):
        self._send_head_raw(msg.data, 'head_raw')

    def _on_head_angle(self, msg):
        self._send_head_raw(self._angle_to_raw(msg.data), 'head_angle')

    def _on_head_preset(self, msg):
        key = msg.data.strip().lower()
        if not key:
            return
        if key not in self._preset_map:
            self.get_logger().warn(f'Preset cabeza desconocido: {key}')
            return
        self._send_head_raw(self._preset_map[key], f'head_preset:{key}')

    def _send_led_value(self, value, source):
        raw = int(value)
        if not self._resend_same_aux_command and raw == self._last_led_value:
            return
        if self._send_value(raw, source):
            self._last_led_value = raw
            self._publish_led_status(raw)

    def _on_led_preset(self, msg):
        key = msg.data.strip().lower()
        if not key:
            return
        if key not in self._led_map:
            self.get_logger().warn(f'Preset LED desconocido: {key}')
            return
        self._send_led_value(self._led_map[key], f'led_preset:{key}')

    def _on_led_raw(self, msg):
        self._send_led_value(msg.data, 'led_raw')

    def _on_speed_cmd(self, msg):
        limit = self._profile_velocity_max_limit if self._profile_velocity_max_limit > 0 else (65535 - SPEED_BASE)
        raw = int(max(0, min(limit, msg.data)))
        encoded = SPEED_BASE + raw
        self._send_value(encoded, 'speed_cmd')

    def destroy_node(self):
        self._cancel_sequence()
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Cm550RemoconBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
