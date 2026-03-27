from setuptools import find_packages, setup

package_name = 'max_vision'

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
    description='Camera capture and object detection for MAX robot',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'detector_node = max_vision.detector_node:main',
            'line_detector_node = max_vision.line_detector_node:main',
            'shape_detector_node = max_vision.shape_detector_node:main',
            'apriltag_detector_node = max_vision.apriltag_detector_node:main',
            'debug_view_node = max_vision.debug_view_node:main',
            'hsv_calibrator = max_vision.hsv_calibrator:main',
            'preflight_check_node = max_vision.preflight_check_node:main',
        ],
    },
)
