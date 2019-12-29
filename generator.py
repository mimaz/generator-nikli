#!/usr/bin/python

from dxfwrite import DXFEngine as dxf
import math

PI = math.acos(0) * 2

def vector_length(vec):
    return math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])

def vector_angle(vec):
    angle = math.asin(abs(vec[1] / vector_length(vec)))
    if vec[1] < 0:
        if vec[0] < 0:
            return PI + angle
        return 2 * PI - angle
    else:
        if vec[0] < 0:
            return PI - angle
        return angle

def normalize_vector(vec):
    return scale_vector(vec, 1 / vector_length(vec))

def scale_vector(vec, scale):
    return (vec[0] * scale, vec[1] * scale)

def add_vector(vec, add):
    return (vec[0] + add[0], vec[1] + add[1])

def sub_vector(vec, sub):
    return (vec[0] - sub[0], vec[1] - sub[1])

def central_point(veclist):
    x = sum(map(lambda v: v[0], veclist))
    y = sum(map(lambda v: v[1], veclist))
    count = len(veclist)
    return (x / count, y / count)

class Node:
    def __init__(self, column, row):
        self.column = column
        self.row = row
        self.coord = (column, row)

    def __hash__(self):
        return hash(self.row * 1000 + self.column)

    def __eq__(self, other):
        return self.column == other.column and self.row == other.row

    def __str__(self):
        return "Node({}, {})".format(self.column, self.row)

    def position_x(self, generator):
        return (self.column + self.row % 2 * generator.odd_offset_x) * generator.scale_x

    def position_y(self, generator):
        return (self.row * generator.scale_y)

    def position(self, generator):
        return (self.position_x(generator), self.position_y(generator))

class Line:
    def __init__(self, start, end):
        self.start = start
        self.end = end

class Arc:
    def __init__(self, center, radius, start, angle):
        self.center = center
        self.radius = radius
        self.start = start
        self.angle = angle

class Generator:
    def __init__(self, scalex, scaley, offx):
        self.connection_width = 5
        self.odd_offset_x = offx
        self.scale_x = scalex
        self.scale_y = scaley
        self.group = {}
        self.reference_points = {}
        self.reference_used = {}
        self.reference_nodes = {}
        self.shapes = []

    def draw_dxf(self, name):
        drawing = dxf.drawing(name)
        for shape in self.shapes:
            dxfshape = None

            if isinstance(shape, Line):
                dxfshape = dxf.line(shape.start, shape.end)

            if isinstance(shape, Arc):
                start = math.degrees(shape.start)
                end = math.degrees(shape.start + shape.angle)
                dxfshape = dxf.arc(shape.radius, shape.center, start, end)

            if dxfshape != None:
                drawing.add(dxfshape)
        drawing.save()

    def add_line(self, start, end):
        self.shapes.append(Line(start, end))

    def add_arc(self, center, radius, start, angle):
        self.shapes.append(Arc(center, radius, start, angle))

    def add_reference_point(self, node, vertex):
        reference = vertex
        if not node in self.reference_points:
            self.reference_points[node] = []
        self.reference_points[node].append(reference)
        self.reference_used[vertex] = False
        self.reference_nodes[vertex] = node

    def load_group(self, group):
        nodes = list(map(lambda c: Node(*c), group))
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
        self.left_column = left_column
        self.right_column = right_column
        self.bottom_row = bottom_row
        self.top_row = top_row

class Triangle:
    def __init__(self, generator, first, second, third, orientation):
        def hole_vertex(point, central):
            vector = (central[0] - point[0], central[1] - point[1])
            vector = normalize_vector(vector)
            vector = scale_vector(vector, generator.connection_width)
            return (point[0] + vector[0], point[1] + vector[1])

        realfirst = first.position(generator)
        realsecond = second.position(generator)
        realthird = third.position(generator)

        central = central_point((realfirst, realsecond, realthird))

        self.orientation = orientation
        self.nodefirst = first
        self.nodesecond = second
        self.nodethird = third
        self.realfirst = hole_vertex(realfirst, central)
        self.realsecond = hole_vertex(realsecond, central)
        self.realthird = hole_vertex(realthird, central)

