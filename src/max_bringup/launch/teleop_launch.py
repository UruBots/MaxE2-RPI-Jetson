"""Teleoperación por teclado: publica /cmd_vel hacia dynamixel_node.

No lances este archivo junto con tracker_node, line_tracker_node ni action_executor_node:
todos publican en /cmd_vel y se pisarían los comandos.

teleop_twist_keyboard requiere TTY en stdin; con ``ros2 launch`` suele fallar sin
``teleop_prefix:='xterm -hold -e '`` (ver teleop_cm550_launch.py).
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

    dynamixel = Node(
        package='max_driver',
        executable='dynamixel_node',
        name='dynamixel_node',
        parameters=[config_path],
        output='screen',
    )

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

    return [dynamixel, teleop]


def generate_launch_description():
    pkg_dir = get_package_share_directory('max_bringup')

    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=os.path.join(pkg_dir, 'config', 'max_params.yaml'),
        description='Path to parameters YAML file',
    )

    teleop_prefix_arg = DeclareLaunchArgument(
        'teleop_prefix',
        default_value='',
        description=(
            'Prefijo TTY para teleop_twist_keyboard, p. ej. "xterm -hold -e " '
            '(espacio final). Vacío si stdin ya es terminal.'
        ),
    )

    return LaunchDescription([
        config_file_arg,
        teleop_prefix_arg,
        OpaqueFunction(function=_launch_setup),
    ])
