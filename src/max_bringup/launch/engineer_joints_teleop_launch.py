"""engineer_joint_node + joint_teleop_node (teclado → JointState).

joint_teleop_node necesita TTY en stdin para el teclado; con ``ros2 launch`` usa
``teleop_prefix:='xterm -hold -e '`` si no recibes teclas (el nodo sigue vivo pero
stdin no es TTY).
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

    engineer = Node(
        package='max_driver',
        executable='engineer_joint_node',
        name='engineer_joint_node',
        parameters=[config_path],
        output='screen',
    )

    teleop_kwargs = dict(
        package='max_control',
        executable='joint_teleop_node',
        name='joint_teleop_node',
        parameters=[config_path],
        output='screen',
    )
    if prefix:
        teleop_kwargs['prefix'] = prefix
    teleop = Node(**teleop_kwargs)

    return [engineer, teleop]


def generate_launch_description():
    pkg_dir = get_package_share_directory('max_bringup')

    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=os.path.join(pkg_dir, 'config', 'engineer_max_e2.yaml'),
        description='YAML con engineer_joint_node y joint_teleop_node',
    )

    teleop_prefix_arg = DeclareLaunchArgument(
        'teleop_prefix',
        default_value='',
        description='Prefijo TTY solo para joint_teleop_node, p. ej. "xterm -hold -e "',
    )

    return LaunchDescription([
        config_file_arg,
        teleop_prefix_arg,
        OpaqueFunction(function=_launch_setup),
    ])
