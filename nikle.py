#!/usr/bin/python

from dxfwrite import DXFEngine as dxf
import subprocess
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

connangle=2*math.degrees(math.asin(connwidth/2/cellradius))
connmap={}

def coord_position(column, row):
    x=cellspace*(column+(row%2)/2)
    y=row*cellspace*math.sqrt(3)/2
    return (x, y)

def cell_position(cellno):
    column=int(cellno/rowcount)
    row=cellno%rowcount
    return coord_position(column, row)

def neighbours(cellno):
    array=[]
    row=cellno%rowcount
    if row%2==0:
        if row<(rowcount-1):
            array.append(cellno-rowcount+1)
        if row>0:
            array.append(cellno-rowcount-1)
    else:
        if row<(rowcount-1):
            array.append(cellno+rowcount+1)
        if row>0:
            array.append(cellno+rowcount-1)
    if row>0:
        array.append(cellno-1)
    if row<(rowcount-1):
        array.append(cellno+1)
    array.append(cellno+rowcount)
    array.append(cellno-rowcount)
    return list(filter(lambda c: c>=0, array))

drawing = dxf.drawing('test.dxf')

def connect_cells(first, second):
    if not first in connmap:
        connmap[first]={}
    if not second in connmap:
        connmap[second]={}

    connmap[first][second]=None
    connmap[second][first]=None

    fx,fy=cell_position(first)
    sx,sy=cell_position(second)
    vecx=sx-fx
    vecy=sy-fy
    if vecx<0:
        return
    magn=math.sqrt(vecx*vecx+vecy*vecy)
    vecx/=magn
    vecy/=magn
    if sy>fy:
        angle=60
    elif sy<fy:
        angle=300
    else:
        angle=0
    radangle=math.radians(angle)
    offx=math.sin(-radangle)*connwidth/2
    offy=math.cos(radangle)*connwidth/2

    cut=math.cos(math.radians(connangle/2))
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


print("connangle: ", connangle)
def make_blind(cellno,target):
    if target in connmap[cellno]:
        return
    fx,fy=cell_position(cellno)
    sx,sy=cell_position(target)
    horz=sx-fx
    vert=sy-fy
    magn=math.sqrt(horz*horz+vert*vert)
    eps=0.0001
    if horz>eps and vert>eps:
        angle=60
    elif horz<-eps and vert>eps:
        angle=120
    elif horz<-eps and vert<-eps:
        angle=240
    elif horz>eps and vert<-eps:
        angle=300
    elif horz<-eps and vert<eps and vert>-eps:
        print("180 ", cellno, target)
        angle=180
    else:
        angle=0

    start=angle-connangle/2
    end=start+connangle
    center=cell_position(cellno)
    drawing.add(dxf.arc(cellradius, center, start, end))

def draw_group(group):
    for cellno in group:
        neigh=neighbours(cellno)
        for target in neigh:
            if target in group:
                connect_cells(cellno, target)
        for target in neigh:
            make_blind(cellno, target)

for group in groups:
    draw_group(group)

drawing.save()
