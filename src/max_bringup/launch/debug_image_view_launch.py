"""Abre visores image_view para los tópicos debug de visión (línea, objeto/color, AprilTag)."""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    line_view = Node(
        package='image_view',
        executable='image_view',
        name='line_debug_view',
        remappings=[('image', '/max/line_debug_image')],
        output='screen',
    )

    obj_view = Node(
        package='image_view',
        executable='image_view',
        name='object_debug_view',
        remappings=[('image', '/max/shape_debug_image')],
        output='screen',
    )

    color_view = Node(
        package='image_view',
        executable='image_view',
        name='color_debug_view',
        remappings=[('image', '/max/debug_image')],
        output='screen',
    )

    tag_view = Node(
        package='image_view',
        executable='image_view',
        name='apriltag_debug_view',
        remappings=[('image', '/max/apriltag_debug_image')],
        output='screen',
    )

    return LaunchDescription([line_view, obj_view, color_view, tag_view])

