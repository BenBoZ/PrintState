#!/usr/bin/env python

import xml.etree.cElementTree as ET
import doctest
import ast
import code
from copy import deepcopy

def rgb_to_hex(rgb): return "#%x%x%x" % (rgb[0]/16,rgb[1]/16,rgb[2]/16)
PURPLE="rgb(210,0,159)"
GREEN="rgb(159,210,0)"

class MemoryField(object):

    width = 75
    height = 25
    margin = 5

    grad_green = ET.Element('linearGradient', id="grad_green", x1="0%", y1="0%", x2="0%", y2="100%")
    _stop1 = ET.SubElement(grad_green, 'stop', offset="0%", style="stop-color:rgb(224,255,129);stop-opacity:1")
    _stop2 = ET.SubElement(grad_green, 'stop', offset="100%", style="stop-color:rgb(176,242,0);stop-opacity:1")

    drop_shade_filter = ET.Element('filter', id='drop_shade_filter', x='0', y='0', width='200%', height='200%')
    _dropshadeOffset  = ET.SubElement(drop_shade_filter, 'feOffset', result='offOut', **{'in':'SourceAlpha', 'dx':'3', 'dy':'3'})
    _dropshadeBlur    = ET.SubElement(drop_shade_filter, 'feGaussianBlur', result='blurOut', **{'in':'offOut', 'stdDeviation':'5'})
    _dropshadeBlend   = ET.SubElement(drop_shade_filter, 'feBlend', **{'in':'SourceGraphic', 'in2':'blurOut', 'mode':'normal'})

    def __init__(self, pos, text ):
        self.text = text
        self.pos = pos
        self.is_input = False

    @classmethod
    def defines(cls):
        return  [cls.grad_green, cls.drop_shade_filter]

    def to_svg(self):
        ''' Writes SVG element
        >>> MemoryField(pos=(25,50), text='bla').to_svg()
        '<rect height="25" style="fill:#8e0;" width="25" x="25" y="50" />'
        '''
        return ET.tostring(self.to_svg_elem())

    def to_svg_elem(self):
        ''' Creates SVG element '''
        group = ET.Element('g')

        if self.is_input:
            color = PURPLE
        else:
            color = GREEN

        elem = ET.SubElement(group, 'rect', y=str(self.pos[1]), x=str(self.pos[0]),
                          width=str(self.width), height=str(self.height),
                          style="fill:url(#grad_green)", filter='url(#drop_shade_filter)', stroke=color)

        text_elem = ET.SubElement(group, 'text', x=str(self.pos[0]+self.width/2), y=str(self.pos[1] + 5 + self.height/2),
                                  style="font-family:monospace;font-size:10px;text-anchor:middle;")
        text_elem.text = self.text
        return group


class ProgramStateHeader(object):


    fontsize = 10

    def __init__(self, pos, fields):
        self.fields = fields
        self.pos = pos

    def to_svg_elems(self):

        group = ET.Element('g')

        for idx, field in enumerate(['line number'] + list(self.fields)):

            y = self.pos[0] + (MemoryField.margin + 1 * MemoryField.width) * idx + MemoryField.width / 2
            x = self.pos[1] + 2* MemoryField.height
            text_elem = ET.SubElement(group, 'text', x=str(x), y=str(y),
                                      style="font-family:monospace;font-size:{size}px;".format(size=self.fontsize),
                                      transform="rotate(-90)")
            text_elem.text = field

        return group

