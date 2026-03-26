from setuptools import find_packages, setup

package_name = 'max_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sebastian',
    maintainer_email='sebastian@todo.com',
    description='Object tracking controller for MAX robot',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'tracker_node = max_control.tracker_node:main',
            'line_tracker_node = max_control.line_tracker_node:main',
            'action_executor_node = max_control.action_executor_node:main',
            'joint_teleop_node = max_control.joint_teleop_node:main',
            'apriltag_head_search_node = max_control.apriltag_head_search_node:main',
        ],
    },
)
