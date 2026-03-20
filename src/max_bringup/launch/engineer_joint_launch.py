"""Control articulaciones Engineer / MAX-E2 (CM-550 + XL430) vía JointState."""
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
        default_value=os.path.join(pkg_dir, 'config', 'engineer_max_e2.yaml'),
        description='YAML con engineer_joint_node (joint_ids / joint_names)',
    )

    joint_node = Node(
        package='max_driver',
        executable='engineer_joint_node',
        name='engineer_joint_node',
        parameters=[config_file],
        output='screen',
    )

    return LaunchDescription([config_file_arg, joint_node])
