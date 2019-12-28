#!/usr/bin/python

from dxfwrite import DXFEngine as dxf
import math
import subprocess

PI = 3.14159

def vector_length(vec):
    return math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])

def vector_angle(vec):
    tan = math.atan(abs(vec[1] / vec[0]))
    if vec[1] < 0:
        if vec[0] < 0:
            return PI + tan
        return 2 * PI - tan
    else:
        if vec[0] < 0:
            return PI - tan
        return tan

def normalize_vector(vec):
    return scale_vector(vec, 1 / vector_length(vec))

def scale_vector(vec, scale):
    return (vec[0] * scale, vec[1] * scale)

def add_vector(vec, add):
    return (vec[0] + add[0], vec[1] + add[1])

def sub_vector(vec, sub):
    return (vec[0] - sub[0], vec[1] - sub[1])

def central_point(pointlist):
    x = 0
    y = 0
    for point in pointlist:
        x += point[0]
        y += point[1]
    return (x / len(pointlist), y / len(pointlist))

class ReferencePoint:
    def __init__(self, vertex, angle, targetlist):
        self.vertex = vertex
        self.targetset = set(targetlist)
        self.angle = angle

class Generator:
    def __init__(self, filename, scalex, scaley, offx):
        self.connection_width = 5
        self.odd_offset_x = offx
        self.scale_x = scalex
        self.scale_y = scaley
        self.graph = {}
        self.group = {}
        self.holes = {}
        self.drawing = dxf.drawing(filename)
        self.reference_points = {}
        self.reference_parents = {}

    def save(self):
        self.drawing.save()

    def add_line(self, start, end):
        self.drawing.add(dxf.line(start, end))

    def add_blind_line(self, start, end):
        self.add_line(start, end)

    def add_arc(self, radius, center, start, end):
        self.drawing.add(dxf.arc(radius, center, start, end))

    def add_reference_point(self, node, targetlist, vertex):
        reference = ReferencePoint(vertex, 0, targetlist)
        if not node in self.reference_points:
            self.reference_points[node] = []
        if node == (0, 0):
            print("add 0 0: ", vertex, " :: ", targetlist)
        self.reference_points[node].append(reference)
        self.reference_parents[vertex] = node

    def find_target_reference_points(self, node, target):
        points = []
        for reference in self.reference_points[node]:
            if target in reference.targetset:
                points.append(reference.vertex)
        return points

    def close_blind(self, node, target):
        points = self.find_target_reference_points(node, target)
        if len(points) == 2:
            self.add_blind_line(points[0], points[1])

    def real_coord(self, abstract):
        column, row = abstract
        print("real row ", int(row))
        coordx = column + row % 2 * self.odd_offset_x
        coordy = row
        return (coordx * self.scale_x, coordy * self.scale_y)

    def make_graph(self, group):
        graph = {}
        left_column = 10000
        right_column = -10000
        bottom_row = 10000
        top_row = -10000
        for vertex in group:
            left_column = min(left_column, vertex[0])
            right_column = max(right_column, vertex[0])
            bottom_row = min(bottom_row, vertex[1])
            top_row = max(top_row, vertex[1])
            if not vertex in graph:
                graph[vertex] = {}
            for c in self.all_vertex_edges(*vertex):
                graph[vertex][c] = c in group
        self.graph = graph
        self.group = group
        self.left_column = left_column
        self.right_column = right_column
        self.bottom_row = bottom_row
        self.top_row = top_row

    def all_valid(self, pointlist):
        for point in pointlist:
            if not point in self.group:
                return False
        return True

    def print_graph(self):
        for v in self.graph:
            print("vertex: ", v)
            for e in self.graph[v]:
                print("    edge: ", e)

class Triangle:
    def __init__(self, gen, first, second, third, orientation):
        def hole_vertex(point, central):
            vector = (central[0] - point[0], central[1] - point[1])
            vector = normalize_vector(vector)
            vector = scale_vector(vector, gen.connection_width)
            return (point[0] + vector[0], point[1] + vector[1])

        realfirst = gen.real_coord(first)
        realsecond = gen.real_coord(second)
        realthird = gen.real_coord(third)

        central = central_point((realfirst, realsecond, realthird))
        self.first = first
        self.second = second
        self.third = third
        self.orientation = orientation
        self.realfirst = hole_vertex(realfirst, central)
        self.realsecond = hole_vertex(realsecond, central)
        self.realthird = hole_vertex(realthird, central)