class IOFinder(ast.NodeVisitor):

    def __init__(self):
        super(IOFinder,self).__init__()
        self.inputs = []
        self.outputs = []

        self._input_mode = False
        self._output_mode = False

    def make_unique(self):

        self.inputs = list(set(self.inputs))
        self.outputs = list(set(self.outputs))

    def _visit_input(self, node):
        self._input_mode = True
        self.visit(node)
        self._input_mode = False

    def _visit_inputs(self, nodes):
        for node in nodes:
            if node:
                self._visit_input(node)

    def _visit_output(self, node):
        self._output_mode = True
        self.visit(node)
        self._output_mode = False

    def _visit_outputs(self, nodes):
        for node in nodes:
            self._visit_output(node)

    def visit_comprehension(self, node):
        self._visit_inputs([node.iter, node.ifs])
        self._visit_output(node.target)

    def visit_Expr(self, node):
        with enabled(self._input_mode):
            self.generic_visit(node)

    def visit_Return(self, node):
        self._visit_input(node.value)
        self._visit_output(node.value)

    def visit_Assign(self, node):
        self._visit_outputs(node.targets)
        self._visit_input(node.value)

    def visit_AugAssign(self, node):
        self._visit_output(node.target)
        self._visit_input(node.value)

    def visit_BinOp(self, node):
        self._visit_input(node.right)
        self._visit_input(node.left)

    def visit_UnaryOp(self, node):
        self._visit_input(node.operand)

    def visit_BoolOp(self, node):
        self._visit_inputs(node.values)

    def visit_Name(self, node):
        if self._input_mode and node.id not in ['True','False']:
            self.inputs += [node.id]
        if self._output_mode:
            self.outputs += [node.id]

    def visit_Subscript(self, node):

        self.visit(node.value)

        old_output_mode = deepcopy(self._output_mode)
        old_input_mode = deepcopy(self._input_mode)
        self._output_mode = False
        self._input_mode = True
        self.visit(node.slice)
        self._output_mode = old_output_mode
        self._input_mode = old_input_mode

    def visit_Compare(self, node):
        self._visit_inputs([node.left] + node.comparators)

    def visit_Call(self, node):
        self._visit_inputs(node.args + node.keywords)

    def _control_flow(self,node):
        self.outputs += ['line_number']
        self.generic_visit(node)

    def visit_If(self, node):
        self._visit_input(node.test)
        self._visit_inputs(node.orelse)
        self.outputs += ['line_number']

    def visit_For(self, node):
        self._visit_output(node.target)
        self._visit_input(node.iter)
        self._visit_inputs(node.orelse)

        self.outputs += ['line_number']

    def visit_While(self, node):
        self._visit_input(node.test)
        self._visit_inputs(node.orelse)
        self.outputs += ['line_number']

    def visit_Break(self, node):
        self._control_flow(node)

    def visit_Try(self, node):
        self._control_flow(node)

    def visit_TryFinally(self, node):
        self._control_flow(node)

    def visit_ExceptHandler(self, node):
        self._control_flow(node)

    def visit_With(self, node):
        self._control_flow(node)

    def visit_withitem(self, node):
        self._control_flow(node)

class ProgramState(object):

    margin = 4 * MemoryField.margin

    def __init__(self, pos, fields, line_no, statement):
        self.fields = []

        self.pos = pos
        self.transformation = Transformation((pos[0] , pos[1] + MemoryField.height/2 * 1.1), statement)
        self.fields.append(MemoryField(pos[:], line_no))
        (inputs, outputs) = self.parse_statement(statement)

        positions = {'line_number':self.fields[0].pos}
        for idx, (field_name, field_value) in enumerate(fields.items(), 1):
            mem_field = MemoryField((pos[0] + (MemoryField.margin + MemoryField.width) * idx, pos[1]), field_value)
            self.fields.append(mem_field)
            positions[field_name] = mem_field.pos
            if field_name in inputs:
                mem_field.is_input = True

        for output_field in outputs:
            input_field = None
            for input_field in inputs:
                self.add_arrow_from_field_to_field(input_field, output_field, mem_field, positions)
            if not input_field:
                self.add_arrow_from_field_to_field(output_field, output_field, mem_field, positions)

    def add_arrow_from_field_to_field(self, from_name, to_name, mem_field, positions):

        x1 = positions[from_name][0] + mem_field.width/2
        y1 = positions[from_name][1] + mem_field.height
        x2 = positions[to_name][0] + mem_field.width/2
        y2 = positions[to_name][1] + mem_field.height + 0.75 * ProgramState.margin
        arrow = Effect((x1,y1), (x2, y2))
        self.fields.append(arrow)

    def parse_statement(self, orig_statement):

        # See if it is valid python
        try:
            if code.compile_command(orig_statement):
                statement = orig_statement
            else:
                statement = orig_statement + ' pass'
        except SyntaxError as e:
            try:
                statement = 'if True: pass\n' + orig_statement
                if not code.compile_command(statement):
                    statement = statement + ' pass'
            except SyntaxError as e:
                #print( "Parsing %s failed" % statement)
                statement = orig_statement

        tree = ast.parse(statement)

        io = IOFinder()
        io.visit(tree)
        io.make_unique()

        return (io.inputs, io.outputs)


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

    x = 0
    y = 0

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

        for define in MemoryField.defines():
            defines.append(define)

        drawing = ET.SubElement(svg_root, 'g', style="fill-opacity:1.0; stroke:black;")


        min_coordinates = [0, 0]
        for child in self.children:
            for children in child.to_svg_elems():
                drawing.append(children)
                for node in children.findall(".//*[@x]"):
                    min_coordinates[0] = min(int(round(float(node.get('x')))), min_coordinates[0])
                    min_coordinates[1] = min(int(round(float(node.get('y')))), min_coordinates[1])

        x_offset = abs(min_coordinates[0]) + 50
        y_offset = abs(min_coordinates[1]) + 50

        svg_root.set('width', str(x_offset + self.width))
        svg_root.set('height', str(y_offset + self.height))

        drawing.set('transform', "translate({x_offset} {y_offset})".format(**locals()))

        return ET.tostring(svg_root)

