import sys
sys.path.insert(0, '/home/m3/Desktop/ReRAM_test/scripts/common')
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

import architecture as arch 
import network as net 
from split_func import *
from writer_func import *
from mem_func import *
from cnn_func import *
from inst_func import *
from USB_func import *

numpy.random.seed(9001)
arch.rram_mode = 1 

arch.init_rram_mem()
arch.init_inst_mem()
#arch.init_shared_mem()


USB_init_constant()

USB_init_pe_idx_all()

#USB_read_constant()
#USB_read_shared(0, 256, 0)

USB_dummy_long()

write_rram_mem(arch.RRAM_words, arch.RRAM_words_full)
write_inst_mem()
#USB_init_RRAM_all()

cycle = 20000
offset = 100
for j in range(0, 24):
    for i in range (0, cycle):
        USB_init_RRAM_word_conv(15, 0, offset, j)
        USB_init_RRAM_word_conv(15, 1, offset, j)
        USB_init_RRAM_word_conv(15, 2, offset, j)
        USB_init_RRAM_word_conv(15, 3, offset, j)
        USB_init_RRAM_word_conv(15, 4, offset, j)
        USB_init_RRAM_word_conv(15, 5, offset, j)
        for i in range(0, 5):
            USB_dummy_short()

#for k in range(4, 8):
#    line = '0' * k + '1' + '0' * (96 - k - 1)
#    for j in range(0, cycle):
#        USB_init_RRAM_word(0, 2, 10512, line)
#        for i in range(0, 5):
#            USB_dummy_short()
#    USB_dummy_short()
#    cycle = cycle + 100000

#line = '0' * 5 + '1' + '0' * (96 - 5 - 1)
#for j in range(0, cycle):
#    USB_init_RRAM_word(15, 2, 10508, line)
#    for i in range(0, 5):
#        USB_dummy_short()

for i in range(0, 64):
    USB_dummy_short()

for i in range(0, 1000):
    for b_idx in range(0, 6): 
        for j in range(0, 24):
            addr = offset + j
            USB_read_RRAM(15, b_idx, addr, addr, 0)
            USB_dummy_short_read()

    #USB_dummy_short()
    #USB_read_RRAM(15, 2, 10508, 10508, 0)
    #USB_read_RRAM(2, 0, 8260, 8260, 0)
    #USB_dummy_short()
    #USB_read_RRAM(2, 0, 8513, 8513, 0)
    #USB_dummy_short()

#USB_start_CNN()

#USB_dummy_long()
#USB_dummy_long()
#USB_dummy_long()
#USB_dummy_long()
USB_dummy_long()

