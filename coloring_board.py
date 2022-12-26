from collections import defaultdict
from enum import Enum, auto
from textwrap import wrap

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import WindowProperties, PandaNode, NodePath
from panda3d.core import Vec3, LColor, Point3, Vec2
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexArrayFormat
from panda3d.core import Geom, GeomTriangles, GeomVertexReader, GeomVertexWriter
from panda3d.core import GeomNode
from panda3d.core import BitMask32
from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletConvexHullShape

from db_manage import get_vertices, get_faces
from tkwindow import WindowTk


class Colors(Enum):
    FLORALWHITE = LColor(1.0, 0.98, 0.94, 1.0)
    SEASHELL = LColor(1.0, 0.96, 0.93, 1.0)
    OLDLACE = LColor(0.99, 0.96, 0.9, 1.0)
    IVORY = LColor(1.0, 1.0, 0.94, 1.0)
    BEIGE = LColor(0.96, 0.96, 0.86, 1.0)
    LINEN = LColor(0.98, 0.94, 0.90, 1.0)
    ANTIQUEWHITE = LColor(0.98, 0.92, 0.84, 1.0)
    WHITESMOKE = LColor(0.96, 0.96, 0.96, 1.0)
    GHOSTWHITE = LColor(0.97, 0.97, 1.0, 1.0)
    SNOW = LColor(1.0, 0.98, 0.98, 1.0)


class Mouse(Enum):

    CLICK = auto()
    RELEASE = auto()
    DRAG = auto()


class ColoringBoard(ShowBase):

    def __init__(self):
        super().__init__(windowType='none')
        self.world = BulletWorld()
        self.polh = Polyhedron(self.world)

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
        self.makeDefaultPipe()
        self.openMainWindow(type='onscreen', props=props, size=(800, 600))

        self.disableMouse()
        self.camera_np = NodePath(PandaNode('cameraNode'))
        self.camera_np.reparentTo(self.render)
        self.camera.reparentTo(self.camera_np)
        self.camera.setPos(15, 0, 0)
        self.camera.lookAt(0, 0, 0)

        self.debug = self.render.attachNewNode(BulletDebugNode('debug'))
        self.world.setDebugNode(self.debug.node())
        self.debug.show()

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

    def save_file(self, filepath):
        geom_node = self.polh.assemble()
        np = NodePath(PandaNode(filepath.stem))
        obj = np.attachNewNode(geom_node)
        obj.setTwoSided(True)
        np.writeBamFile(filepath.name)

    def open_file(self, filepath):
        self.polh.clear()
        model = self.loader.loadModel(filepath.name)
        self.polh.disassemble(model)

    def change_color(self, m_pos):
        near_pos = Point3()
        far_pos = Point3()
        self.camLens.extrude(m_pos, near_pos, far_pos)
        from_pos = self.render.getRelativePoint(self.cam, near_pos)
        to_pos = self.render.getRelativePoint(self.cam, far_pos)
        result = self.world.rayTestClosest(from_pos, to_pos)

        if result.hasHit():
            if hexa_color := self.app.selected_color():
                node = result.getNode()
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

        for i, (f, p) in enumerate(zip(faces, color_pattern)):
            face_vertices = (Vec3(vertices[i]) for i in f)
            self.polh.make_face(face_vertices, len(f), i, self.polh.colors[p])

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
            vec.x -= 180
        elif delta_x > 0:
            vec.x += 180

        if delta_y < 0:
            vec.z -= 180
        elif delta_y > 0:
            vec.z += 180

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
        obj = self.attachNewNode(geom_node)
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
        self.colors = [m.value for m in Colors]
        self.polh_format = self.make_custom_format()

    def make_custom_format(self):
        array = GeomVertexArrayFormat()
        array.addColumn('vertex', 3, Geom.NTFloat32, Geom.CPoint)
        array.addColumn('color', 4, Geom.NTFloat32, Geom.CColor)
        array.addColumn('normal', 3, Geom.NTFloat32, Geom.CNormal)
        array.addColumn('face', 1, Geom.NTUint8, Geom.COther)
        format_ = GeomVertexFormat()
        format_.addArray(array)
        format_ = GeomVertexFormat.registerFormat(format_)
        return format_

    def get_vdata(self, np, modify=False):
        found = np.findAllMatches('**/+GeomNode').getPath(0)
        geom_node = found.node()

        if modify:
            geom = geom_node.modifyGeom(0)
            vdata = geom.modifyVertexData()
        else:
            geom = geom_node.getGeom(0)
            vdata = geom.getVertexData()

        return vdata

    def disassemble(self, model):
        vdata = self.get_vdata(model)
        vertex_reader = GeomVertexReader(vdata, 'vertex')
        face_reader = GeomVertexReader(vdata, 'face')
        color_reader = GeomVertexReader(vdata, 'color')

        face_dic = defaultdict(list)
        color_dic = dict()

        while not vertex_reader.isAtEnd():
            vertex = vertex_reader.getData3()
            color = color_reader.getData4()
            face_num = face_reader.getData1i()

            face_dic[face_num].append(vertex)
            if face_num not in color_dic:
                color_dic[face_num] = LColor(color)

        for key, face_vertices in face_dic.items():
            self.make_face(face_vertices, len(face_vertices), key, color_dic[key])

    def make_face(self, face_vertices, num_vertices, face_num, color):
        geom_node = self.make_geomnode(face_vertices, num_vertices, face_num, color)
        face = Face(f'face_{face_num}', geom_node)
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

    def make_geomnode(self, face_vertices, num_vertices, face_num, rgba):
        vdata = GeomVertexData('polyhedron', self.polh_format, Geom.UHStatic)
        vdata.setNumRows(num_vertices)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        face = GeomVertexWriter(vdata, 'face')

        for pt in face_vertices:
            vertex.addData3(pt)
            normal.addData3(pt.normalized())
            color.addData4f(rgba)
            face.add_data1i(face_num)

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
        vdata = self.get_vdata(face, modify=True)
        color_writer = GeomVertexWriter(vdata, 'color')

        while not color_writer.isAtEnd():
            color_writer.setData4f(color)

    def clear(self):
        for face in self.getChildren():
            self.world.remove(face.node())
            face.removeNode()

    def assemble(self):
        """Connect faces into one polyhedron.
        """
        vdata = GeomVertexData('polyhedron', self.polh_format, Geom.UHStatic)
        vertex_writer = GeomVertexWriter(vdata, 'vertex')
        normal_writer = GeomVertexWriter(vdata, 'normal')
        color_writer = GeomVertexWriter(vdata, 'color')
        face_writer = GeomVertexWriter(vdata, 'face')

        prim = GeomTriangles(Geom.UHStatic)
        start = 0

        for child in self.getChildren():
            child_vdata = self.get_vdata(child)
            vertex_reader = GeomVertexReader(child_vdata, 'vertex')
            normal_reader = GeomVertexReader(child_vdata, 'normal')
            color_reader = GeomVertexReader(child_vdata, 'color')
            face_reader = GeomVertexReader(child_vdata, 'face')

            while not vertex_reader.isAtEnd():
                vertex_writer.addData3(vertex_reader.getData3())
                normal_writer.addData3(normal_reader.getData3())
                face_writer.addData1i(face_reader.getData1i())
                color_writer.addData4f(color_reader.getData4f())

            n = child_vdata.getNumRows()
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