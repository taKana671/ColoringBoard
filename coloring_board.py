import random
from enum import Enum, auto
from textwrap import wrap

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import WindowProperties, PandaNode, NodePath
from panda3d.core import Vec3, LColor, Point3, Vec2
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexReader, GeomVertexWriter
from panda3d.core import GeomNode
from panda3d.core import BitMask32
from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletConvexHullShape

from db_manage import get_vertices, get_faces
from tkwindow import WindowTk


class Colors(Enum):

    RED = LColor(1, 0, 0, 1)
    BLUE = LColor(0, 0, 1, 1)
    YELLOW = LColor(1, 1, 0, 1)
    GREEN = LColor(0, 0.5, 0, 1)
    ORANGE = LColor(1, 0.549, 0, 1)
    MAGENTA = LColor(1, 0, 1, 1)
    PURPLE = LColor(0.501, 0, 0.501, 1)
    LIME = LColor(0, 1, 0, 1)
    VIOLET = LColor(0.54, 0.16, 0.88, 1)
    SKY = LColor(0, 0.74, 1, 1)

    @classmethod
    def select(cls, n):
        return random.sample([m.value for m in cls], n)


class Mouse(Enum):

    CLICK = auto()
    RELEASE = auto()
    DRAG = auto()


class ColoringBoard(ShowBase):

    def __init__(self):
        super().__init__(windowType='none')
        self.startTk()
        root = self.tkRoot
        root.geometry('1080x640')
        root.resizable(False, False)

        self.app = WindowTk(root, self)
        root.bind('<Escape>', self.app.close)

        props = WindowProperties()
        props.setParentWindow(root.winfo_id())
        props.setOrigin(260, 20)
        props.setSize(800, 600)
        # props.setSize(self.frame.winfo_width(), self.frame.winfo_height())
        self.makeDefaultPipe()
        self.openMainWindow(type='onscreen', props=props, size=(800, 600))

        self.disableMouse()
        self.camera_np = NodePath(PandaNode('cameraNode'))
        self.camera_np.reparentTo(self.render)
        self.camera.reparentTo(self.camera_np)
        self.camera.setPos(15, 0, 0)
        self.camera.lookAt(0, 0, 0)

        self.world = BulletWorld()

        self.debug = self.render.attachNewNode(BulletDebugNode('debug'))
        self.world.setDebugNode(self.debug.node())

        self.polh = Polyhedron(self.world)
        self.show_coloring_pic(self.app.combobox.get())
        self.toggle_debug()

        self.dragging = 0
        self.clicked_pos = None
        self.state = None

        self.accept('mouse1', self.click)
        self.accept('mouse1-up', self.release)
        self.taskMgr.add(self.update, 'update')

    def click(self):
        self.state = Mouse.CLICK

    def release(self):
        self.state = Mouse.RELEASE

    def make_file(self, filepath):
        geom_node = self.polh.connect_geoms()
        np = NodePath(PandaNode(filepath.stem))
        obj = np.attachNewNode(geom_node)
        obj.setTwoSided(True)
        np.writeBamFile(filepath.name)

    def change_color(self, m_pos):
        near_pos = Point3()
        far_pos = Point3()
        self.camLens.extrude(m_pos, near_pos, far_pos)
        from_pos = self.render.getRelativePoint(self.cam, near_pos)
        to_pos = self.render.getRelativePoint(self.cam, far_pos)
        result = self.world.rayTestClosest(from_pos, to_pos)

        if result.hasHit():
            node = result.getNode()
            if hexa_color := self.app.selected_color():
                rgb = [int(n, 16) / 255 for n in wrap(hexa_color[1:], 2)]
                color = LColor(*rgb, 1)
                self.polh.change_face_color(node.getName(), color)

    def show_coloring_pic(self, name):
        self.polh.clear()
        vertices = get_vertices(name)
        faces = get_faces(name)

        li = [len(item) for item in faces]
        dic = {item: i for i, item in enumerate(set(li))}
        color_pattern = [dic[item] for item in li]
        self.polh.make_faces(vertices, faces, color_pattern)

    def toggle_debug(self, outline=1):
        if outline:
            self.debug.show()
        else:
            self.debug.hide()

    def rotate(self, dt, m_pos):
        vec = Vec3()
        delta_x = m_pos.x - self.clicked_pos.x
        delta_y = m_pos.y - self.clicked_pos.y

        if delta_x < 0:
            vec.x -= 90
        elif delta_x > 0:
            vec.x += 90

        if delta_y < 0:
            vec.z -= 90
        elif delta_y > 0:
            vec.z += 90

        self.camera_np.setHpr(self.camera_np.getHpr() + vec * dt)
        self.clicked_pos.x = m_pos.x
        self.clicked_pos.y = m_pos.y

    def update(self, task):
        dt = globalClock.getDt()

        if self.mouseWatcherNode.hasMouse():
            m_pos = self.mouseWatcherNode.getMouse()

            match self.state:
                case Mouse.CLICK:
                    self.dragging = globalClock.getFrameCount() + 7
                    self.clicked_pos = Vec2(m_pos.x, m_pos.y)
                    self.state = Mouse.DRAG
                case Mouse.RELEASE:
                    if globalClock.getFrameCount() <= self.dragging:
                        self.change_color(m_pos)
                    self.dragging = 0
                    self.state = None
                case Mouse.DRAG:
                    if 0 < self.dragging < globalClock.getFrameCount():
                        self.rotate(dt, m_pos)

        self.world.doPhysics(dt)
        return task.cont


