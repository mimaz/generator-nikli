#!/usr/bin/python

##
 # 2019 Mieszko Mazurek <mimaz@gmx.com>
 ##

import generator as gen

reention_70_14s=[
        [(0, 1), (0, 2), (0, 3), (1, 0), (2, 0)],
        [(1, 1), (1, 2), (1, 3), (2, 4), (3, 4)],
        [(2, 1), (2, 2), (2, 3), (3, 0), (3, 2)],
        [(4, 0), (3, 1), (4, 2), (3, 3), (4, 4)],
        [(5, 0), (4, 1), (5, 2), (4, 3), (5, 4)],
        [(6, 0), (5, 1), (6, 2), (5, 3), (6, 4)],
        [(7, 0), (6, 1), (7, 2), (6, 3), (7, 4)],
        [(8, 0), (7, 1), (8, 2), (7, 3), (8, 4)],
        [(9, 0), (8, 1), (9, 2), (8, 3), (9, 4)],
        [(10, 0), (9, 1), (10, 2), (9, 3), (10, 4)],
        [(11, 0), (10, 1), (11, 2), (10, 3), (11, 4)],
        [(12, 0), (11, 1), (12, 1), (12, 2), (11, 3)],
        [(13, 1), (13, 2), (12, 3), (12, 4), (14, 2)],
        [(14, 1), (15, 2), (14, 3), (13, 3), (13, 4)],
]

reention_56_14s=[
        [(0, 1), (0, 2), (0, 3), (1, 2)],
        [(1, 1), (2, 2), (1, 3), (2, 1)],
        [(2, 3), (3, 2), (3, 1), (4, 0)],
        [(3, 3), (4, 2), (4, 1), (5, 0)],
        [(4, 3), (5, 2), (5, 1), (6, 0)],
        [(5, 3), (6, 2), (6, 1), (7, 0)],
        [(6, 3), (7, 2), (7, 1), (8, 0)],
        [(7, 3), (8, 2), (8, 1), (9, 0)],
        [(8, 3), (9, 2), (9, 1), (10, 0)],
        [(9, 3), (10, 2), (10, 1), (11, 0)],
        [(10, 3), (11, 2), (11, 1), (12, 0)],
        [(11, 3), (12, 2), (12, 1), (13, 0)],
        [(12, 3), (13, 2), (13, 1), (14, 0)],
        [(14, 1), (14, 2), (13, 3), (15, 2)],
]

test_14s1p=[
        [(0, 0)],
        [(1, 0)],
        [(2, 0)],
        [(3, 0)],
        [(4, 0)],
        [(5, 0)],
        [(6, 0)],
        [(7, 0)],
        [(8, 0)],
        [(9, 0)],
        [(10, 0)],
        [(11, 0)],
        [(12, 0)],
        [(13, 0)],
]

distance = 18
width = 5
radius = 1
margin = 1

def count_rows(mapping):
    low = 0
    up = 0
    for group in mapping:
        for pair in group:
            low = min(low, pair[1])
            up = max(up, pair[1])
    return up - low + 1

def draw_battery(mapping, filename):
    rows = count_rows(mapping)
    generator = gen.HexagonalGenerator(distance, width, radius, rows, margin)
    for group in gen.Group.generate_list(mapping):
        generator.load_group(group)
        generator.draw_group()
        generator.draw_dilatation(4, 0)
    generator.draw_dxf(filename)

draw_battery(reention_70_14s, 'reention_70_14s.dxf')
draw_battery(reention_56_14s, 'reention_56_14s.dxf')
draw_battery(test_14s1p, 'test_14s1p.dxf')
