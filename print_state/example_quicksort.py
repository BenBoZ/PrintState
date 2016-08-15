#!/usr/bin/env python

from tracer import trace_me
from image_generator import create_image

@trace_me(tracefile="quicksort.csv")
def quicksort(sortme):
    less = []
    equal = []
    greater = []

    if len(sortme) > 1:
        pivot = sortme[0]
        for x in sortme:
            if x < pivot:
                less.append(x)
            if x == pivot:
                equal.append(x)
            if x > pivot:
                greater.append(x)
        return quicksort(less)+equal+quicksort(greater)
    else:
        return sortme


if __name__ == "__main__":
    quicksort([7,3,5])
    create_image("quicksort.csv")
