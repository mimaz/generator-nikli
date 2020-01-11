##
 # 2019 Mieszko Mazurek <mimaz@gmx.com>
 ##

from dxfwrite import DXFEngine as dxf
import math

PI = math.acos(0) * 2

class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __hash__(self):
        return hash(self.x + 1000000 + self.y)

    def __eq__(self, other):
        return other != None and self.x == other.x and self.y == other.y

    def __str__(self):
        return "Vector({}, {})".format(self.x, self.y)

    def zero():
        return Vector(0, 0)

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def angle(self):
        angle = math.asin(abs(self.y / self.length()))
        if self.y < 0:
            if self.x < 0:
                return PI + angle
            return 2 * PI - angle
        else:
            if self.x < 0:
                return PI - angle
            return angle

    def normalized(self):
        return self.scaled(1 / self.length())

    def scaled(self, scale):
        return Vector(self.x * scale, self.y * scale)

    def add(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def sub(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def coords(self):
        return (self.x, self.y)

    def center(veclist):
        x = sum(map(lambda v: v.x, veclist))
        y = sum(map(lambda v: v.y, veclist))
        count = len(veclist)
        return Vector(float(x) / count, float(y) / count)

    def min(self, other):
        return Vector(min(self.x, other.x), min(self.y, other.y))

    def max(self, other):
        return Vector(max(self.x, other.x), max(self.y, other.y))

class Rect(Vector):
    def __init__(self, center, size):
        super(Rect, self).__init__(center.x, center.y)
        self.size = size

    def zero():
        return Rect(Vector.zero(), Vector.zero())

    def merge(self, other):
        lower = self.lower().min(other.lower())
        upper = self.upper().max(other.upper())
        center = Vector.center((lower, upper))
        size = upper.sub(lower)
        return Rect(center, size)

    def lower(self):
        return self.sub(self.size.scaled(0.5))

    def upper(self):
        return self.add(self.size.scaled(0.5))

class Node(Vector):
    def __init__(self, generator, vector):
        column, row = int(vector.x), int(vector.y)
        assert(column == vector.x)
        assert(row == vector.y)
        coords = generator.node_coords(column, row)
        super(Node, self).__init__(coords.x, coords.y)
        self.column = column
        self.row = row

    def __str__(self):
        return "Node({}, {})".format(self.column, self.row)

class Shape:
    def __init__(self, layer):
        self.layer = layer

class Line(Shape):
    def __init__(self, layer, start, end):
        super(Line, self).__init__(layer)
        self.start = start
        self.end = end

    def __str__(self):
        return "Line({} -> {})".format(self.start, self.end)

class Arc(Shape):
    def __init__(self, layer, center, radius, start, angle):
        super(Arc, self).__init__(layer)
        self.center = center
        self.radius = radius
        self.start = start
        self.angle = angle

    def __str__(self):
        start = self.start / PI
        angle = self.angle / PI
        return "Arc({} [{}] {}PI/{}PI)".format(self.center, self.radius, start, angle)

class Group:
    def __init__(self, array, layer):
        self.array = array
        self.layer = layer

    def generate_list(batgroups):
        grouplist = []
        prevgroup = []
        layer = 0
        for group in batgroups:
            merged = {*group, *prevgroup}
            grouplist.append(Group(merged, layer))
            layer = layer + 1
            #if layer > 0:
                #layer = 0
            #else:
                #layer = 1
            prevgroup = group
        grouplist.append(Group(prevgroup, layer))
        return grouplist

class Generator:
    def __init__(self, scalex, scaley):
        self.scale_x = scalex
        self.scale_y = scaley
        self.shapes = []
        self.layer_boxes = {}
        self.layer_count = 0
        self.compress_distance = 0
        self.secondary_offset = 0

    def draw_dxf(self, name):
        drawing = dxf.drawing(name)
        for shape in self.shapes:
            dxfshape = None
            layrow = shape.layer % 2
            laycolumn = shape.layer / 2
            if layrow == 0:
                offset_y = 0
            else:
                box = self.layer_boxes[0]
                offset_y = box.y + box.size.y / 2 - self.compress_distance

            offset_x = -self.compress_distance * laycolumn
            layer_offset = Vector(offset_x, offset_y)

            if isinstance(shape, Line):
                start = shape.start.add(layer_offset).coords()
                end = shape.end.add(layer_offset).coords()
                dxfshape = dxf.line(start, end)

            if isinstance(shape, Arc):
                center = shape.center.add(layer_offset).coords()
                start = math.degrees(shape.start)
                end = math.degrees(shape.start + shape.angle)
                dxfshape = dxf.arc(shape.radius, center, start, end)

            if dxfshape != None:
                drawing.add(dxfshape)
        drawing.save()

    def add_layer_box(self, rect):
        layrow = self.layer % 2
        if layrow in self.layer_boxes:
            prev = self.layer_boxes[layrow]
        else:
            prev = Rect.zero()
        self.layer_boxes[layrow] = prev.merge(rect)

    def add_line(self, start, end):
        box = Rect(Vector.center((start, end)), end.sub(start))
        self.add_layer_box(box)
        self.shapes.append(Line(self.layer, start, end))

    def add_arc(self, center, radius, start, angle):
        box = Rect(center, Vector(radius * 2, radius * 2))
        self.add_layer_box(box)
        self.shapes.append(Arc(self.layer, center, radius, start, angle))

    def add_reference_point(self, node, vertex):
        reference = vertex
        if not node in self.reference_points:
            self.reference_points[node] = []
        self.reference_points[node].append(reference)
        self.reference_used[vertex] = False
        self.reference_nodes[vertex] = node

    def load_group(self, group):
        nodes = list(map(lambda v: Node(self, Vector(*v)), group.array))
        first = nodes[0]
        left_column = first.column
        right_column = first.column
        bottom_row = first.row
        top_row = first.row
        for node in nodes[1:]:
            left_column = min(left_column, node.column)
            right_column = max(right_column, node.column)
            bottom_row = min(bottom_row, node.row)
            top_row = max(top_row, node.row)
        self.group = set(nodes)
        self.layer = group.layer
        self.reference_points = {}
        self.reference_used = {}
        self.reference_nodes = {}
        self.left_column = left_column
        self.right_column = right_column
        self.bottom_row = bottom_row
        self.top_row = top_row

class Triangle:
    def __init__(self, generator, first, second, third, orientation):
        def hole_vertex(point, central):
            width = generator.connection_width
            return central.sub(point).normalized().scaled(width).add(point)

        central = Vector.center((first, second, third))
        self.orientation = orientation
        self.nodefirst = first
        self.nodesecond = second
        self.nodethird = third
        self.first = hole_vertex(first, central)
        self.second = hole_vertex(second, central)
        self.third = hole_vertex(third, central)

class HexagonalGenerator(Generator):
    def __init__(self, scale, width, radius):
        vscale = scale * math.sqrt(3) / 2
        super(HexagonalGenerator, self).__init__(scale, vscale)
        self.triangle_radius = radius
        self.compress_distance = scale - width * math.sqrt(3) - 1
        self.connection_width = width

    def node_coords(self, column, row):
        x = (column + row % 2 * 0.5) * self.scale_x
        y = row * self.scale_y
        return Vector(x, y)

    def draw_round_triangle(self, first, second, third):
        margins = math.sqrt(3) * self.triangle_radius

        def corner(vertex, left, right):
            middle = Vector.center((left, right))
            vector = middle.sub(vertex).normalized().scaled(2 * self.triangle_radius)
            center = vector.add(vertex)
            angle = vector.angle() + PI * 2 / 3
            self.add_arc(center, self.triangle_radius, angle, PI * 2 / 3)

        def line(start, end):
            vector = end.sub(start).normalized().scaled(margins)
            start = start.add(vector)
            end = end.sub(vector)
            self.add_line(start, end)

        self.reference_used[first] = True
        self.reference_used[second] = True
        self.reference_used[third] = True
        corner(first, second, third)
        corner(third, first, second)
        corner(second, third, first)
        line(first, second)
        line(second, third)
        line(third, first)

    def draw_round_corner(self, first, second, third, order):
        self.reference_used[first] = True
        self.reference_used[second] = True
        third2vector = third.sub(first).scaled(2)
        secondvector = second.sub(first)
        middlevector = third2vector.sub(secondvector).normalized()
        sidevector = secondvector.normalized().scaled(2 - math.sqrt(3))
        center = first.add(middlevector.add(sidevector))
        vector = center.sub(first).normalized()
        radius = self.connection_width * (1 + math.sqrt(3) / 2)
        center = first.add(vector.scaled(radius / math.sin(math.radians(75))))
        angle = secondvector.angle() + PI / 2
        if order > 0:
            angle += PI * 5 / 6
        self.add_arc(center, radius, angle, PI / 6)
        target = second.sub(first).normalized()
        central = Vector.center((first, second))
        margins = self.connection_width / 2
        shifted = first.add(target.scaled(margins))
        self.add_line(shifted, central)

    def draw_round_line(self, first, second, third, order):
        self.draw_round_corner(first, second, third, order)
        self.draw_round_corner(second, first, third, order * -1)

    def draw_group(self):
        self.draw_holes()
        self.draw_corners()

    def draw_holes(self):
        bottom = self.bottom_row - 1
        top = self.top_row + 2
        left = self.left_column - 1
        right = self.right_column + 1
        row_range = range(bottom, top)
        column_range = range(left, right)
        nodes = []
        for row in row_range:
            for column in column_range:
                nodes.append(Node(self, Vector(column, row)))
        triangles = []
        for left in nodes:
            right = Node(self, Vector(left.column + 1, left.row))
            if left.row % 2:
                up = Node(self, Vector(left.column + 1, left.row + 1))
                down = Node(self, Vector(left.column + 1, left.row - 1))
            else:
                up = Node(self, Vector(left.column, left.row + 1))
                down = Node(self, Vector(left.column, left.row - 1))
            triangles.append(Triangle(self, left, right, up, 1))
            triangles.append(Triangle(self, left, right, down, -1))

        for t in triangles:
            self.add_reference_point(t.nodefirst, t.first)
            self.add_reference_point(t.nodesecond, t.second)
            self.add_reference_point(t.nodethird, t.third)

        for t in triangles:
            if all(map(lambda n: n in self.group, (t.nodefirst, t.nodesecond, t.nodethird))):
                self.draw_round_triangle(t.first, t.second, t.third)
            elif t.nodefirst in self.group and t.nodesecond in self.group:
                self.draw_round_line(t.first, t.second, t.third, t.orientation)
            elif t.nodefirst in self.group and t.nodethird in self.group:
                self.draw_round_line(t.first, t.third, t.second, -t.orientation)
            elif t.nodethird in self.group and t.nodesecond in self.group:
                self.draw_round_line(t.third, t.second, t.first, -t.orientation)

    def draw_corner(self, vertex, node):
        points = self.reference_points[node]
        distmap = {}
        for p in points:
            distmap[p] = p.sub(vertex).length()
        points = sorted(points, key = lambda v: distmap[v])
        points = list(filter(lambda p: distmap[p] != 0, points))
        shortest = distmap[points[0]]
        points = list(filter(lambda p: abs(distmap[p] - shortest) < 0.001, points))
        assert(len(points) == 2)
        first, second = points
        vector = node.sub(vertex).normalized()
        shift = math.tan(math.radians(30)) * 2
        central = vertex.add(vector.scaled(shift))
        start = central.sub(node).angle() - PI / 6
        radius = self.connection_width / 2 * math.sqrt(3)
        self.add_arc(node, radius, start, PI / 3)

    def draw_corners(self):
        for node in filter(lambda n: n in self.group, self.reference_points):
            for ref in self.reference_points[node]:
                vertex = ref
                if not self.reference_used[vertex]:
                    self.draw_corner(vertex, node)

    def draw_dilatation(self, x, y):
        for node in self.group:
            shift = Vector(x / 2, y / 2)
            left = node.sub(shift)
            right = node.add(shift)
            self.add_line(left, right)
