"""Teleop por teclado hacia la CM-550 (discretiza /cmd_vel a remocon pages)."""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('max_bringup')

    config_file = LaunchConfiguration('config_file')
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=os.path.join(pkg_dir, 'config', 'cm550_motion_bridge_max_e2.yaml'),
        description='YAML para teleop CM-550 con keyboard → motions discretas',
    )

    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        parameters=[config_file],
        output='screen',
    )

    twist_mapper = Node(
        package='max_control',
        executable='twist_to_motion_node',
        name='twist_to_motion_node',
        parameters=[config_file, {'motion_topic': '/max/motion_cmd_teleop'}],
        output='screen',
    )

    motion_bridge = Node(
        package='max_driver',
        executable='cm550_remocon_bridge_node',
        name='cm550_remocon_bridge_node',
        parameters=[config_file],
        output='screen',
    )

    return LaunchDescription([
        config_file_arg,
        teleop,
        twist_mapper,
        motion_bridge,
    ])
