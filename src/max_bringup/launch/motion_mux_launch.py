"""Selecciona la fuente de /max/motion_cmd (teleop/tracker/apriltag/line)."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    active = LaunchConfiguration('active_source')
    active_arg = DeclareLaunchArgument(
        'active_source',
        default_value='teleop',
        description='Fuente activa: teleop | tracker | apriltag | line',
    )

    mux = Node(
        package='max_control',
        executable='motion_mux_node',
        name='motion_mux_node',
        parameters=[{'active_source': active}],
        output='screen',
    )

    return LaunchDescription([active_arg, mux])

