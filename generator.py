#!/usr/bin/python

from dxfwrite import DXFEngine as dxf
import math
import subprocess

class Generator:
    def __init__(self, filename, scalex, scaley, offx):
        self.conn_width = 5
        self.odd_offset_x = offx
        self.scale_x = scalex
        self.scale_y = scaley
        self.graph = {}
        self.group = {}
        self.holes = {}
        self.drawing = dxf.drawing(filename)

    def save(self):
        self.drawing.save()

    def add_line(self, start, end):
        self.drawing.add(dxf.line(start, end))
        print("add_line ", start, end)

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
            for conn in filter(lambda c: c in group, self.all_vertex_edges(*vertex)):
                graph[vertex][conn] = True
        self.graph = graph
        self.group = group
        self.left_column = left_column
        self.right_column = right_column
        self.bottom_row = bottom_row
        self.top_row = top_row

    def central_point(self, pointlist):
        x = 0
        y = 0
        for point in pointlist:
            x += point[0]
            y += point[1]
        return (x / len(pointlist), y / len(pointlist))

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
        super(HexagonalGenerator, self).__init__(filename, scale, scale * math.sqrt(3) / 2, 0.5)

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
        magnitude = math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])
        vector = (vector[0] / magnitude, vector[1] / magnitude)
        shift = self.conn_width
        return (point[0] + vector[0] * shift, point[1] + vector[1] * shift)

    def make_holes(self):
        left_row_range = range(self.bottom_row, self.top_row + 1)
        nodes = [*self.group, *map(lambda r: (self.left_column - 1, r), left_row_range)]
        for left in nodes:
            print("node: ", left)
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

            realcentral = self.central_point((realleft, realright, realup))
            vertexleft = self.hole_vertex(realleft, realcentral)
            vertexright = self.hole_vertex(realright, realcentral)
            vertexup = self.hole_vertex(realup, realcentral)
            
            if left in self.group and right in self.group:
                self.add_line(vertexleft, vertexright)

            if left in self.group and up in self.group:
                self.add_line(vertexleft, vertexup)

            if up in self.group and right in self.group:
                self.add_line(vertexup, vertexright)

            realcentral = self.central_point((realleft, realright, realdown))
            vertexleft = self.hole_vertex(realleft, realcentral)
            vertexright = self.hole_vertex(realright, realcentral)
            vertexdown = self.hole_vertex(realdown, realcentral)
                
            if left in self.group and right in self.group:
                self.add_line(vertexleft, vertexright)

            if left in self.group and down in self.group:
                self.add_line(vertexleft, vertexdown)

            if down in self.group and right in self.group:
                self.add_line(vertexdown, vertexright)

    def make_blinds(self):
        for node in self.group:
            for target in filter(lambda t: not t in self.group, self.all_vertex_edges(*node)):
                vector = (target[0] - node[0], target[1] - node[1])
                magnitude = math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])
                vector = (vector[0] / magnitude, vector[1] / magnitude)

                self.add_line(self.real_coord(node), self.real_coord(target))
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
