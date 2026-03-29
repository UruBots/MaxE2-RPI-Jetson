"""Teleop por teclado hacia la CM-550 (discretiza /cmd_vel a remocon pages).

teleop_twist_keyboard necesita un TTY en stdin. Los procesos hijos de ``ros2 launch``
a menudo no lo tienen (termios: Inappropriate ioctl for device). Opciones:

- ``teleop_prefix`` con terminal gráfico (``xterm``, ``gnome-terminal``) — requiere
  ``DISPLAY`` (escritorio local o ``ssh -X``).
- Por **SSH sin X11**: ``include_teleop:=false`` y en **otra** sesión ``ssh -t`` ejecuta
  solo ``ros2 run teleop_twist_keyboard ...`` (así hay TTY real).
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node


def _truthy(value: str) -> bool:
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _launch_setup(context, *args, **kwargs):
    config_path = context.launch_configurations['config_file']
    prefix = context.launch_configurations.get('teleop_prefix', '').strip()
    include_teleop = _truthy(context.launch_configurations.get('include_teleop', 'true'))

    teleop_kwargs = dict(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        parameters=[config_path],
        output='screen',
    )
    if prefix:
        teleop_kwargs['prefix'] = prefix

    teleop = Node(**teleop_kwargs)

    # motion_topic desde YAML (p. ej. /max/motion_cmd). No usar /max/motion_cmd_teleop
    # aquí sin motion_mux_node: el puente solo escucha command_topic (/max/motion_cmd).
    twist_mapper = Node(
        package='max_control',
        executable='twist_to_motion_node',
        name='twist_to_motion_node',
        parameters=[config_path],
        output='screen',
    )

    motion_bridge = Node(
        package='max_driver',
        executable='cm550_remocon_bridge_node',
        name='cm550_remocon_bridge_node',
        parameters=[config_path],
        output='screen',
    )

    if include_teleop:
        return [teleop, twist_mapper, motion_bridge]
    return [twist_mapper, motion_bridge]


def generate_launch_description():
    pkg_dir = get_package_share_directory('max_bringup')

    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=os.path.join(pkg_dir, 'config', 'cm550_motion_bridge_max_e2.yaml'),
        description='YAML para teleop CM-550 con keyboard → motions discretas',
    )

    teleop_prefix_arg = DeclareLaunchArgument(
        'teleop_prefix',
        default_value='',
        description=(
            'Prefijo para ejecutar teleop_twist_keyboard con TTY real. '
            'Ej.: "xterm -hold -e " (requiere: sudo apt install xterm; espacio final). '
            'En Ubuntu Desktop sin xterm: "gnome-terminal -- ". '
            'xterm/gnome-terminal necesitan DISPLAY (no usar por SSH sin ssh -X). '
            'Vacío: mismo stdin que launch (falla termios si no es TTY).'
        ),
    )

    include_teleop_arg = DeclareLaunchArgument(
        'include_teleop',
        default_value='true',
        description=(
            'Si false, no arranca teleop_twist_keyboard (útil por SSH sin X11): '
            'lanzar el teleop en otra terminal con ssh -t y el mismo params-file.'
        ),
    )

    return LaunchDescription([
        config_file_arg,
        teleop_prefix_arg,
        include_teleop_arg,
        OpaqueFunction(function=_launch_setup),
    ])
