"""Bridge ROS 2 LED commands to the CM-550 auxiliary LED path."""
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
        default_value=os.path.join(pkg_dir, 'config', 'led_ollo_bridge.yaml'),
        description='YAML para cm550_remocon_bridge_node',
    )

    node = Node(
        package='max_driver',
        executable='cm550_remocon_bridge_node',
        name='cm550_remocon_bridge_node',
        parameters=[config_file],
        output='screen',
    )

    return LaunchDescription([config_file_arg, node])
