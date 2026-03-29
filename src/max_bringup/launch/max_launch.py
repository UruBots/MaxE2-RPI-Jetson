import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('max_bringup')

    platform_arg = DeclareLaunchArgument(
        'platform',
        default_value='rpi',
        description=(
            'Reservado (compatibilidad). No cambia el YAML: en Jetson usa '
            'config_file apuntando a config/max_params_jetson.yaml.'
        ),
    )

    config_file = LaunchConfiguration('config_file', default=os.path.join(
        pkg_dir, 'config', 'max_params.yaml'))

    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=os.path.join(pkg_dir, 'config', 'max_params.yaml'),
        description='Path to parameters YAML file'
    )

    detector_node = Node(
        package='max_vision',
        executable='detector_node',
        name='detector_node',
        parameters=[config_file],
        output='screen',
    )

    tracker_node = Node(
        package='max_control',
        executable='tracker_node',
        name='tracker_node',
        parameters=[config_file],
        output='screen',
    )

    dynamixel_node = Node(
        package='max_driver',
        executable='dynamixel_node',
        name='dynamixel_node',
        parameters=[config_file],
        output='screen',
    )

    debug_view_node = Node(
        package='max_vision',
        executable='debug_view_node',
        name='debug_view_node',
        parameters=[config_file],
        output='screen',
    )

    return LaunchDescription([
        platform_arg,
        config_file_arg,
        detector_node,
        tracker_node,
        dynamixel_node,
        debug_view_node,
    ])
