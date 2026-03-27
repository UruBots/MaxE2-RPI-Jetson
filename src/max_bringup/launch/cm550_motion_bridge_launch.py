"""Bridge ROS 2 high-level commands to CM-550 motion pages."""
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
        description='YAML para cm550_motion_bridge_node',
    )

    motion_bridge = Node(
        package='max_driver',
        executable='cm550_remocon_bridge_node',
        name='cm550_remocon_bridge_node',
        parameters=[config_file],
        output='screen',
    )

    return LaunchDescription([config_file_arg, motion_bridge])
