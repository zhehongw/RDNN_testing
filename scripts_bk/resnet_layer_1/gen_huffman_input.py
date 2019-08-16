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

numpy.random.seed(9001)

num_pe = 1
ic = 8 
ic_total = 8 
oc = 64 
oc_total = 64
stride = 2
kernel_size = 7 
output_kernel_size = 3
ia_size = 230 
oa_size = (ia_size - kernel_size + 1)/(stride) + output_kernel_size - 1
write_ia_num = 0
write_oa_num = 1
rram_banks = 8 
right_shift = 11 
ia_ram_banks = 4
pe_ic = 8
pe_oc = 8

sparse_w = numpy.zeros((oc_total, ic_total, kernel_size, kernel_size), dtype=numpy.int) 

row_cnt = 0
col_cnt = 0
ic_cnt = 0
oc_cnt = 0
with open("1_conv_weight.txt") as weight_file:
    for line in weight_file:
        split_line = line.split(",")
        single_weight = Bits(bin=(''.join(map(str, split_line))))
        sparse_w[oc_cnt][ic_cnt][row_cnt][col_cnt] = single_weight.int
        row_cnt = row_cnt + 1
        if(row_cnt == kernel_size):
            row_cnt = 0
            col_cnt = col_cnt + 1
        if(col_cnt == kernel_size):
            col_cnt = 0
            ic_cnt = ic_cnt + 1
        if(ic_cnt == 4 ):
            ic_cnt = 0
            oc_cnt = oc_cnt + 1
        if(oc_cnt == oc_total):
            oc_cnt = 0

print("density: " + str(float(numpy.count_nonzero(sparse_w))/float(ic_total*oc_total*kernel_size*kernel_size)))

ia = numpy.zeros((ic_total, ia_size, ia_size), dtype=numpy.int)

row_cnt = 0
col_cnt = 0
ic_cnt = 0
oc_cnt = 0
with open("1_input.txt") as ia_file:
    for line in ia_file:
        split_line = line.split(",")
        single_ia = Bits(bin=(''.join(map(str, split_line))))
        ia[ic_cnt][row_cnt + (kernel_size-1)/2][col_cnt + (kernel_size-1)/2] = single_ia.int
        row_cnt = row_cnt + 1
        if(row_cnt == ia_size - kernel_size + 1):
            row_cnt = 0
            col_cnt = col_cnt + 1
        if(col_cnt == ia_size - kernel_size + 1):
            col_cnt = 0
            ic_cnt = ic_cnt + 1
        if(ic_cnt == ic_total):
            ic_cnt = 0

for ic_cnt in range (0, ic_total):
    for row in range (0, ia_size):
        for col in range (0, ia_size):
            if(row < (kernel_size-1)/2 or col < (kernel_size-1)/2 or row >= ia_size - (kernel_size-1)/2 or col >= ia_size - (kernel_size-1)/2):
                ia[ic_cnt][row][col] = 0 

weight_list = []
runlength_list = []
abs_loc_list = [] 

