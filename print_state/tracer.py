#!/usr/bin/env python

import sys
import linecache
from types import ModuleType, FunctionType
import csv

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
        __tracements__ += [dict(line_globals.items() + line_locals.items() + {'lineno':lineno, 'line':line}.items())]

    return traceit

#----- Wrapper
from functools import wraps

def trace_me(tracefile='tracefile', image=True):
    def trace_decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):

            global __tracements__

            sys.settrace(traceit)
            result = func(*args, **kwargs)
            sys.settrace(None)

            with open(tracefile, 'w') as output:

                writer = csv.DictWriter(output, fieldnames=__tracements__[-1].keys())
                writer.writeheader()
                for tracement in __tracements__:
                    writer.writerow(tracement)

            __tracements__ = []

            return result
        return wrapped
    return trace_decorator

if __name__ == "__main__":
    import doctest
    doctest.testmod()
