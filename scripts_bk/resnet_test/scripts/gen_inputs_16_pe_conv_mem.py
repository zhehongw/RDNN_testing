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

USB_init_constant()

#USB_read_constant()
#USB_read_shared(0, 256, 0)

USB_dummy_long()

offset = 256 
addr = 0
rram_pe_id = 0
rram_bank_id = 4 
#16 pes
#for rram_pe_id in range(0, 1):
for rram_bank_id in range(0, 6):
    #6 rram banks 
    #for rram_bank_id in range(0, 6):
        #print(str(i) + " " + str(j) + " " + str(addr))
    #USB_init_RRAM_word_conv(rram_pe_id, rram_bank_id, offset, addr)
    for k in range(0, 4):
        USB_dummy_short()

for i in range(0, 64):
    USB_dummy_short()

for cnt in range(0, 2048):
    #16 pes
    #for rram_pe_id in range(0, 1):
    for rram_bank_id in range(0, 6):
        #6 rram banks 
        #for rram_bank_id in range(0, 6):
            #print(str(i) + " " + str(j) + " " + str(addr))
        USB_read_RRAM(rram_pe_id, rram_bank_id, addr+offset, addr+offset, 0)
        USB_dummy_short()

USB_dummy_long()

