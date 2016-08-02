#!/usr/bin/env python

import sys
import linecache
from types import ModuleType, FunctionType, ClassType, TypeType

__tracements__ = []

def traceit(frame, event, arg):
    if event == "line":

        line_globals = {k:v for k,v in frame.f_globals.items() if not (k.startswith('__')
                                                                       or isinstance(v, ModuleType)
                                                                       or isinstance(v, FunctionType)
                                                                       or isinstance(v, ClassType)
                                                                       or isinstance(v, TypeType)
                                                                       or k.endswith('Type'))}
        line_locals = {k:v for k,v in frame.f_locals.items() if not k.startswith('__')}
        lineno = frame.f_lineno
        filename = frame.f_globals["__file__"]
        if (filename.endswith(".pyc") or
            filename.endswith(".pyo")):
            filename = filename[:-1]
        name = frame.f_globals["__name__"]
        line = linecache.getline(filename, lineno)

        global __tracements__
        __tracements__ += ["State: {line_globals} {line_locals}".format(**locals())]
        __tracements__ += ["Transformation @line{lineno}:{line}".format(**locals())]

    return traceit

#----- Wrapper
from functools import wraps
def trace_me(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        sys.settrace(traceit)
        result = f(*args, **kwargs)
        sys.settrace(None)
        print "\n".join(__tracements__)
        return result
    return wrapped

#----- SVG generation
import xml.etree.cElementTree as ET
import doctest

def rgb_to_hex(rgb): return "#%x%x%x" % (rgb[0]/16,rgb[1]/16,rgb[2]/16)

class MemoryField(object):

    width = 25
    height = 25
    margin = 5

    def __init__(self, pos, text ):
        self.text = text
        self.pos = pos

    def to_svg(self):
        ''' Writes SVG element
        >>> MemoryField(pos=(25,50), text='bla').to_svg()
        '<rect height="25" style="fill:#663;" width="25" x="25" y="50" />'
        '''
        elem = ET.Element('rect', y=str(self.pos[1]), x=str(self.pos[0]),
                          width=str(self.width), height=str(self.height),
                          style="fill:"+rgb_to_hex((100,100,50))+";")

        return ET.tostring(elem)

class ProgramState(object):

    fields = {}

    def __init__(self, pos, fields):

        self.pos = pos

        for idx, field in enumerate(fields.keys()):

            pos[0] = pos[0] + (MemoryField.margin + MemoryField.width) * idx
            self.fields[field] = MemoryField(pos[:], fields[field])

    def to_svg(self):
        ''' Writes SVG elements
        >>> ProgramState([10,20], {'a':12, 'b':13}).to_svg()
        '<rect height="25" style="fill:#663;" width="25" x="10" y="20" />\\n<rect height="25" style="fill:#663;" width="25" x="40" y="20" />'
        '''

        result  = []

        for fieldname, field in self.fields.items():
            result.append(field.to_svg())

        return "\n".join(result)

class SVGdrawing(object):

    height= 500
    width = 500

    children = []

    def to_svg(self):
        ''' Writes SVG elements
        >>> SVGdrawing().to_svg()
        '<svg height="500" width="500"><g style="fill-opacity:1.0; stroke:black;" /></svg>'
        '''
        svg_root = ET.Element('svg',
                       height=str(self.height),
                      width=str(self.width))
        drawing = ET.SubElement(svg_root, 'g', style="fill-opacity:1.0; stroke:black;")

        for child in self.children:
            drawing.append(child)

        return ET.tostring(svg_root)

#----- Code to trace
@trace_me
def bubblesort(sortme):
    offset = 1

    while True:
        swapped = False
        for i in range(len(sortme)-offset):
            if sortme[i] > sortme[i+1]:
                sortme[i], sortme[i+1] = sortme[i+1], sortme[i]
                swapped = True
        offset += 1

        if not swapped:
            return sortme
@trace_me
def find_max(num1, num2, num3):

    max_num = 0

    if num1 > num2 and num1 > num3:
        max_num = num1

    elif num2 > num1 and num2 > num3:
        max_num = num2

    elif num3 > num1 and num3 > num2:
        max_num = num3

    return max_num

if __name__ == "__main__":
    #import doctest
    #doctest.testmod()
    bubblesort([3,2,1])
    find_max(3,2,1)
