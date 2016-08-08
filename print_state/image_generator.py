#!/usr/bin/env python

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
        '<rect height="25" style="fill:#8e0;" width="25" x="25" y="50" />'
        '''
        return ET.tostring(self.to_svg_elem())

    def to_svg_elem(self):
        ''' Creates SVG element '''
        elem = ET.Element('rect', y=str(self.pos[1]), x=str(self.pos[0]),
                          width=str(self.width), height=str(self.height),
                          style="fill:"+rgb_to_hex((140,225,0))+";")
        return elem

class Transformation(object):

    height = int(MemoryField.height * 0.8)
    width  = 50

    arrowhead_define = ET.Element('marker', id='arrowhead',
                            orient='auto',
                            markerWidth='1',
                            markerHeight='2',
                            refX='0.1', refY='2')
    arrowhead_shape = ET.SubElement(arrowhead_define, 'path', d='M0,0 V4 L2,2 Z', fill='black')

    def __init__(self, pos, statement):
        self.pos = pos
        self.statement = statement.strip()

    @classmethod
    def defines(cls):
        return cls.arrowhead_define

    def to_svg_elems(self):

        group = ET.Element('g')

        x1, x2 = self.pos[0], self.pos[0]-self.width
        x3     = self.pos[0]-10
        y1, y2 = self.pos[1], self.pos[1]+self.height

        line_elem = ET.SubElement(group, 'path', **{'marker-end':'url(#arrowhead)',
                                'stroke-width':'5',
                                'fill':'none',
                                'stroke':'black',
                                'd':'M{x1},{y1} C{x2},{y1} {x2},{y2} {x3},{y2}'.format(**locals())})

        width_of_text = len(self.statement) * 6
        text_elem = ET.SubElement(group, 'text', x=str(x2-width_of_text), y=str(y1 + self.height/2),
                                  style="font-family:monospace;font-size:10px;")
        text_elem.text = self.statement

        return group

class ProgramStateHeader(object):


    def __init__(self, pos, fields):
        self.fields = fields
        self.pos = pos

    def to_svg_elems(self):

        group = ET.Element('g')

        for idx, field in enumerate(['line number'] + self.fields):

            y = self.pos[0] + (MemoryField.margin + 1 * MemoryField.width) * idx + MemoryField.width / 2
            x = self.pos[1] + 2* MemoryField.height
            text_elem = ET.SubElement(group, 'text', x=str(x), y=str(y),
                                      style="font-family:monospace;font-size:10px;",
                                      transform="rotate(-90)")
            text_elem.text = field

        return group


class ProgramState(object):


    def __init__(self, pos, fields, line_no, statement):
        self.fields = []

        self.pos = pos
        self.transformation = Transformation((pos[0] , pos[1] + MemoryField.height/2 * 1.1), statement)
        self.fields.append(MemoryField(pos[:], line_no))

        for idx, (field_name, field_value) in enumerate(fields.iteritems(), 1):
            mem_field = MemoryField((pos[0] + (MemoryField.margin + MemoryField.width) * idx, pos[1]), field_value)
            self.fields.append(mem_field)

    def to_svg(self):
        ''' Writes SVG elements
        >>> ProgramState([10,20], {'a':12, 'b':13, 'c':14}).to_svg()
        '<rect height="25" style="fill:#8e0;" width="25" x="10" y="20" />\\n<rect height="25" style="fill:#8e0;" width="25" x="40" y="20" />\\n<rect height="25" style="fill:#8e0;" width="25" x="70" y="20" />'
        '''

        result  = []

        for field in self.fields:
            result.append(field.to_svg())

        return "\n".join(result)

    def to_svg_elems(self):
        ''' Writes SVG elements '''

        return [field.to_svg_elem() for field in self.fields] + [self.transformation.to_svg_elems()]

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
        defines = ET.SubElement(svg_root, 'defs')

        defines.append(Transformation.defines())
        drawing = ET.SubElement(svg_root, 'g', style="fill-opacity:1.0; stroke:black;")

        for child in self.children:
            for children in child.to_svg_elems():
                drawing.append(children)

        return ET.tostring(svg_root)

import csv
def create_image(path):

    with open(path) as csvfile:
        reader = csv.DictReader(csvfile)

        drawing = SVGdrawing()
        offset = MemoryField.height + MemoryField.margin


        for idx, row in enumerate(reader):

            statement = row.pop('line')
            line_no = row.pop('lineno')

            if idx == 0:
                drawing.children = [ProgramStateHeader((MemoryField.margin, -40), row.keys())]

            drawing.children += [ProgramState((MemoryField.margin, offset*idx + MemoryField.margin), row, line_no, statement)]

                

        drawing.height = len(drawing.children) * offset + MemoryField.margin
        drawing.width = len(drawing.children[-1].fields) * (MemoryField.width + MemoryField.margin) + MemoryField.margin

        with open(path+'.svg','w') as svgfile:
            svgfile.write(drawing.to_svg())


if __name__ == "__main__":
    import doctest
    doctest.testmod()