class Arrow(object):

    arrowhead_define = ET.Element('marker', id='arrowhead',
                            orient='auto',
                            markerWidth='1',
                            markerHeight='2',
                            refX='0.1', refY='2')
    arrowhead_shape = ET.SubElement(arrowhead_define, 'path', d='M0,0 V4 L2,2 Z', fill='black')

    @classmethod
    def defines(cls):
        return cls.arrowhead_define

class Transformation(Arrow):

    height = int(ProgramState.margin + 3 * MemoryField.margin)
    width  = 50

    def __init__(self, pos, statement):
        self.pos = pos
        self.statement = statement.strip()

    def to_svg_elems(self):

        group = ET.Element('g')

        x1, x2 = self.pos[0], self.pos[0]-self.width
        x3     = self.pos[0]-10
        y1, y2 = self.pos[1], self.pos[1]+self.height

        line_elem = ET.SubElement(group, 'path', **{'marker-end':'url(#arrowhead)',
                                'stroke-width':'3',
                                'fill':'none',
                                'stroke':'black',
                                'd':'M{x1},{y1} C{x2},{y1} {x2},{y2} {x3},{y2}'.format(**locals())})

        width_of_text = len(self.statement) * 6
        text_elem = ET.SubElement(group, 'text', x=str(x2-width_of_text), y=str(y1 + self.height/2),
                                  style="font-family:monospace;font-size:10px;")
        text_elem.text = self.statement

        return group

class Effect(Arrow):
    def __init__(self, from_pos, to_pos):
        self.from_pos = from_pos
        self.to_pos = to_pos

    def to_svg_elem(self):

        x1, x2 = self.from_pos[0], self.to_pos[0]
        y1, y2 = self.from_pos[1], self.to_pos[1]

        line_elem = ET.Element('path', **{'marker-end':'url(#arrowhead)',
                               'stroke-width':'3',
                               'fill':'none',
                               'stroke':PURPLE,
                               'd':'M{x1},{y1} C{x1},{y2} {x2},{y1} {x2},{y2}'.format(**locals())})

        return line_elem

import csv
def create_image(path):

    with open(path) as csvfile:
        reader = csv.DictReader(csvfile)

        drawing = SVGdrawing()
        offset = MemoryField.height + ProgramState.margin


        for idx, row in enumerate(reader):

            statement = row.pop('line')
            line_no = row.pop('lineno')

            if idx == 0:
                drawing.children = [ProgramStateHeader((MemoryField.margin, -40), row.keys())]

            drawing.children += [ProgramState((MemoryField.margin, offset*idx + MemoryField.margin), row, line_no, statement)]



        drawing.height = len(drawing.children) * offset + MemoryField.margin
        drawing.width = len(drawing.children[-1].fields) * (MemoryField.width + MemoryField.margin) + MemoryField.margin

        drawing.x = 1000
        drawing.y = 1000

        with open(path+'.svg','wb') as svgfile:
            svgfile.write(drawing.to_svg())


if __name__ == "__main__":
    import doctest
    doctest.testmod()