class HexagonalGenerator(Generator):
    def __init__(self, scale, width, radius):
        vscale = scale * math.sqrt(3) / 2
        super(HexagonalGenerator, self).__init__(scale, vscale, 0.5)
        self.triangle_radius = radius

    def draw_round_triangle(self, first, second, third):
        margins = math.sqrt(3) * self.triangle_radius

        def corner(vertex, left, right):
            middle = central_point((left, right))
            vector = sub_vector(middle, vertex)
            vector = normalize_vector(vector)
            vector = scale_vector(vector, 2 * self.triangle_radius)
            center = add_vector(vertex, vector)
            angle = vector_angle(vector) + PI * 2 / 3
            self.add_arc(center, self.triangle_radius, angle, PI * 2 / 3)

        def line(start, end):
            vector = (end[0] - start[0], end[1] - start[1])
            vector = normalize_vector(vector)
            vector = scale_vector(vector, margins)
            start = add_vector(start, vector)
            end = sub_vector(end, vector)
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
        third2vector = scale_vector(sub_vector(third, first), 2)
        secondvector = sub_vector(second, first)
        middlevector = normalize_vector(sub_vector(third2vector, secondvector))
        sidevector = scale_vector(normalize_vector(secondvector), 2 - math.sqrt(3))
        center = add_vector(first, add_vector(middlevector, sidevector))
        vector = normalize_vector(sub_vector(center, first))
        radius = self.connection_width * (1 + math.sqrt(3) / 2)
        center = add_vector(first, scale_vector(vector, radius / math.sin(math.radians(75))))
        angle = vector_angle(secondvector) + PI / 2
        if order > 0:
            angle += PI * 5 / 6
        self.add_arc(center, radius, angle, PI / 6)
        target = normalize_vector(sub_vector(second, first))
        central = central_point((first, second))
        margins = self.connection_width / 2
        shifted = add_vector(first, scale_vector(target, margins))
        self.add_line(shifted, central)

    def draw_round_line(self, first, second, third, order):
        self.draw_round_corner(first, second, third, order)
        self.draw_round_corner(second, first, third, order * -1)

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
                nodes.append(Node(column, row))
        triangles = []
        for left in nodes:
            right = Node(left.column + 1, left.row)
            if left.row % 2:
                up = Node(left.column + 1, left.row + 1)
                down = Node(left.column + 1, left.row - 1)
            else:
                up = Node(left.column, left.row + 1)
                down = Node(left.column, left.row - 1)
            triangles.append(Triangle(self, left, right, up, 1))
            triangles.append(Triangle(self, left, right, down, -1))

        for t in triangles:
            self.add_reference_point(t.nodefirst, t.realfirst)
            self.add_reference_point(t.nodesecond, t.realsecond)
            self.add_reference_point(t.nodethird, t.realthird)

        for t in triangles:
            if t.nodefirst in self.group and t.nodesecond in self.group and t.nodethird in self.group:
                self.draw_round_triangle(t.realfirst, t.realsecond, t.realthird)
            elif t.nodefirst in self.group and t.nodesecond in self.group:
                self.draw_round_line(t.realfirst, t.realsecond, t.realthird, t.orientation)
            elif t.nodefirst in self.group and t.nodethird in self.group:
                self.draw_round_line(t.realfirst, t.realthird, t.realsecond, -t.orientation)
            elif t.nodethird in self.group and t.nodesecond in self.group:
                self.draw_round_line(t.realthird, t.realsecond, t.realfirst, -t.orientation)

    def draw_corner(self, vertex, node):
        center = node.position(self)
        points = list(map(lambda r: r, self.reference_points[node]))
        distmap = {}
        for p in points:
            distmap[p] = vector_length(sub_vector(p, vertex))
        def vertex_distance(v):
            return distmap[v]
        points = sorted(points, key = vertex_distance)
        points = list(filter(lambda p: distmap[p] != 0, points))
        shortest = distmap[points[0]]
        points = list(filter(lambda p: abs(distmap[p] - shortest) < 0.001, points))
        assert(len(points) == 2)
        first, second = points
        vector = normalize_vector(sub_vector(center, vertex))
        shift = math.tan(math.radians(30)) * 2
        central = add_vector(vertex, scale_vector(vector, shift))
        start = vector_angle(sub_vector(central, center)) - PI / 6
        radius = self.connection_width / 2 * math.sqrt(3)
        self.add_arc(center, radius, start, PI / 3)

    def draw_corners(self):
        for node in filter(lambda n: n in self.group, self.reference_points):
            for ref in self.reference_points[node]:
                vertex = ref
                if not self.reference_used[vertex]:
                    self.draw_corner(vertex, node)

groups=[
        {(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (1, 3), (0, -1), (2, 1), (-1, 2), (2, 2), (2, 0)},
]

generator = HexagonalGenerator(19.5, 6, 1.5)
generator.load_group(groups[0])
generator.draw_holes()
generator.draw_corners()
generator.draw_dxf('nikle.dxf')