for pe_id in range(0, num_pe):
    weight_list.append([])
    runlength_list.append([])
    abs_loc_list.append([])

    #8 pe --> 4 ic + 2 oc
    #for oc_cnt_base in range (pe_id/4 * oc/pe_oc, (pe_id/4+1) * oc/pe_oc): 
    #    for ic_cnt_base in range (pe_id%4 * ic/pe_ic, (pe_id%4+1) * ic/pe_ic): 
    for oc_cnt_base in range (0, oc/pe_oc): 
        for ic_cnt_base in range (0 , ic/pe_ic): 
            for row in range (0, kernel_size):
                for col in range (0, kernel_size):
                    runlength = 0
                    for oc_cnt in range (0, pe_oc): 
                        for ic_cnt in range (0, pe_ic): 
                            if(sparse_w[oc_cnt_base*pe_oc+oc_cnt][ic_cnt_base*pe_ic+ic_cnt][row][col] == 0):
                                if(runlength == 32 or (oc_cnt == pe_oc-1 and ic_cnt == pe_ic-1)):
                                    weight_list[pe_id].append(0)
                                    runlength_list[pe_id].append(runlength)
                                    abs_loc_list[pe_id].append([oc_cnt_base, ic_cnt_base, row, col])
                                    runlength = 1
                                else:
                                    runlength = runlength + 1
                            else:
                                weight_list[pe_id].append(sparse_w[oc_cnt_base*pe_oc+oc_cnt][ic_cnt_base*pe_ic+ic_cnt][row][col])
                                runlength_list[pe_id].append(runlength)
                                abs_loc_list[pe_id].append([oc_cnt_base, ic_cnt_base, row, col])
                                runlength = 1
    
    weights_htree = HuffmanCoding(weight_list[pe_id])
    weight_list_coded = weights_htree.compress()
    weight_list_decoded = weights_htree.decompress(weight_list_coded)
    weight_codes = weights_htree.get_codes()
    weight_table = weights_htree.get_code_table()
    runlength_htree = HuffmanCoding(runlength_list[pe_id])
    runlength_list_coded = runlength_htree.compress()
    runlength_list_decoded = runlength_htree.decompress(runlength_list_coded)
    runlength_codes = runlength_htree.get_codes()
    runlength_table= runlength_htree.get_code_table()

    #print (weight_list_decoded == weight_list)
    #print (runlength_list_decoded == runlength_list)
    weight_mapping_file = open('pe_' + str(pe_id) + '_weight_mapping.txt', 'w')
    weight_table_file = open('pe_' + str(pe_id) + '_weight_table.txt', 'w')
    weight_raw_file = open('pe_' + str(pe_id) + '_weight_list_raw.txt', 'w')
    weight_coded_file = open('pe_' + str(pe_id) + '_weight_list_coded.txt', 'w')
    runlength_mapping_file = open('pe_' + str(pe_id) + '_runlength_mapping.txt', 'w')
    runlength_table_file = open('pe_' + str(pe_id) + '_runlength_table.txt', 'w')
    runlength_raw_file = open('pe_' + str(pe_id) + '_runlength_list_raw.txt', 'w')
    runlength_coded_file = open('pe_' + str(pe_id) + '_runlength_list_coded.txt', 'w')
    for item in weight_list[pe_id]:
      weight_raw_file.write("%s\n" % item)
    for item in weight_list_coded:
      weight_coded_file.write("%s\n" % item)
    for item in runlength_list[pe_id]:
      runlength_raw_file.write("%s\n" % item)
    for item in runlength_list_coded:
      runlength_coded_file.write("%s\n" % item)
    for item in weight_codes:
        weight_mapping_file.write(str(item) + ' ' + str(weight_codes[item]) + '\n')
    for subtree in weight_table:
        for item in subtree:
            if(item ==''):
                weight_table_file.write('00000000000000' + '\n')
            else:
                weight_table_file.write(item + '\n')
    for item in runlength_codes:
        runlength_mapping_file.write(str(item) + ' ' + str(runlength_codes[item]) + '\n')
    for subtree in runlength_table:
        for item in subtree:
            if(item ==''):
                runlength_table_file.write('00000000000000' + '\n')
            else:
                runlength_table_file.write(item + '\n')

weight_golden = open('weight.txt','w+') 
for oc_cnt in range (0, oc_total):
    for ic_cnt in range (0, ic_total):
        weight_golden.write('w channel: [' + str(oc_cnt) + ', ' + str(ic_cnt) + ']\n')
        for row in range (0, kernel_size):
            for col in range (0, kernel_size):
                weight_golden.write(str(format(sparse_w[oc_cnt][ic_cnt][row][col], '4d')) + '\t')
            weight_golden.write('\n')

weight_golden.close()


