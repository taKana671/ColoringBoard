import random
from enum import Enum
from textwrap import wrap

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import WindowProperties, PandaNode, NodePath
from panda3d.core import Point3
from panda3d.core import Vec3, LColor, Point3, VBase4, Quat
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexWriter, GeomVertexRewriter
from panda3d.core import GeomNode
from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletConvexHullShape


from panda3d.core import BitMask32

from tkwindow import WindowTk
from polyhedrons_data import POLYHEDRONS


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


class ColoringBoard(ShowBase):

    def __init__(self):
        super().__init__(windowType='none')
        self.startTk()
        root = self.tkRoot
        root.geometry('1080x640')
        root.resizable(False, False)
        self.app = WindowTk(root)
        root.bind('<Escape>', self.app.close)

        props = WindowProperties()
        props.setParentWindow(root.winfo_id())
        props.setOrigin(260, 20)
        props.setSize(800, 600)
        # props.setSize(self.frame.winfo_width(), self.frame.winfo_height())
        self.makeDefaultPipe()
        self.openMainWindow(type='onscreen', props=props, size=(800, 600))

        self.disableMouse()
        self.camera.setPos(10, 10, 10)
        self.camera.lookAt(0, 0, 0)

        self.world = BulletWorld()

        # **********************************************************
        debug = self.render.attachNewNode(BulletDebugNode('debug'))
        self.world.setDebugNode(debug.node())
        debug.show()
        # **********************************************************    
        self.show_polh()

        self.dragging = 0
        self.clicked_pos = None

        self.accept('mouse1', self.click)
        self.accept('mouse1-up', self.release)
        self.taskMgr.add(self.update, 'update')

    def click(self):
        self.clicked_pos = self.mouseWatcherNode.getMouse()
        self.dragging = globalClock.getFrameCount() + 7

    def release(self):
        if globalClock.getFrameCount() <= self.dragging:
            self.change_color()
        self.dragging = 0

    def change_color(self):
        near_pos = Point3()
        far_pos = Point3()
        self.camLens.extrude(self.clicked_pos, near_pos, far_pos)
        from_pos = self.render.getRelativePoint(self.cam, near_pos)
        to_pos = self.render.getRelativePoint(self.cam, far_pos)
        result = self.world.rayTestClosest(from_pos, to_pos)
        if result.hasHit():
            node = result.getNode()
            name = node.getName()
            idx = int(name.split('_')[1])
            face = self.faces[idx]

            if hexa_color := self.app.selected_color():
                rgb = [int(n, 16) / 255 for n in wrap(hexa_color[1:], 2)]
                color = LColor(*rgb, 1)
                face.setColor(color)

    def show_polh(self):
        self.faces = [face for face in self.make_polh()]

    def make_polh(self):
        shape_root = NodePath(PandaNode('shape'))
        shape_root.reparentTo(self.render)

        self.data = POLYHEDRONS['elongated_pentagonal_rotunda']
        vertices = self.data['vertices']
        faces = self.data['faces']
        color_pattern = self.data['color_pattern']

        n = max(self.data['color_pattern'])
        colors = Colors.select(n + 1)
        maker = GeomMaker()

        for idx, (f, p) in enumerate(zip(faces, color_pattern)):
            face = [Vec3(vertices[i]) for i in f]
            geom_node = maker.make_geomnode(face, colors[p])
            face = Face(f'face_{idx}', geom_node)
            face.reparentTo(shape_root)
            self.world.attachRigidBody(face.node())
            yield face

        # shape_root.hprInterval(8, (360, 720, 360)).loop()

    
    def rotate(self, dt):
        angle = 45 * dt
        axis = Vec3.up()
        # # axis = Vec3.right()
        # # axis = Vec3.forward()
        # axis = Vec3.back()

        q = Quat()
        q.setFromAxisAngle(angle, axis.normalized())
        r = q.xform(self.camera.getPos() - Point3(0, 0, 0))
        rotated_pos = Point3(0, 0, 0) + r
        self.camera.setPos(rotated_pos)

        self.camera.setH(self.camera.getH() + angle)



        # self.camera.setP(self.camera.getP() + angle)

        
        # self.camera.lookAt(Point3(0, 0, 0))
        # self.camera.lookAt(Point3(0, 0, 0))
        # self.camera.lookAt(Point3(0, 0, 0))
        # print(self.camera.getHpr())
        
        # self.camera.setHpr(self.camera.getHpr() + axis * 3)
    
    def update(self, task):
        dt = globalClock.getDt()

        if 0 < self.dragging < globalClock.getFrameCount():
            self.rotate(dt)

        self.world.doPhysics(dt)
        return task.cont


class Face(NodePath):

    def __init__(self, name, geom_node):
        super().__init__(BulletRigidBodyNode(name))
        # self.reparentTo(base.render)
        obj = self.attachNewNode(geom_node)
        obj.setTwoSided(True)
        obj.reparentTo(self)
        shape = BulletConvexHullShape()
        shape.addGeom(geom_node.getGeom(0))
        self.node().addShape(shape)
        self.setCollideMask(BitMask32(1))
        self.setScale(1.5)


class GeomMaker:

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

    def prim_vertices(self, face):
        start = 0
        if (vertices_num := len(face)) == 3:
            yield self.triangle(start)
        elif vertices_num == 4:
            yield from self.square(start)
        elif vertices_num >= 5:
            yield from self.polygon(start, vertices_num)
        start += vertices_num

    def make_geomnode(self, face, rgba):
        format_ = GeomVertexFormat.getV3n3cpt2()  # getV3n3c4
        vdata = GeomVertexData('triangle', format_, Geom.UHStatic)
        vdata.setNumRows(len(face))

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        # texcoord = GeomVertexWriter(vdata, 'texcoord')

        for pt in face:
            vertex.addData3(pt)
            normal.addData3(pt.normalized())
            color.addData4f(rgba)
            # texcoord.addData2f(tex)

        node = GeomNode('geomnode')
        prim = GeomTriangles(Geom.UHStatic)

        for vertices in self.prim_vertices(face):
            prim.addVertices(*vertices)

        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node.addGeom(geom)

        return node



if __name__ == '__main__':
    # app = tk.Tk()
    # window = WindowTk(app)
    # window.mainloop()
    # root = tk.Tk()
    # Pmw.initialise(root)
    
    app = ColoringBoard()
    app.run()