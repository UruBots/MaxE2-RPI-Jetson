"""Teleop por teclado hacia la CM-550 (discretiza /cmd_vel a remocon pages).

teleop_twist_keyboard necesita un TTY en stdin. Los procesos hijos de ``ros2 launch``
a menudo no lo tienen (termios: Inappropriate ioctl for device). Solución: lanzar
con ``teleop_prefix`` apuntando a un terminal real, p. ej. ``xterm -hold -e ``.
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _launch_setup(context, *args, **kwargs):
    config_path = context.launch_configurations['config_file']
    prefix = context.launch_configurations.get('teleop_prefix', '').strip()

    teleop_kwargs = dict(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        parameters=[config_path],
        output='screen',
    )
    if prefix:
        teleop_kwargs['prefix'] = prefix

    teleop = Node(**teleop_kwargs)

    twist_mapper = Node(
        package='max_control',
        executable='twist_to_motion_node',
        name='twist_to_motion_node',
        parameters=[config_path, {'motion_topic': '/max/motion_cmd_teleop'}],
        output='screen',
    )

    motion_bridge = Node(
        package='max_driver',
        executable='cm550_remocon_bridge_node',
        name='cm550_remocon_bridge_node',
        parameters=[config_path],
        output='screen',
    )

    return [teleop, twist_mapper, motion_bridge]


def generate_launch_description():
    pkg_dir = get_package_share_directory('max_bringup')

    config_file = LaunchConfiguration('config_file')
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=os.path.join(pkg_dir, 'config', 'cm550_motion_bridge_max_e2.yaml'),
        description='YAML para teleop CM-550 con keyboard → motions discretas',
    )

    teleop_prefix_arg = DeclareLaunchArgument(
        'teleop_prefix',
        default_value='',
        description=(
            'Prefijo para ejecutar teleop_twist_keyboard con TTY real. '
            'Ej.: "xterm -hold -e " (nota el espacio final). '
            'Vacío: el nodo usa el mismo stdin que launch (falla si no es TTY).'
        ),
    )

    return LaunchDescription([
        config_file_arg,
        teleop_prefix_arg,
        OpaqueFunction(function=_launch_setup),
    ])
