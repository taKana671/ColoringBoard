from panda3d.core import Vec3


class Bounds:

    def __init__(self, vertices):
        """vertices: list of Vec3
        """
        self.top_right = self.get_top_right(vertices)
        self.bottom_left = self.get_bottom_left(vertices)
        self.height = self.top_right.z - self.bottom_left.z
        self.width = self.top_right.x - self.bottom_left.x
        self.center = self.get_center(vertices)
        self.radius = max(rad for rad in self.get_radius(vertices))

    def get_top_right(self, vertices):
        x = max(vertices, key=lambda vertex: vertex.x).x
        y = min(vertices, key=lambda vertex: vertex.y).y
        z = max(vertices, key=lambda vertex: vertex.z).z

        return Vec3(x, y, z)

    def get_bottom_left(self, vertices):
        x = min(vertices, key=lambda vertex: vertex.x).x
        y = max(vertices, key=lambda vertex: vertex.y).y
        z = min(vertices, key=lambda vertex: vertex.z).z

        return Vec3(x, y, z)

    def get_center(self, vertices):
        cnt = len(vertices)
        x = sum(vertex.x for vertex in vertices) / cnt
        y = sum(vertex.y for vertex in vertices) / cnt
        z = sum(vertex.z for vertex in vertices) / cnt

        return Vec3(x, y, z)

    def get_radius(self, vertices):
        for vertex in vertices:
            x = vertex.x - self.center.x
            y = vertex.y - self.center.y
            z = vertex.z - self.center.z
            radius = (x ** 2 + y ** 2 + z ** 2) ** 0.5
            yield radius