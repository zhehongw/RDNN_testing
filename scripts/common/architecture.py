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

class cnn_layer:
    #instruction class
    def __init__(self):
        #basic
        self.name = 'none'
        self.opcode = 'invalid' 
        self.max_0_avg_1 = 0
        self.relu = 0
        self.process_kernel_size = 0
        self.output_kernel_size = 1
        self.stride = 0
        self.ic_total = 0
        self.oc_total = 0
        self.ia_size = 0 
        self.oa_size = 0
        self.right_shift = 0 
        self.w = numpy.zeros((self.oc_total, self.ic_total, self.process_kernel_size, self.process_kernel_size), dtype=numpy.int) 
        self.ia = numpy.zeros((self.ic_total, self.ia_size, self.ia_size), dtype=numpy.int) 
        self.ia_add = numpy.zeros((self.ic_total, self.ia_size, self.ia_size), dtype=numpy.int) 
        self.oa = numpy.zeros((self.oc_total, self.oa_size, self.oa_size), dtype=numpy.int) 
        #split
        self.pe_ic_max = 0  
        self.pe_oc_max = 0 
        self.ia_mem_addr = 0
        self.oa_mem_addr = 0
        self.w_rram_addr = 0

class instruction:
    #instruction class
    def __init__(self):
        self.valid = 0 
        self.opcode = 0
        self.max_0_avg_1 = 0
        self.process_kernel_size = 0
        self.output_kernel_size = 1
        self.stride = 0
        self.ic_size = 0
        self.current_ic = 0
        self.start_ic = 0 
        self.finish_ic = 0 
        self.oc_size = 0
        self.current_oc = 0
        self.start_oc = 0 
        self.finish_oc = 0
        self.ia_row_current = 0 
        self.ia_row_start = 0  
        self.ia_row_end = 0 
        self.ia_row_size = 0
        self.ia_col_current = 0
        self.ia_col_start = 0  
        self.ia_col_end = 0 
        self.ia_col_size  = 0
        self.oa_row_size = 0
        self.oa_col_size = 0
        self.shift_width = 0
        self.buffer_mode = 0
        self.ia_mem_addr_0 = 0
        self.ia_mem_dir_0 = 0
        self.ia_mem_buffer_0 = 0
        self.ia_mem_addr_1 = 0
        self.ia_mem_dir_1 = 0
        self.ia_mem_buffer_1 = 0
        self.oa_mem_addr = 0
        self.oa_mem_dir = 0
        self.oa_mem_buffer = 0
        self.sparse_fc_clean = 0
        self.sparse_fc_process = 0
        self.sparse_fc_mov = 0
        self.rram_mode = 0
        self.rram_addr = 0
        self.wram_addr = 0
        self.stall_cycles = 0
        self.conv_clear_finished = 0
        self.conv_clear_addr = 0 

#constants
num_pe_row = 4
num_pe_col = 4
num_pe = 16 
rram_banks = 6 
pe_ic = 4
pe_oc = 4
pe_mult = 8
max_pe_ic = 128
max_pe_oc = 128
pe_row_master = [1, 5, 9, 13]
rram_mode = 0 

#RRAM
RRAM_words = []
RRAM_words_full = []
RRAM_file = []
rram_mem = []
rram_cnt = []
def init_rram_mem():
    for j in range(0, num_pe):
        RRAM_words.append([])
        RRAM_words_full.append([])
        RRAM_file.append(open('../data/pe_' + str(j) + '_RRAM_full.mem','w+'))
        rram_mem.append([])
        rram_cnt.append([])
        for i in range(0, rram_banks):
            rram_mem[j].append(open('../data/pe_' + str(j) + '_rram_' + str(i) + '.mem','w+'))
            rram_cnt[j].append(0)

#INST SRAM
inst_list=[]
inst_txt=[]
inst_mem_cnt=[]
inst_mem=[]
def init_inst_mem():
    for i in range(0, num_pe):
        inst_list.append([])
        inst_txt.append(open('../inst/pe_' + str(i) + '_inst' + '.txt','w+'))
        inst_mem.append([])
        inst_mem_cnt.append(0)
        for k in range(0, 2):
            inst_mem[i].append([])
            for j in range(0, 3):
                inst_mem[i][k].append(open('../inst/pe_' + str(i) + '_inst_' + str(k) + '_' + str(j) + '.mem','w+'))

USB_inst_list=[]
USB_inst_file = open('../USB_inst' + '.txt','w+')

def get_neighbor_dir(pe_master, pe_slave):
    if(pe_master/4 == pe_slave/4):
    #same row
        if(pe_master - pe_slave == 1):
        #west neighbor
            return 0
        elif(pe_slave - pe_master == 1):
        #east neighbor
            return 2
        else:
            return -1
    else:
        if(pe_master - pe_slave == 4):
        #north neighbor
            return 3
        elif(pe_slave - pe_master == 4):
        #south neighbor
            return 1
        else:
            return -1 


