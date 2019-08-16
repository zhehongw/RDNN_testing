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

USB_init_pe_idx_all()
USB_init_constant()

#USB_init_icache_from_file_all_conv_test()
#USB_init_RRAM_from_file_all_conv_test()

#USB_init_icache_pe_from_file(0)
#USB_init_RRAM_pe_from_file(0)

#USB_dummy_long()

inst_begin, inst_end = gen_conv_inst_ia_split(net.conv_1, 0, 16384, 0, arch.RRAM_words_full, arch.num_pe)
gen_conv_input_ia_split(net.conv_1, 0, 2, arch.RRAM_words, arch.RRAM_words_full, arch.num_pe)
init_ia_word_list = build_share_mem([net.conv_1.ia], [0])

USB_init_pe_inst_all(inst_begin, inst_end)
USB_init_shared(init_ia_word_list)
USB_init_icache_all()
USB_init_w_huffman_shared()
USB_init_loc_huffman_shared()
USB_start_CNN_stop_USB()

#reading data out
for i in range(0, 1000):
    USB_read_shared(16384, 16388, 0)
    USB_dummy_short()

#inst_begin, inst_end = gen_pool_inst_ia_split(net.pool_2, 16384, 0)
#net.pool_2.ia = copy.deepcopy(net.conv_1.oa)
#gen_pool_input_ia_split(net.pool_2, 2, 0)
#
#USB_init_pe_inst_all(inst_begin, inst_end)
##USB_init_shared(init_ia_word_list)
##USB_init_icache_all()
#USB_start_CNN_stop_USB()

write_rram_mem(arch.RRAM_words, arch.RRAM_words_full)
write_inst_mem()

#USB_dummy_long()

