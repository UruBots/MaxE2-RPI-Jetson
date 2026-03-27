"""Scan with the head until an AprilTag is detected, then center head and body."""
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
        default_value=os.path.join(pkg_dir, 'config', 'apriltag_head_search.yaml'),
        description='YAML para barrido de cabeza y recentrado con AprilTag',
    )

    apriltag_detector = Node(
        package='max_vision',
        executable='apriltag_detector_node',
        name='apriltag_detector_node',
        parameters=[config_file],
        output='screen',
    )

    motion_bridge = Node(
        package='max_driver',
        executable='cm550_motion_bridge_node',
        name='cm550_motion_bridge_node',
        parameters=[config_file],
        output='screen',
    )

    head_bridge = Node(
        package='max_driver',
        executable='head_ollo_bridge_node',
        name='head_ollo_bridge_node',
        parameters=[config_file],
        output='screen',
    )

    led_bridge = Node(
        package='max_driver',
        executable='led_ollo_bridge_node',
        name='led_ollo_bridge_node',
        parameters=[config_file],
        output='screen',
    )

    controller = Node(
        package='max_control',
        executable='apriltag_head_search_node',
        name='apriltag_head_search_node',
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

    return LaunchDescription([
        config_file_arg,
        apriltag_detector,
        motion_bridge,
        head_bridge,
        led_bridge,
        controller,
        debug_view,
    ])
