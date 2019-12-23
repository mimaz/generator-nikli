#!/usr/bin/python

from dxfwrite import DXFEngine as dxf
import math
import subprocess

def vector_length(vec):
    return math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])

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
    def __init__(self, vertex, targetlist):
        self.vertex = vertex
        self.targetset = set(targetlist)

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

    def save(self):
        self.drawing.save()

    def add_line(self, start, end):
        self.drawing.add(dxf.line(start, end))

    def add_arc(self, radius, center, start, end):
        self.drawing.add(dxf.arc(radius, center, start, end))

    def add_reference_point(self, node, targetlist, vertex):
        reference = ReferencePoint(vertex, targetlist)
        if not node in self.reference_points:
            self.reference_points[node] = []
        self.reference_points[node].append(reference)

    def find_target_reference_points(self, node, target):
        points = []
        for reference in self.reference_points[node]:
            if target in reference.targetset:
                points.append(reference.vertex)
        return points

    def close_blind(self, node, target):
        points = self.find_target_reference_points(node, target)
        if len(points) == 2:
            self.add_line(points[0], points[1])

    def real_coord(self, abstract):
        column, row = abstract
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
            for c in filter(lambda c: c in group, self.all_vertex_edges(*vertex)):
                graph[vertex][c] = True
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

    def hole_vertex(self, point, central):
        vector = (central[0] - point[0], central[1] - point[1])
        vector = normalize_vector(vector)
        shift = self.connection_width
        return (point[0] + vector[0] * shift, point[1] + vector[1] * shift)

    def add_line(self, start, end):
        vector = (end[0] - start[0], end[1] - start[1])
        vector = normalize_vector(vector)
        vector = scale_vector(vector, 1)
        start = add_vector(start, vector)
        end = sub_vector(end, vector)
        super(HexagonalGenerator, self).add_line(start, end)

    def round_triangle(self, vertex, left, right):
        middle = central_point((left, right))
        vector = sub_vector(middle, vertex)
        vector = normalize_vector(vector)
        vector = scale_vector(vector, math.sqrt(3) / 6 * 2 * 2)
        center = add_vector(vertex, vector)
        angle = math.asin(vector[1] / vector_length(vector))
        angle = math.degrees(angle)
        angle = angle + 120
        if vector[0] < 0:
            angle = angle + 120
            if vector[1] < 0:
                angle = angle + 120
        self.add_arc(math.sqrt(3) / 3, center, angle, angle + 120)

    def make_holes(self):
        row_range = range(self.bottom_row - 1, self.top_row + 2)
        column_range = range(self.left_column - 1, self.right_column + 1)
        nodes = []
        for row in row_range:
            for column in column_range:
                nodes.append((column, row))
        for left in nodes:
            right = (left[0] + 1, left[1])
            if left[1] % 2:
                up = (left[0] + 1, left[1] + 1)
                down = (left[0] + 1, left[1] - 1)
            else:
                up = (left[0], left[1] + 1)
                down = (left[0], left[1] - 1)

            realleft = self.real_coord(left)
            realright = self.real_coord(right)
            realup = self.real_coord(up)
            realdown = self.real_coord(down)

            # upper triangle
            realcentral = central_point((realleft, realright, realup))
            vertexleft = self.hole_vertex(realleft, realcentral)
            vertexright = self.hole_vertex(realright, realcentral)
            vertexup = self.hole_vertex(realup, realcentral)

            if left in self.group:
                self.add_reference_point(left, (right, up), vertexleft)

            if right in self.group:
                self.add_reference_point(right, (left, up), vertexright)

            if up in self.group:
                self.add_reference_point(up, (left, right), vertexup)
            
            if left in self.group and right in self.group:
                self.add_line(vertexleft, vertexright)

            if left in self.group and up in self.group:
                self.add_line(vertexleft, vertexup)

            if up in self.group and right in self.group:
                self.add_line(vertexup, vertexright)

            if self.all_valid((left, right, up)):
                self.round_triangle(vertexleft, vertexup, vertexright)
                self.round_triangle(vertexup, vertexright, vertexleft)
                self.round_triangle(vertexright, vertexleft, vertexup)

            # lower triangle
            realcentral = central_point((realleft, realright, realdown))
            vertexleft = self.hole_vertex(realleft, realcentral)
            vertexright = self.hole_vertex(realright, realcentral)
            vertexdown = self.hole_vertex(realdown, realcentral)

            if left in self.group:
                self.add_reference_point(left, (right, down), vertexleft)

            if right in self.group:
                self.add_reference_point(right, (left, down), vertexright)

            if down in self.group:
                self.add_reference_point(down, (left, right), vertexdown)

            if left in self.group and right in self.group:
                self.add_line(vertexleft, vertexright)

            if left in self.group and down in self.group:
                self.add_line(vertexleft, vertexdown)

            if down in self.group and right in self.group:
                self.add_line(vertexdown, vertexright)

            if self.all_valid((left, right, down)):
                self.round_triangle(vertexleft, vertexright, vertexdown)
                self.round_triangle(vertexright, vertexdown, vertexleft)
                self.round_triangle(vertexdown, vertexleft, vertexright)

    def make_blinds(self):
        for node in self.group:
            for target in filter(lambda t: not t in self.group, self.all_vertex_edges(*node)):
                generator.close_blind(node, target)
                vector = (target[0] - node[0], target[1] - node[1])
                magnitude = math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])
                vector = (vector[0] / magnitude, vector[1] / magnitude)

                print(node, target)

groups=[
        {(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)},
]

generator = HexagonalGenerator('nikle.dxf', 19.5, 6)
generator.make_graph(groups[0])
generator.make_holes()
generator.make_blinds()
generator.print_graph()
generator.save()
