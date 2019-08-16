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

import architecture as arch 
import network as net 
from split_func import *
from writer_func import *
from mem_func import *
from cnn_func import *
from inst_func import *
from USB_func import *

numpy.random.seed(9001)
arch.rram_mode = 0 

arch.init_rram_mem()
arch.init_inst_mem()
#arch.init_shared_mem()

USB_init_pe_idx_all()
USB_init_constant()

inst_begin, inst_end = gen_conv_inst_ia_split(net.conv_1, 0, 16384, arch.RRAM_words_full, 4)
gen_conv_input_ia_split(net.conv_1, 0, 2, arch.RRAM_words, arch.RRAM_words_full, 4)
init_ia_word_list = build_share_mem([net.conv_1.ia], [0])

USB_init_pe_inst_all(inst_begin, inst_end)
USB_init_w_huffman_shared()
USB_init_loc_huffman_shared()
#USB_init_shared(init_ia_word_list)
#USB_init_icache_all()
USB_start_CNN_stop_USB()

write_rram_mem(arch.RRAM_words, arch.RRAM_words_full)
write_inst_mem()
#USB_init_RRAM_all()

#USB_start_CNN()

