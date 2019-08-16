import sys
sys.path.insert(0, '/net/tawas/w/liziyun/RRAM_DNN/common')
import os
from numpy import arange
import bisect
from decimal import *
import numpy
import math
from scipy import stats as scistats
import csv
from scipy.ndimage.filters import correlate as convolveim
import copy
from HuffmanCoding_weights import HuffmanCoding

from cnn_func import *
import architecture as arch

#########################################header layer#############################################
####################layer 1###########################
#layer 1, conv, 3x64x64 ia, 128x3x7x7 weight, stride 4, 128x32x32 oa
conv_1 = clear_layer() 
conv_1.name = 'conv1'
conv_1.opcode = 'conv'
conv_1.process_kernel_size = 7
conv_1.output_kernel_size = 1
conv_1.stride = 2 
conv_1.ic_total = 4 
conv_1.oc_total = 32 
conv_1.ia_size = 64 
conv_1.right_shift = 7 
conv_1 = gen_layer(conv_1, 1)

#partition
conv_1.pe_ic_max = 4 
conv_1.pe_oc_max = 32

####################layer 2###########################
#layer 2, pool, 128x32x32 ia, stride 2, 128x16x16 oa
pool_2 = clear_layer() 
pool_2.name = 'pool2'
pool_2.opcode = 'pool'
pool_2.max_0_avg_1 = 0
pool_2.process_kernel_size = 3
pool_2.output_kernel_size = 1
pool_2.stride = 2 
pool_2.ic_total = 32 
pool_2.oc_total = 32 
pool_2.ia_size = 32 
pool_2.right_shift = 0 
pool_2 = gen_layer(pool_2, 0)

#partition
pool_2.pe_ic_max = 32 
pool_2.pe_oc_max = 32

#########################################main layer#############################################
####################layer 3###########################
#layer 3, conv, 128x32x32 ia, stride 2, 128x16x16 oa
conv_3 = clear_layer() 
conv_3.name = 'conv3'
conv_3.opcode = 'conv'
conv_3.process_kernel_size = 3
conv_3.output_kernel_size = 1
conv_3.stride = 1 
conv_3.ic_total = 32 
conv_3.oc_total = 32
conv_3.ia_size = 16 
conv_3.right_shift = 9 
conv_3.relu = 0 
conv_3.ia = copy.deepcopy(pool_2.oa)
conv_3 = gen_layer(conv_3, 0)

#partition
conv_3.pe_ic_max = 8 
conv_3.pe_oc_max = 8

####################layer 4###########################
#layer 4, conv, 128x32x32 ia, stride 2, 128x16x16 oa
conv_4 = clear_layer() 
conv_4.name = 'conv4'
conv_4.opcode = 'conv'
conv_4.process_kernel_size = 3
conv_4.output_kernel_size = 1
conv_4.stride = 1 
conv_4.ic_total = 32 
conv_4.oc_total = 32 
conv_4.ia_size = 16 
conv_4.right_shift = 9 
conv_4.relu = 0
conv_4.ia = copy.deepcopy(conv_3.oa)
conv_4 = gen_layer(conv_4, 0)

#partition
conv_4.pe_ic_max = 8 
conv_4.pe_oc_max = 8

####################skip layer 24###########################
#layer 24, add, 128x32x32 ia, stride 1, 128x16x16 oa
add_24 = clear_layer() 
add_24.name = 'add24'
add_24.opcode = 'add'
add_24.process_kernel_size = 1
add_24.output_kernel_size = 1
add_24.stride = 1 
add_24.ic_total = 32 
add_24.oc_total = 32 
add_24.ia_size = 16 
add_24.right_shift = 1 
add_24.relu = 0
add_24.ia = copy.deepcopy(pool_2.oa)
add_24.ia_add = copy.deepcopy(conv_4.oa)
add_24 = gen_layer(add_24, 0)

#partition
add_24.pe_ic_max = 32 
add_24.pe_oc_max = 32

#########################################tail layer#############################################
####################layer 5###########################
#layer 5, conv, 128x32x32 ia, stride 2, 128x8x8 oa
conv_5 = clear_layer() 
conv_5.name = 'conv5'
conv_5.opcode = 'conv'
conv_5.process_kernel_size = 3
conv_5.output_kernel_size = 1
conv_5.stride = 2 
conv_5.ic_total = 32 
conv_5.oc_total = 32 
conv_5.ia_size = 16 
conv_5.right_shift = 11 
conv_5 = gen_layer(conv_5, 0)

#partition
conv_5.pe_ic_max = 8 
conv_5.pe_oc_max = 8

####################layer 2###########################
#layer 6, pool, 128x32x32 ia, stride 2, 128x16x16 oa
pool_6 = clear_layer() 
pool_6.name = 'pool6'
pool_6.opcode = 'pool'
pool_6.max_0_avg_1 = 1
pool_6.process_kernel_size = 8
pool_6.output_kernel_size = 1
pool_6.stride = 8 
pool_6.ic_total = 32 
pool_6.oc_total = 32 
pool_6.ia_size = 8 
pool_6.right_shift = 6 
pool_6 = gen_layer(pool_6, 0)

#partition
pool_6.pe_ic_max = 32 
pool_6.pe_oc_max = 32