class HexagonalGenerator(Generator):
    def __init__(self, filename, scale, width):
        vscale = scale * math.sqrt(3) / 2
        super(HexagonalGenerator, self).__init__(filename, scale, vscale, 0.5)

    def all_vertex_edges(self, column, row):
        edges = []
        edges.append((column + 1, row))
        edges.append((column - 1, row))
        edges.append((column, row + 1))
        edges.append((column, row - 1))
        if row % 2:
            edges.append((column + 1, row + 1))
            edges.append((column + 1, row - 1))
        else:
            edges.append((column - 1, row + 1))
            edges.append((column - 1, row - 1))
        return edges

    def add_line_with_margins(self, start, end, margins):
        vector = (end[0] - start[0], end[1] - start[1])
        vector = normalize_vector(vector)
        vector = scale_vector(vector, margins)
        start = add_vector(start, vector)
        end = sub_vector(end, vector)
        self.add_line(start, end)

    def draw_triangle_corner(self, vertex, left, right):
        middle = central_point((left, right))
        vector = sub_vector(middle, vertex)
        vector = normalize_vector(vector)
        vector = scale_vector(vector, 2)
        center = add_vector(vertex, vector)
        angle = math.asin(vector[1] / vector_length(vector))
        angle = math.degrees(angle)
        angle = angle + 120
        if vector[0] < 0:
            angle = angle + 120
            if vector[1] < 0:
                angle = angle + 120
        self.add_arc(1, center, angle, angle + 120)

    def draw_round_triangle(self, first, second, third):
        self.draw_triangle_corner(first, second, third)
        self.draw_triangle_corner(third, first, second)
        self.draw_triangle_corner(second, third, first)
        self.add_line_with_margins(first, second, math.sqrt(3))
        self.add_line_with_margins(second, third, math.sqrt(3))
        self.add_line_with_margins(third, first, math.sqrt(3))

    def draw_round_corner(self, first, second, third, order):
        margins = 2 - math.sqrt(3)
        v1 = sub_vector(third, first)
        v2 = scale_vector(v1, 2)
        v3 = sub_vector(second, first)
        v4 = normalize_vector(sub_vector(v2, v3))
        v5 = scale_vector(normalize_vector(v3), 2 - math.sqrt(3))
        v6 = normalize_vector(sub_vector(v3, v2))
        center = add_vector(first, add_vector(v4, v5))
        radians = vector_angle(v3)
        degrees = math.degrees(radians) + 90
        if order > 0:
            degrees = degrees + 150
        end = degrees + 30
        self.add_arc(1, center, degrees, end)
        target = normalize_vector(sub_vector(second, first))
        central = central_point((first, second))
        shifted = add_vector(first, scale_vector(target, margins))
        self.add_line(shifted, central)
        node = self.reference_parents[first]
        assert(node in self.group)
        points = self.reference_points[node]
        firstdistmap = {}
        seconddistmap = {}
        for p in points:
            firstdistmap[p] = vector_length(sub_vector(p.vertex, first))
            seconddistmap[p] = vector_length(sub_vector(p.vertex, second))
        def distance_first(p):
            return firstdistmap[p]
        def distance_second(p):
            return seconddistmap[p]
        points = sorted(points, key=distance_first)
        points = list(filter(lambda p: firstdistmap[p] != 0, points))
        if len(points) < 1:
            return
        shortest = firstdistmap[points[0]]
        points = list(filter(lambda p: abs(firstdistmap[p] - shortest) < 0.001, points))
        points = sorted(points, key=distance_second)
        point = points[0]
        print("shortest: ", shortest)
        for point in points:
            print(node, " -> ", point.vertex, " : ", vector_length(sub_vector(point.vertex, first)))
        center = central_point((point.vertex, first))
        vector = sub_vector(point.vertex, first)
        vector = normalize_vector(vector)
        vector = scale_vector(vector, math.tan(math.radians(15)) * 1)
        start = add_vector(first, vector)
        self.add_line(start, center)

    def draw_round_line(self, first, second, third, order):
        self.draw_round_corner(first, second, third, order)
        self.draw_round_corner(second, first, third, order * -1)

    def make_holes(self):
        bottom = self.bottom_row - 1
        top = self.top_row + 2
        left = self.left_column - 1
        right = self.right_column + 1
        row_range = range(bottom, top)
        column_range = range(left, right)
        nodes = []
        for row in row_range:
            for column in column_range:
                nodes.append((column, row))
        triangles = []
        for left in nodes:
            right = (left[0] + 1, left[1])
            if left[1] % 2:
                up = (left[0] + 1, left[1] + 1)
                down = (left[0] + 1, left[1] - 1)
            else:
                up = (left[0], left[1] + 1)
                down = (left[0], left[1] - 1)
            triangles.append(Triangle(self, left, right, up, 1))
            triangles.append(Triangle(self, left, right, down, -1))

        for t in triangles:
            self.add_reference_point(t.first, (t.second, t.third), t.realfirst)
            self.add_reference_point(t.second, (t.first, t.third), t.realsecond)
            self.add_reference_point(t.third, (t.first, t.second), t.realthird)

        for t in triangles:
            if self.all_valid((t.first, t.second, t.third)):
                self.draw_round_triangle(t.realfirst, t.realsecond, t.realthird)
            elif t.first in self.group and t.second in self.group:
                self.draw_round_line(t.realfirst, t.realsecond, t.realthird, t.orientation)
            elif t.first in self.group and t.third in self.group:
                self.draw_round_line(t.realfirst, t.realthird, t.realsecond, -t.orientation)
            elif t.third in self.group and t.second in self.group:
                self.draw_round_line(t.realthird, t.realsecond, t.realfirst, -t.orientation)

    def add_blind_line(self, start, end):
        self.add_line_with_margins(start, end, 2 - math.sqrt(3))

    def make_blinds(self):
        for node in self.group:
            for target in filter(lambda t: not t in self.group, self.all_vertex_edges(*node)):
                generator.close_blind(node, target)
                vector = (target[0] - node[0], target[1] - node[1])
                magnitude = math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])
                vector = (vector[0] / magnitude, vector[1] / magnitude)

groups=[
        {(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (1, 3)},
]

generator = HexagonalGenerator('nikle.dxf', 19.5, 6)
generator.make_graph(groups[0])
generator.make_holes()
#generator.make_blinds()
#generator.print_graph()
generator.save()
