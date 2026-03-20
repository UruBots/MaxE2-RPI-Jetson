"""Teleoperación por teclado: publica /cmd_vel hacia dynamixel_node.

No lances este archivo junto con tracker_node, line_tracker_node ni action_executor_node:
todos publican en /cmd_vel y se pisarían los comandos.
"""
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
        default_value=os.path.join(pkg_dir, 'config', 'max_params.yaml'),
        description='Path to parameters YAML file',
    )

    dynamixel = Node(
        package='max_driver',
        executable='dynamixel_node',
        name='dynamixel_node',
        parameters=[config_file],
        output='screen',
    )

    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        parameters=[config_file],
        output='screen',
    )

    return LaunchDescription([
        config_file_arg,
        dynamixel,
        teleop,
    ])
