#!/usr/bin/env python

import sys
import linecache
from types import ModuleType, FunctionType

__tracements__ = []

def traceit(frame, event, arg):
    if event == "line":

        line_globals = {k:v for k,v in frame.f_globals.items() if not (k.startswith('__')
                                                                       or isinstance(v, ModuleType)
                                                                       or isinstance(v, FunctionType)
                                                                       or isinstance(v, type)
                                                                       or k.endswith('Type'))}
        line_locals = {k:v for k,v in frame.f_locals.items() if not k.startswith('__')}
        lineno = frame.f_lineno
        filename = frame.f_globals["__file__"]
        if (filename.endswith(".pyc") or
            filename.endswith(".pyo")):
            filename = filename[:-1]
        name = frame.f_globals["__name__"]
        line = linecache.getline(filename, lineno).strip()

        global __tracements__
        __tracements__ += ["State: {line_globals} {line_locals}".format(**locals())]
        __tracements__ += ["Transformation @line{lineno}:{line}".format(**locals())]

    return traceit

#----- Wrapper
from functools import wraps

def trace_me(tracefile='tracefile'):
    def trace_decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            sys.settrace(traceit)
            result = func(*args, **kwargs)
            sys.settrace(None)

            with open(tracefile, 'w') as output:
                for tracement in __tracements__:
                    output.write("{tracement}\n".format(**locals()))

            return result
        return wrapped
    return trace_decorator

if __name__ == "__main__":
    import doctest
    doctest.testmod()
