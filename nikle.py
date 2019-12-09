#!/usr/bin/python

from dxfwrite import DXFEngine as dxf
import math

rowcount=5
columncount=20
groups=[
    {0, 1, 2, 3, 4, 5, 6, 7},
    {8, 9, 10, 11, 12, 13, 14, 15},
]

cellspace=20
cellradius=6
connwidth=4

connangle=math.degrees(math.asin(connwidth/2/cellradius))
connmap={}

def cell_position(cellno):
    column=int(cellno/rowcount)
    row=cellno%rowcount
    x=cellspace*(column+(row%2)/2)
    y=row*cellspace*math.sqrt(3)/2
    return (x, y)

def neighbours(cellno, group):
    array=[]
    row=cellno%rowcount
    if row%2==0:
        if row<(rowcount-1):
            array.append(cellno+1)
        if row>0:
            array.append(cellno-1)
    else:
        if row<(rowcount-1):
            array.append(cellno+1+rowcount)
        if row>0:
            array.append(cellno-1+rowcount)
    array.append(cellno+rowcount)
    return list(filter(lambda cellno: cellno in group, array))

drawing = dxf.drawing('test.dxf')

def connect_cells(first, second):
    fx,fy=cell_position(first)
    sx,sy=cell_position(second)
    vecx=sx-fx
    vecy=sy-fy
    magn=math.sqrt(vecx*vecx+vecy*vecy)
    vecx/=magn
    vecy/=magn
    if sy>fy:
        angle=300
    elif sy<fy:
        angle=60
    else:
        angle=0
    radangle=math.radians(angle)
    offx=math.sin(radangle)*connwidth/2
    offy=math.cos(radangle)*connwidth/2

    cut=math.cos(math.radians(connangle))
    cut=cut*cellradius

    fx+=vecx*cut
    sx-=vecx*cut
    fy+=vecy*cut
    sy-=vecy*cut

    start=fx+offx,fy+offy
    end=sx+offx,sy+offy
    drawing.add(dxf.line(start, end))

    start=fx-offx,fy-offy
    end=sx-offx,sy-offy
    drawing.add(dxf.line(start, end))

    if not first in connmap:
        connmap[first]=[]
    if not second in connmap:
        connmap[second]=[]

    connmap[first].append(angle)
    connmap[second].append((angle + 180) % 360)

def make_blind(cellno,angle):
    start=angle+connangle+300+connangle
    end=start+connangle*2
    center=cell_position(cellno)
    drawing.add(dxf.arc(cellradius, center, -end, -start))
    print("need blind: ", angle)

def draw_group(group):
    for cellno in group:
        for i in range(0, 6):
            start=i*60+connangle
            end=start+60-connangle*2
            center=cell_position(cellno)
            drawing.add(dxf.arc(cellradius, center, start, end))
        for neigh in neighbours(cellno, group):
            print("{} -> {}".format(cellno, neigh))
            connect_cells(cellno, neigh)

    for cellno in group:
        print("cell: ", cellno)
        for angle in range(0, 360, 60):
            if not angle in connmap[cellno]:
                make_blind(cellno, angle)

for group in groups:
    print("group: {}".format(group))
    draw_group(group)

drawing.save()
