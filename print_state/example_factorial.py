#!/usr/bin/env python

from tracer import trace_me
from image_generator import create_image



@trace_me(tracefile="factorial.csv")
def factorial(n):

    result = 1

    while n:
        n -= 1
        result *= n

    return result

if __name__ == "__main__":
    factorial(3)
    create_image("factorial.csv")
