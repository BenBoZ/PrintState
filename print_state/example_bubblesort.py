#!/usr/bin/env python

from tracer import trace_me
from image_generator import create_image



@trace_me(tracefile="bub.csv")
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

if __name__ == "__main__":
    bubblesort([7,8,3])
    create_image("bub.csv")
