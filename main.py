#!/usr/bin/python

from . import Generator

groups=[
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

distance = 19.5
width = 6
radius = 1
filename = 'nikle.dxf'

generator = HexagonalGenerator(distance, width, radius)

for group in Group.generate_list(groups):
    generator.load_group(group)
    generator.draw_holes()
    generator.draw_corners()

generator.draw_dxf(filename)