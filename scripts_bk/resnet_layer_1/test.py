import os
from matplotlib import pyplot
from numpy import arange
import bisect
from decimal import *
import numpy
import math
from scipy import stats as scistats
import csv
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from scipy.ndimage.filters import correlate as convolveim
import copy
from HuffmanCoding_weights import HuffmanCoding
from bitstring import Bits

def bindigits(n, bits):
    s = bin(n & int("1"*bits, 2))[2:]
    return ("{0:0>%s}" % (bits)).format(s)
ia = numpy.zeros((10, 5), dtype=numpy.int)

row_cnt = 0
col_cnt = 0
ic_cnt = 0
oc_cnt = 0
with open("1_50_input.txt") as ia_file:
    for line in ia_file:
        split_line = line.split(",")
        single_ia = Bits(bin=(''.join(map(str, split_line))))
        #print(single_ia.int)
        ia[row_cnt][col_cnt] = single_ia.int
        row_cnt = row_cnt + 1
        if(row_cnt == 10):
            row_cnt = 0
            col_cnt = col_cnt + 1
        if(col_cnt == 5):
            col_cnt = 0

ia_golden = open('ia.txt','w+') 
for row in range (0, 10):
    for col in range (0, 5):
        ia_golden.write(str(format(ia[row][col], '4d')) + '\t')
    ia_golden.write('\n')

ia_golden.close()


