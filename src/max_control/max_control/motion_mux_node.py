import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MotionMuxNode(Node):
    """MUX simple: reemite /max/motion_cmd_<source> según source_param hacia /max/motion_cmd."""

    def __init__(self):
        super().__init__('motion_mux_node')
        self.declare_parameter('sources', ['teleop', 'tracker', 'apriltag', 'line'])
        self.declare_parameter('active_source', 'teleop')
        self.declare_parameter('output_topic', '/max/motion_cmd')

        self.output_topic = self.get_parameter('output_topic').get_parameter_value().string_value
        self.sources = [
            s.strip() for s in self.get_parameter('sources').get_parameter_value().string_array_value
        ]
        self.active_source = (
            self.get_parameter('active_source').get_parameter_value().string_value.strip()
        )

        self.pub = self.create_publisher(String, self.output_topic, 10)
        self.subs = {}
        for src in self.sources:
            topic = f'/max/motion_cmd_{src}'
            self.subs[src] = self.create_subscription(
                String, topic, lambda msg, src=src: self._on_motion(msg, src), 10
            )
        self.get_logger().info(
            f'motion_mux_node listo: output={self.output_topic} active={self.active_source} sources={self.sources}'
        )

    def _on_motion(self, msg: String, src: str):
        if src != self.active_source:
            return
        self.pub.publish(msg)

    def set_parameters(self, parameters):
        result = super().set_parameters(parameters)
        for p in parameters:
            if p.name == 'active_source' and p.type_ == p.Type.STRING:
                new_src = p.value.strip()
                if new_src in self.sources:
                    self.active_source = new_src
                    self.get_logger().info(f'Fuente activa ahora: {self.active_source}')
                else:
                    self.get_logger().warn(f'Fuente desconocida: {new_src} (sources={self.sources})')
        return result


def main(args=None):
    rclpy.init(args=args)
    node = MotionMuxNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