class Face(NodePath):

    def __init__(self, name, geom_node):
        super().__init__(BulletRigidBodyNode(name))
        obj = self.attachNewNode(geom_node)  # obj.reparentTo(self)はいらない
        obj.setTwoSided(True)
        shape = BulletConvexHullShape()
        shape.addGeom(geom_node.getGeom(0))
        self.node().addShape(shape)
        self.setCollideMask(BitMask32(1))
        self.setScale(1.5)
        self.setR(-30)


class Polyhedron(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('polyhedronRoot'))
        self.reparentTo(base.render)
        self.world = world

    def make_faces(self, vertices, faces, color_pattern):
        n = max(color_pattern)
        colors = Colors.select(n + 1)

        for idx, (f, p) in enumerate(zip(faces, color_pattern)):
            face = (Vec3(vertices[i]) for i in f)
            geom_node = self.make_face_geomnode(face, len(f), colors[p])
            face = Face(f'face_{idx}', geom_node)
            face.reparentTo(self)
            self.world.attachRigidBody(face.node())

    def triangle(self, start):
        return (start, start + 1, start + 2)

    def square(self, start):
        for x, y, z in [(0, 1, 3), (1, 2, 3)]:
            yield (start + x, start + y, start + z)

    def polygon(self, start, vertices_num):
        for i in range(2, vertices_num):
            if i == 2:
                yield (start, start + i - 1, start + i)
            else:
                yield (start + i - 1, start, start + i)

    def prim_vertices(self, n, start):
        match n:
            case 3:
                yield self.triangle(start)
            case 4:
                yield from self.square(start)
            case _:
                yield from self.polygon(start, n)

    def make_face_geomnode(self, face, num_vertices, rgba):
        format_ = GeomVertexFormat.getV3n3cpt2()  # getV3n3c4
        vdata = GeomVertexData('triangle', format_, Geom.UHStatic)
        vdata.setNumRows(num_vertices)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')

        for pt in face:
            vertex.addData3(pt)
            normal.addData3(pt.normalized())
            color.addData4f(rgba)
            # texcoord.addData2f(tex)

        node = GeomNode('geomnode')
        prim = GeomTriangles(Geom.UHStatic)

        for vertices in self.prim_vertices(num_vertices, 0):
            prim.addVertices(*vertices)

        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node.addGeom(geom)

        return node

    def change_face_color(self, node_name, color):
        i = int(node_name.split('_')[1])
        face = self.getChild(i)
        face.setColor(color)

    def clear(self):
        for face in self.getChildren():
            self.world.remove(face.node())
            face.removeNode()

    def connect_geoms(self):
        format_ = GeomVertexFormat.getV3n3cpt2()  # getV3n3c4
        vdata = GeomVertexData('triangle', format_, Geom.UHStatic)
        vertex_writer = GeomVertexWriter(vdata, 'vertex')
        normal_writer = GeomVertexWriter(vdata, 'normal')
        color_writer = GeomVertexWriter(vdata, 'color')

        prim = GeomTriangles(Geom.UHStatic)
        start = 0

        for face in self.getChildren():
            rgba = face.getColor() if face.hasColor() else None
            np = face.findAllMatches('**/+GeomNode').getPath(0)
            geom_node = np.node()
            face_geom = geom_node.getGeom(0)
            face_vdata = face_geom.getVertexData()
            vertex_reader = GeomVertexReader(face_vdata, 'vertex')
            normal_reader = GeomVertexReader(face_vdata, 'normal')
            color_reader = GeomVertexReader(face_vdata, 'color')

            while not vertex_reader.isAtEnd():
                vertex_writer.addData3(vertex_reader.getData3())
                normal_writer.addData3(normal_reader.getData3())
                if rgba:
                    color_writer.addData4f(rgba)
                else:
                    color_writer.addData4f(color_reader.getData4f())

            n = face_vdata.getNumRows()
            for vertices in self.prim_vertices(n, start):
                prim.addVertices(*vertices)
            start += n

        node = GeomNode('geomnode')
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node.addGeom(geom)

        return node


if __name__ == '__main__':
    app = ColoringBoard()
    app.run()