#!/usr/bin/env python

from tracer import trace_me
from image_generator import create_image

@trace_me(tracefile="max.csv")
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
    find_max(3,3,5)
    create_image("max.csv")
