"""
Control multi-articular ROS2 para humanoides ROBOTIS Engineer (p. ej. MAX-E2) vía CM-550.

- Comando: sensor_msgs/JointState en /max/joint_command (position = objetivo)
- Estado: sensor_msgs/JointState en /joint_states

Las posiciones pueden estar en radianes (recomendado) o en ticks Dynamixel (0–4095).
Ajusta joint_ids y joint_names con Dynamixel Wizard 2.0 según tu montaje.
"""
import math
import threading

import rclpy
from rcl_interfaces.msg import ParameterDescriptor, ParameterType
from rclpy.exceptions import ParameterUninitializedException
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header

from max_interfaces.srv import SetOperatingMode, SetTorque

try:
    from dynamixel_sdk import PortHandler, PacketHandler
except ImportError:
    PortHandler = None
    PacketHandler = None

COMM_SUCCESS = 0

ADDR_OPERATING_MODE = 11
ADDR_TORQUE_ENABLE = 64
ADDR_PROFILE_VELOCITY = 112
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132
ADDR_PRESENT_VELOCITY = 128

MODE_POSITION = 3
DEFAULT_TICKS_PER_REV = 4096


class EngineerJointNode(Node):
    def _get_bool_array(self, name: str):
        try:
            return list(self.get_parameter(name).get_parameter_value().bool_array_value)
        except ParameterUninitializedException:
            return []

    def _get_double_array(self, name: str):
        try:
            return list(self.get_parameter(name).get_parameter_value().double_array_value)
        except ParameterUninitializedException:
            return []

    def __init__(self):
        super().__init__('engineer_joint_node')
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 1000000)
        self.declare_parameter('protocol_version', 2.0)
        self.declare_parameter('state_publish_rate', 30.0)
        self.declare_parameter(
            'joint_ids',
            [1, 2, 3, 4, 5, 6, 7, 8],
            ParameterDescriptor(type=ParameterType.PARAMETER_INTEGER_ARRAY),
        )
        self.declare_parameter(
            'joint_names',
            [
                'joint_1', 'joint_2', 'joint_3', 'joint_4',
                'joint_5', 'joint_6', 'joint_7', 'joint_8',
            ],
            ParameterDescriptor(type=ParameterType.PARAMETER_STRING_ARRAY),
        )
        # YAML con joint_invert: [] / joint_offset_rad: [] a veces deja el override sin tipo válido
        # y declare falla al fusionar → ParameterUninitializedException. ignore_override evita eso.
        self.declare_parameter(
            'joint_invert',
            [],
            ParameterDescriptor(type=ParameterType.PARAMETER_BOOL_ARRAY),
            ignore_override=True,
        )
        self.declare_parameter(
            'joint_offset_rad',
            [],
            ParameterDescriptor(type=ParameterType.PARAMETER_DOUBLE_ARRAY),
            ignore_override=True,
        )
        self.declare_parameter('positions_in_radians', True)
        self.declare_parameter('ticks_per_revolution', DEFAULT_TICKS_PER_REV)
        self.declare_parameter('command_topic', '/max/joint_command')
        self.declare_parameter('auto_enable_torque', True)
        self.declare_parameter('set_position_mode_on_start', True)
        self.declare_parameter('profile_velocity', 0)
        self.declare_parameter('disable_torque_on_shutdown', True)

        self._port = self.get_parameter('port').get_parameter_value().string_value
        self._baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        self._protocol_version = self.get_parameter('protocol_version').get_parameter_value().double_value
        self._state_publish_rate = max(
            1.0, self.get_parameter('state_publish_rate').get_parameter_value().double_value
        )
        self._joint_ids = list(
            self.get_parameter('joint_ids').get_parameter_value().integer_array_value
        )
        self._joint_names = list(
            self.get_parameter('joint_names').get_parameter_value().string_array_value
        )
        inv = self._get_bool_array('joint_invert')
        off = self._get_double_array('joint_offset_rad')
        self._joint_invert = self._pad_bool_list(inv, len(self._joint_ids), False)
        self._joint_offset_rad = self._pad_float_list(off, len(self._joint_ids), 0.0)
        self._positions_in_radians = (
            self.get_parameter('positions_in_radians').get_parameter_value().bool_value
        )
        self._ticks_per_rev = max(
            1, self.get_parameter('ticks_per_revolution').get_parameter_value().integer_value
        )
        self._command_topic = self.get_parameter('command_topic').get_parameter_value().string_value
        self._auto_torque = self.get_parameter('auto_enable_torque').get_parameter_value().bool_value
        self._set_pos_mode = (
            self.get_parameter('set_position_mode_on_start').get_parameter_value().bool_value
        )
        self._profile_velocity = self.get_parameter('profile_velocity').get_parameter_value().integer_value
        self._disable_on_shutdown = (
            self.get_parameter('disable_torque_on_shutdown').get_parameter_value().bool_value
        )

        if len(self._joint_ids) != len(self._joint_names):
            self.get_logger().fatal(
                f'joint_ids ({len(self._joint_ids)}) y joint_names ({len(self._joint_names)}) '
                'deben tener la misma longitud'
            )
            raise ValueError('joint_ids / joint_names mismatch')

        self._name_to_id = {n: i for n, i in zip(self._joint_names, self._joint_ids)}
        self._lock = threading.Lock()
        self._port_handler = None
        self._packet_handler = None
        self._port_open = False

        if PortHandler is None or PacketHandler is None:
            self.get_logger().error('dynamixel_sdk no instalado: pip install dynamixel-sdk')
        else:
            self._open_and_configure()

        self.create_subscription(
            JointState, self._command_topic, self._on_joint_command, 10
        )
        self._joint_state_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.create_timer(1.0 / self._state_publish_rate, self._publish_states)

        # Nombres distintos de dynamixel_node por si ambos coexisten en pruebas
        self.create_service(SetTorque, '/max/engineer/set_torque', self._srv_set_torque)
        self.create_service(
            SetOperatingMode, '/max/engineer/set_operating_mode',
            self._srv_set_operating_mode,
        )

        self.get_logger().info(
            f'engineer_joint_node: {len(self._joint_ids)} articulaciones, '
            f'comando={self._command_topic}, estado=/joint_states'
        )

    @staticmethod
    def _pad_bool_list(lst, n, default):
        out = list(lst[:n])
        while len(out) < n:
            out.append(default)
        return out

    @staticmethod
    def _pad_float_list(lst, n, default):
        out = list(lst[:n])
        while len(out) < n:
            out.append(default)
        return out

    def _open_and_configure(self):
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

        with self._lock:
            for jid in self._joint_ids:
                if self._set_pos_mode:
                    self._packet_handler.write1ByteTxRx(
                        self._port_handler, jid, ADDR_TORQUE_ENABLE, 0
                    )
                    self._packet_handler.write1ByteTxRx(
                        self._port_handler, jid, ADDR_OPERATING_MODE, MODE_POSITION
                    )
                if self._auto_torque:
                    self._packet_handler.write1ByteTxRx(
                        self._port_handler, jid, ADDR_TORQUE_ENABLE, 1
                    )
                if self._profile_velocity > 0:
                    self._packet_handler.write4ByteTxRx(
                        self._port_handler, jid, ADDR_PROFILE_VELOCITY,
                        self._profile_velocity & 0xFFFFFFFF
                    )

    def _rad_to_raw(self, joint_idx, rad):
        r = rad + self._joint_offset_rad[joint_idx]
        if self._joint_invert[joint_idx]:
            r = -r
        raw = int(round((r / (2.0 * math.pi)) * float(self._ticks_per_rev)))
        raw = max(0, min(self._ticks_per_rev - 1, raw))
        return raw

    def _raw_to_rad(self, joint_idx, raw):
        rad = (float(raw) / float(self._ticks_per_rev)) * (2.0 * math.pi)
        if self._joint_invert[joint_idx]:
            rad = -rad
        rad -= self._joint_offset_rad[joint_idx]
        return rad

    def _on_joint_command(self, msg: JointState):
        if not self._port_open or self._packet_handler is None:
            return
        if not msg.name or not msg.position:
            return

        with self._lock:
            for name, pos in zip(msg.name, msg.position):
                if name not in self._name_to_id:
                    continue
                jid = self._name_to_id[name]
                idx = self._joint_ids.index(jid)
                if self._positions_in_radians:
                    raw = self._rad_to_raw(idx, float(pos))
                else:
                    raw = int(round(float(pos)))
                    raw = max(0, min(self._ticks_per_rev - 1, raw))
                self._packet_handler.write4ByteTxRx(
                    self._port_handler, jid, ADDR_GOAL_POSITION, raw & 0xFFFFFFFF
                )

    def _publish_states(self):
        if not self._port_open or self._packet_handler is None:
            return

        names = []
        positions = []
        velocities = []

        with self._lock:
            for idx, jid in enumerate(self._joint_ids):
                try:
                    pos, comm, err = self._packet_handler.read4ByteTxRx(
                        self._port_handler, jid, ADDR_PRESENT_POSITION
                    )
                    if comm != COMM_SUCCESS:
                        self.get_logger().warn(
                            f'Lectura posición id={jid} comm={comm} err={err}'
                        )
                        continue
                    vel, _, _ = self._packet_handler.read4ByteTxRx(
                        self._port_handler, jid, ADDR_PRESENT_VELOCITY
                    )
                    if vel > 0x7FFFFFFF:
                        vel = vel - 0x100000000
                except Exception as e:
                    self.get_logger().warn(f'Lectura id={jid}: {e}')
                    continue

                names.append(self._joint_names[idx])
                if self._positions_in_radians:
                    positions.append(self._raw_to_rad(idx, pos))
                else:
                    positions.append(float(pos))
                if self._positions_in_radians:
                    velocities.append(
                        (float(vel) / float(self._ticks_per_rev)) * (2.0 * math.pi)
                    )
                else:
                    velocities.append(float(vel))

        if not names:
            return

        out = JointState()
        out.header = Header()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = 'base_link'
        out.name = names
        out.position = positions
        out.velocity = velocities
        out.effort = []
        self._joint_state_pub.publish(out)

    def _srv_set_torque(self, request, response):
        if not self._port_open or self._packet_handler is None:
            response.success = False
            response.message = 'Puerto no abierto'
            return response
        en = 1 if request.enable else 0
        with self._lock:
            comm, err = self._packet_handler.write1ByteTxRx(
                self._port_handler, request.id, ADDR_TORQUE_ENABLE, en
            )
        response.success = comm == COMM_SUCCESS and err == 0
        response.message = '' if response.success else f'comm={comm} err={err}'
        return response

    def _srv_set_operating_mode(self, request, response):
        if not self._port_open or self._packet_handler is None:
            response.success = False
            response.message = 'Puerto no abierto'
            return response
        with self._lock:
            self._packet_handler.write1ByteTxRx(
                self._port_handler, request.id, ADDR_TORQUE_ENABLE, 0
            )
            comm, err = self._packet_handler.write1ByteTxRx(
                self._port_handler, request.id, ADDR_OPERATING_MODE, request.mode
            )
        response.success = comm == COMM_SUCCESS and err == 0
        response.message = '' if response.success else f'comm={comm} err={err}'
        return response

    def destroy_node(self):
        if self._disable_on_shutdown and self._port_open and self._packet_handler is not None:
            with self._lock:
                for jid in self._joint_ids:
                    try:
                        self._packet_handler.write1ByteTxRx(
                            self._port_handler, jid, ADDR_TORQUE_ENABLE, 0
                        )
                    except Exception:
                        pass
            self._port_handler.closePort()
            self._port_open = False
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = EngineerJointNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
