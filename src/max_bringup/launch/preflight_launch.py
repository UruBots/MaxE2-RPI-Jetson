"""Chequeo rápido de cámara y puerto serial antes del bring-up."""
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
        description='YAML con parámetros de cámara y serial para el preflight',
    )

    preflight = Node(
        package='max_vision',
        executable='preflight_check_node',
        name='preflight_check_node',
        parameters=[config_file],
        output='screen',
    )

    return LaunchDescription([
        config_file_arg,
        preflight,
    ])

