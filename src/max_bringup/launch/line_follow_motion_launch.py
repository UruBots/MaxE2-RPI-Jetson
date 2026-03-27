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
        default_value=os.path.join(pkg_dir, 'config', 'max_params_motion.yaml'),
        description='Path to parameters YAML file',
    )

    line_detector = Node(
        package='max_vision',
        executable='line_detector_node',
        name='line_detector_node',
        parameters=[config_file],
        output='screen',
    )

    line_tracker = Node(
        package='max_control',
        executable='line_tracker_node',
        name='line_tracker_node',
        parameters=[config_file],
        output='screen',
    )

    motion_bridge = Node(
        package='max_driver',
        executable='cm550_remocon_bridge_node',
        name='cm550_remocon_bridge_node',
        parameters=[config_file],
        output='screen',
    )

    debug_view = Node(
        package='max_vision',
        executable='debug_view_node',
        name='debug_view_node',
        parameters=[config_file],
        output='screen',
    )

    return LaunchDescription([config_file_arg, line_detector, line_tracker, motion_bridge, debug_view])
