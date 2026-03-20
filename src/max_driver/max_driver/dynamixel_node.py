import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Header
from max_interfaces.msg import DynamixelStateArray, DynamixelState
from max_interfaces.srv import SetTorque, SetOperatingMode

try:
    from dynamixel_sdk import *
except ImportError:
    PortHandler = None
    PacketHandler = None
    COMM_SUCCESS = 0


ADDR_OPERATING_MODE = 11
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_VELOCITY = 104
ADDR_PRESENT_POSITION = 132
ADDR_PRESENT_VELOCITY = 128
ADDR_PRESENT_TEMPERATURE = 146

MODE_VELOCITY = 1

class DynamixelNode(Node):
    """ROS2 node for Dynamixel servo control via CM-550."""

    def __init__(self):
        super().__init__('dynamixel_node')
        self._declare_parameters()
        self._port_handler = None
        self._packet_handler = None
        self._port_open = False

        if PortHandler is not None and PacketHandler is not None:
            self._init_dynamixel()
        else:
            self.get_logger().warn(
                'dynamixel_sdk not available; running without hardware'
            )

        self._cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self._cmd_vel_callback, 10
        )
        self._state_pub = self.create_publisher(
            DynamixelStateArray, '/max/dynamixel_states', 10
        )
        rate = max(0.1, self._state_publish_rate)
        self._state_timer = self.create_timer(1.0 / rate, self._state_timer_callback)
        self._set_torque_srv = self.create_service(
            SetTorque, '/max/set_torque', self._set_torque_callback
        )
        self._set_operating_mode_srv = self.create_service(
            SetOperatingMode, '/max/set_operating_mode',
            self._set_operating_mode_callback
        )

    def _declare_parameters(self):
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 1000000)
        self.declare_parameter('protocol_version', 2.0)
        self.declare_parameter('left_wheel_id', 1)
        self.declare_parameter('right_wheel_id', 2)
        self.declare_parameter('wheel_separation', 0.16)
        self.declare_parameter('max_velocity', 200)
        self.declare_parameter('state_publish_rate', 10.0)
        self.declare_parameter('invert_left', False)
        self.declare_parameter('invert_right', True)
        self.declare_parameter('set_velocity_mode_on_start', True)

        self._port = self.get_parameter('port').get_parameter_value().string_value
        self._baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        self._protocol_version = self.get_parameter('protocol_version').get_parameter_value().double_value
        self._left_wheel_id = self.get_parameter('left_wheel_id').get_parameter_value().integer_value
        self._right_wheel_id = self.get_parameter('right_wheel_id').get_parameter_value().integer_value
        self._wheel_separation = self.get_parameter('wheel_separation').get_parameter_value().double_value
        self._max_velocity = self.get_parameter('max_velocity').get_parameter_value().integer_value
        self._state_publish_rate = self.get_parameter('state_publish_rate').get_parameter_value().double_value
        self._invert_left = self.get_parameter('invert_left').get_parameter_value().bool_value
        self._invert_right = self.get_parameter('invert_right').get_parameter_value().bool_value
        self._set_velocity_mode = self.get_parameter(
            'set_velocity_mode_on_start'
        ).get_parameter_value().bool_value

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

    def _write1_checked(self, motor_id, address, value, action):
        comm, err = self._packet_handler.write1ByteTxRx(
            self._port_handler, motor_id, address, value
        )
        if comm != COMM_SUCCESS or err != 0:
            self.get_logger().error(
                f'id={motor_id} {action} fallo en addr {address}: {self._format_sdk_error(comm, err)}'
            )
            return False
        return True

    def _init_dynamixel(self):
        self._port_handler = PortHandler(self._port)
        self._packet_handler = PacketHandler(self._protocol_version)

        if not self._port_handler.openPort():
            self.get_logger().error(f'Failed to open port {self._port}')
            return

        if not self._port_handler.setBaudRate(self._baudrate):
            self.get_logger().error(f'Failed to set baudrate {self._baudrate}')
            self._port_handler.closePort()
            return

        self._port_open = True

        configured = 0
        for motor_id in [self._left_wheel_id, self._right_wheel_id]:
            ok = True
            if self._set_velocity_mode:
                ok &= self._write1_checked(
                    motor_id, ADDR_TORQUE_ENABLE, 0, 'deshabilitar torque antes de velocity mode'
                )
                ok &= self._write1_checked(
                    motor_id, ADDR_OPERATING_MODE, MODE_VELOCITY, 'configurar velocity mode'
                )
            ok &= self._write1_checked(motor_id, ADDR_TORQUE_ENABLE, 1, 'habilitar torque')
            if ok:
                configured += 1

        if configured == 0:
            self.get_logger().error(
                'No se pudo configurar ningun motor. Verifica CM-550 en Manage mode, '
                'Bypass Port=USB, baudrate e IDs.'
            )
            self._port_handler.closePort()
            self._port_open = False
        elif configured != 2:
            self.get_logger().warn(f'Solo se configuraron {configured}/2 motores')

    def _cmd_vel_callback(self, msg):
        if not self._port_open or self._packet_handler is None:
            return

        linear_x = msg.linear.x
        angular_z = msg.angular.z

        left_vel = linear_x - angular_z * self._wheel_separation / 2.0
        right_vel = linear_x + angular_z * self._wheel_separation / 2.0

        left_dxl = int(left_vel * self._max_velocity)
        right_dxl = int(right_vel * self._max_velocity)

        if self._invert_left:
            left_dxl = -left_dxl
        if self._invert_right:
            right_dxl = -right_dxl

        left_dxl = max(-self._max_velocity, min(self._max_velocity, left_dxl))
        right_dxl = max(-self._max_velocity, min(self._max_velocity, right_dxl))

        try:
            self._packet_handler.write4ByteTxRx(
                self._port_handler, self._left_wheel_id,
                ADDR_GOAL_VELOCITY, left_dxl & 0xFFFFFFFF
            )
            self._packet_handler.write4ByteTxRx(
                self._port_handler, self._right_wheel_id,
                ADDR_GOAL_VELOCITY, right_dxl & 0xFFFFFFFF
            )
        except Exception as e:
            self.get_logger().warn(f'Failed to write velocity: {e}')

    def _state_timer_callback(self):
        if not self._port_open or self._packet_handler is None:
            return

        states = []
        try:
            for motor_id in [self._left_wheel_id, self._right_wheel_id]:
                pos, _, _ = self._packet_handler.read4ByteTxRx(
                    self._port_handler, motor_id, ADDR_PRESENT_POSITION
                )
                vel, _, _ = self._packet_handler.read4ByteTxRx(
                    self._port_handler, motor_id, ADDR_PRESENT_VELOCITY
                )
                temp, _, _ = self._packet_handler.read2ByteTxRx(
                    self._port_handler, motor_id, ADDR_PRESENT_TEMPERATURE
                )
                if vel > 0x7FFFFFFF:
                    vel_signed = vel - 0x100000000
                else:
                    vel_signed = vel
                states.append(DynamixelState(
                    id=motor_id,
                    present_position=pos,
                    present_velocity=vel_signed,
                    present_temperature=temp
                ))
        except Exception as e:
            self.get_logger().warn(f'Failed to read state: {e}')
            return

        msg = DynamixelStateArray()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = ''
        msg.states = states
        self._state_pub.publish(msg)

    def _set_torque_callback(self, request, response):
        if not self._port_open or self._packet_handler is None:
            response.success = False
            response.message = 'Port not open or SDK not available'
            return response

        enable = 1 if request.enable else 0
        dxl_comm_result, dxl_error = self._packet_handler.write1ByteTxRx(
            self._port_handler, request.id, ADDR_TORQUE_ENABLE, enable
        )
        if dxl_comm_result == COMM_SUCCESS and dxl_error == 0:
            response.success = True
            response.message = ''
        else:
            response.success = False
            response.message = f'Write failed: comm={dxl_comm_result} err={dxl_error}'
        return response

    def _set_operating_mode_callback(self, request, response):
        if not self._port_open or self._packet_handler is None:
            response.success = False
            response.message = 'Port not open or SDK not available'
            return response

        self._packet_handler.write1ByteTxRx(
            self._port_handler, request.id, ADDR_TORQUE_ENABLE, 0
        )
        dxl_comm_result, dxl_error = self._packet_handler.write1ByteTxRx(
            self._port_handler, request.id, ADDR_OPERATING_MODE, request.mode
        )
        if dxl_comm_result == COMM_SUCCESS and dxl_error == 0:
            response.success = True
            response.message = ''
        else:
            response.success = False
            response.message = f'Write failed: comm={dxl_comm_result} err={dxl_error}'
        return response

    def destroy_node(self):
        if self._port_open and self._packet_handler is not None:
            for motor_id in [self._left_wheel_id, self._right_wheel_id]:
                try:
                    self._packet_handler.write1ByteTxRx(
                        self._port_handler, motor_id, ADDR_TORQUE_ENABLE, 0
                    )
                except Exception:
                    pass
            self._port_handler.closePort()
            self._port_open = False
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DynamixelNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
