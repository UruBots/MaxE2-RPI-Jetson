from setuptools import find_packages, setup

package_name = 'max_driver'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'dynamixel_sdk', 'pyserial'],
    zip_safe=True,
    maintainer='sebastian',
    maintainer_email='sebastian@todo.com',
    description='Dynamixel servo driver for MAX robot',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'dynamixel_node = max_driver.dynamixel_node:main',
            'engineer_joint_node = max_driver.engineer_joint_node:main',
            'cm550_remocon_bridge_node = max_driver.cm550_remocon_bridge_node:main',
            'cm550_motion_bridge_node = max_driver.cm550_motion_bridge_node:main',
            'head_ollo_bridge_node = max_driver.head_ollo_bridge_node:main',
            'led_ollo_bridge_node = max_driver.led_ollo_bridge_node:main',
        ],
    },
)
