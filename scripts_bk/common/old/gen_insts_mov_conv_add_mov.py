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

def bindigits(n, bits):
    s = bin(n & int("1"*bits, 2))[2:]
    return ("{0:0>%s}" % (bits)).format(s)

def bininst(valid, opcode, max_0_avg_1, process_kernel_size, output_kernel_size, stride, ic_size, current_ic, start_ic, finish_ic, oc_size, current_oc, start_oc, finish_oc, \
            ia_size, ia_row_current, ia_col_current, ia_row_start, ia_col_start, ia_row_end, ia_col_end, ia_row_size, ia_col_size, oa_size, shift_width, buffer_mode, \
            ia_mem_addr_0, ia_mem_dir_0, ia_mem_buffer_0, ia_mem_addr_1, ia_mem_dir_1, ia_mem_buffer_1, oa_mem_addr, oa_mem_dir, oa_mem_buffer, sparse_fc_clean, sparse_fc_process, \
            sparse_fc_mov, rram_mode, rram_addr, stall_cycles, conv_clear_finished, conv_clear_addr):
    return bindigits(valid, 1) + bindigits(opcode, 3) + bindigits(max_0_avg_1, 1) + bindigits(process_kernel_size, 4) + bindigits(output_kernel_size, 4) + \
            bindigits(stride, 2) + bindigits(ic_size, 12) + bindigits(current_ic, 12) + bindigits(start_ic, 12) + bindigits(finish_ic, 12) + bindigits(oc_size, 12) + bindigits(current_oc, 12) + \
            bindigits(start_oc, 12) + bindigits(finish_oc, 12) + bindigits(ia_size, 8) + bindigits(ia_row_current, 8) + bindigits(ia_col_current, 8) + bindigits(ia_row_start, 8) + bindigits(ia_col_start, 8) + \
            bindigits(ia_row_end, 8) + bindigits(ia_col_end, 8) + bindigits(ia_row_size, 8) + bindigits(ia_col_size, 8) + bindigits(oa_size, 8) + bindigits(shift_width, 5) + bindigits(buffer_mode, 1) + \
            bindigits(ia_mem_addr_0, 16) + bindigits(ia_mem_dir_0, 4) + bindigits(ia_mem_buffer_0, 2) + bindigits(ia_mem_addr_1, 16) + bindigits(ia_mem_dir_1, 4) + bindigits(ia_mem_buffer_1, 2) + \
            bindigits(oa_mem_addr, 16) + bindigits(oa_mem_dir, 4) + bindigits(oa_mem_buffer, 2) + bindigits(sparse_fc_clean, 1) + bindigits(sparse_fc_process, 1) + \
            bindigits(sparse_fc_mov, 1) + bindigits(rram_mode, 2) + bindigits(rram_addr, 32) + bindigits(stall_cycles, 32) + bindigits(conv_clear_finished, 1) + bindigits(conv_clear_addr, 10)

#inst_rram_mode =
#inst_rram_addr =
#inst_stall_cycles =

numpy.random.seed(9001)

num_pe = 8
ic = 64 
ic_total = 256
oc = 32 
oc_total = 64
stride = 1
kernel_size = 3
output_kernel_size = 3
ia_size = 18
oa_size = (ia_size - kernel_size + 1)/stride + output_kernel_size - 1
write_ia_num = 0
write_oa_num = 1
rram_banks = 8 
right_shift = 8
ia_ram_banks = 4
pe_ic = 8
pe_oc = 8

inst_valid = 0 
inst_opcode = 0
inst_max_0_avg_1 = 0
inst_process_kernel_size = 0
inst_output_kernel_size = 0
inst_stride = 0
inst_ic_size = 0
inst_current_ic = 0
inst_oc_size = 0
inst_current_oc = 0
inst_ia_size = 0
inst_oa_size = 0
inst_shift_width = 0
inst_buffer_mode = 0
inst_ia_mem_addr_0 = 0
inst_ia_mem_dir_0 = 0
inst_ia_mem_buffer_0 = 0
inst_ia_mem_addr_1 = 0
inst_ia_mem_dir_1 = 0
inst_ia_mem_buffer_1 = 0
inst_oa_mem_addr = 0
inst_oa_mem_dir = 0
inst_oa_mem_buffer = 0
inst_sparse_fc_clean = 0
inst_sparse_fc_process = 0
inst_sparse_fc_mov = 0
inst_rram_mode = 0
inst_rram_addr = 0
inst_stall_cycles = 0
inst_conv_clear_finished = 0
inst_conv_clear_addr = 0 

#instructions first
#8 move, 8 conv in parallel, then add, then add

#INST SRAM
inst_list=[]
for i in range(0, num_pe):
    inst_list.append([])

inst_txt=[]
for i in range(0, num_pe):
    inst_txt.append(open('pe_' + str(i) + '_inst' + '.txt','w+'))

inst_mem=[]
for i in range(0, num_pe):
    inst_mem.append([])
    for j in range(0, 3):
        inst_mem[i].append(open('pe_' + str(i) + '_inst_' + str(j) + '.mem','w+'))

inst_mem_cnt=[]
for j in range(0, num_pe):
    inst_mem_cnt.append(0)

for pe_id in range(0, num_pe):
    for i in range(0, num_pe):
        #mov
        inst_valid = 1 
        inst_opcode = 2 
        inst_process_kernel_size = 3
        inst_output_kernel_size = 3
        inst_ic_size = 256
        inst_current_ic = 0 
        inst_start_ic = 64 * int(i%4) 
        inst_finish_ic = 64 * int(i%4) + 64 
        inst_oc_size = 32 
        inst_current_oc = 0 
        inst_start_oc = 32 * int(i/4) 
        inst_finish_oc = 32 * int(i/4) + 32
        inst_ia_size = 34 
        inst_ia_row_current = 0
        inst_ia_col_current = 0
        inst_ia_row_start = 0
        inst_ia_col_start = 0
        inst_ia_row_end = 0
        inst_ia_col_end = 0
        inst_ia_row_size = 0
        inst_ia_col_size  = 0
        inst_oa_size = 34
        inst_ia_mem_addr_0 = 0
        inst_ia_mem_dir_0 = 8 
        inst_ia_mem_buffer_0 = 0
        inst_oa_mem_addr = 0
        inst_oa_mem_dir = 15
        inst_oa_mem_buffer = 0 

        inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
                    inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
                    inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
                    inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
                    inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

        inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')
        if(i == pe_id):
            inst_list[i].append(inst_word)
            inst_mem_cnt[i] = inst_mem_cnt[i] + 1

        #conv
        inst_valid = 1 
        inst_opcode = 0 
        inst_max_0_avg_1 = 0
        inst_process_kernel_size = 3
        inst_output_kernel_size = 3
        inst_stride = 1 
        inst_ic_size = 64
        inst_current_ic = 0 
        inst_finish_ic = 64 
        inst_oc_size = 32 
        inst_current_oc = 0 
        inst_finish_oc = 32 
        inst_ia_size = 10 
        inst_ia_row_current = 0
        inst_ia_col_current = 0
        inst_ia_row_end = 0
        inst_ia_col_end = 0
        inst_ia_row_size = 0
        inst_ia_col_size = 0
        inst_oa_size = 10 
        inst_oa_end = 0
        inst_shift_width = 6 # total 8 = conv 6 + add 2 
        inst_buffer_mode = 0
        inst_ia_mem_addr_0 = 0
        inst_ia_mem_dir_0 = 15 #local 
        inst_ia_mem_buffer_0 = 0
        inst_oa_mem_addr = 0
        inst_oa_mem_dir = 15 #local
        inst_oa_mem_buffer = 1

        inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
                    inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
                    inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
                    inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
                    inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

        inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')
        if(i == pe_id):
            inst_list[i].append(inst_word)
            inst_mem_cnt[i] = inst_mem_cnt[i] + 1

        #print(inst_word)
        #stall
        inst_valid = 1 
        inst_opcode = 6  
        inst_stall_cycles = 640 

        inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
                    inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
                    inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
                    inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
                    inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

        inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')
        #print(inst_word)

        if(i != pe_id):
            inst_list[i].append(inst_word)
            inst_mem_cnt[i] = inst_mem_cnt[i] + 1

#add
inst_valid = 1 
inst_opcode = 3  
inst_process_kernel_size = 3
inst_output_kernel_size = 3
inst_ic_size = 32 
inst_current_ic = 0 
inst_oc_size = 32 
inst_current_oc = 0 
inst_ia_size = 10 
inst_oa_size = 10 
inst_shift_width = 1 # total 8 = conv 6 + add 1 + add 1 
inst_buffer_mode = 0
inst_ia_mem_addr_0 = 0
inst_ia_mem_dir_0 = 15 #local 
inst_ia_mem_buffer_0 = 1 
inst_ia_mem_addr_1 = 0
#dir varies with pe
inst_ia_mem_buffer_1 = 1
inst_oa_mem_addr = 0
inst_oa_mem_dir = 15 #local
inst_oa_mem_buffer = 2 

#merge 1
inst_ia_mem_dir_1 =  0#left neighbor 


inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
            inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
            inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
            inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
            inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')

inst_list[1].append(inst_word)
inst_mem_cnt[1] = inst_mem_cnt[1] + 1

inst_list[5].append(inst_word)
inst_mem_cnt[5] = inst_mem_cnt[5] + 1


inst_ia_mem_dir_1 =  2#right neighbor 


inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
            inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
            inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
            inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
            inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')

inst_list[2].append(inst_word)
inst_mem_cnt[2] = inst_mem_cnt[2] + 1

inst_list[6].append(inst_word)
inst_mem_cnt[6] = inst_mem_cnt[6] + 1

#wait
inst_valid = 1 
inst_opcode = 6  
inst_stall_cycles = 160 

inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
            inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
            inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
            inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
            inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')
#print(inst_word)

inst_list[1].append(inst_word)
inst_mem_cnt[1] = inst_mem_cnt[1] + 1

inst_list[5].append(inst_word)
inst_mem_cnt[5] = inst_mem_cnt[5] + 1

#merge 2
#add
inst_valid = 1 
inst_opcode = 3  
inst_process_kernel_size = 3
inst_output_kernel_size = 3
inst_ic_size = 32 
inst_current_ic = 0 
inst_oc_size = 32 
inst_current_oc = 0 
inst_ia_size = 10 
inst_oa_size = 10 
inst_shift_width = 1 # total 8 = conv 6 + add 1 + add 1 
inst_buffer_mode = 0
inst_ia_mem_addr_0 = 0
inst_ia_mem_dir_0 = 15 #local 
inst_ia_mem_buffer_0 = 1 
inst_ia_mem_addr_1 = 0
#dir varies with pe
inst_ia_mem_buffer_1 = 1
inst_oa_mem_addr = 0
inst_oa_mem_dir = 15 #local
inst_oa_mem_buffer = 2 

inst_ia_mem_dir_1 =  2#right neighbor 
inst_ia_mem_buffer_0 = 2 
inst_ia_mem_buffer_1 = 2 
inst_oa_mem_buffer = 3 

inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
            inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
            inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
            inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
            inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')

inst_list[1].append(inst_word)
inst_mem_cnt[1] = inst_mem_cnt[1] + 1

inst_ia_mem_dir_1 =  2#right neighbor 
inst_ia_mem_buffer_0 = 2 
inst_ia_mem_buffer_1 = 2 
inst_oa_mem_buffer = 3 

inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
            inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
            inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
            inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
            inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')

inst_list[5].append(inst_word)
inst_mem_cnt[5] = inst_mem_cnt[5] + 1

#mov back
#mov
inst_valid = 1 
inst_opcode = 2 
inst_process_kernel_size = 3
inst_output_kernel_size = 3
inst_ic_size = 64 
inst_current_ic = 0 
inst_start_ic = 0
inst_finish_ic = 32 
inst_oc_size = 64 
inst_current_oc = 0 
inst_ia_size = 34 
inst_ia_row_current = 0
inst_ia_col_current = 0
inst_ia_row_start = 0
inst_ia_col_start = 0
inst_ia_row_end = 9
inst_ia_col_end = 9 
inst_ia_row_size = 9 
inst_ia_col_size = 9
inst_oa_size = 34
inst_oa_end = 0
inst_ia_mem_addr_0 = 0
inst_ia_mem_dir_0 = 15 
inst_ia_mem_buffer_0 = 3 
inst_oa_mem_addr = 8192 
inst_oa_mem_dir = 8
inst_oa_mem_buffer = 0


inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
            inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
            inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
            inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
            inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')
inst_list[1].append(inst_word)
inst_mem_cnt[1] = inst_mem_cnt[1] + 1

#print(inst_word)
#stall
inst_valid = 1 
inst_opcode = 6  
inst_stall_cycles = 640 

inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
            inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
            inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
            inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
            inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')
#print(inst_word)

inst_list[5].append(inst_word)
inst_mem_cnt[5] = inst_mem_cnt[i] + 1

#mov back
#mov
inst_valid = 1 
inst_opcode = 2 
inst_process_kernel_size = 3
inst_output_kernel_size = 3
inst_ic_size = 64 
inst_current_ic = 0 
inst_start_ic = 32
inst_finish_ic = 64 
inst_oc_size = 64 
inst_current_oc = 0 
inst_ia_size = 34 
inst_ia_row_current = 0
inst_ia_col_current = 0
inst_ia_row_start = 0
inst_ia_col_start = 0
inst_ia_row_end = 9
inst_ia_col_end = 9 
inst_ia_row_size = 9 
inst_ia_col_size = 9
inst_oa_size = 34
inst_oa_end = 0
inst_ia_mem_addr_0 = 0
inst_ia_mem_dir_0 = 15 
inst_ia_mem_buffer_0 = 3 
inst_oa_mem_addr = 8192 
inst_oa_mem_dir = 8
inst_oa_mem_buffer = 0


inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
            inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
            inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
            inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
            inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')
inst_list[5].append(inst_word)
inst_mem_cnt[5] = inst_mem_cnt[5] + 1

#sync
for i in range(0, num_pe):
    inst_valid = 1 
    inst_opcode = 6  
    inst_sparse_fc_process = 1

    inst = bininst(inst_valid, inst_opcode, inst_max_0_avg_1, inst_process_kernel_size, inst_output_kernel_size, inst_stride, inst_ic_size, inst_current_ic, inst_start_ic, inst_finish_ic, \
                inst_oc_size, inst_current_oc, inst_start_oc, inst_finish_oc, inst_ia_size, inst_ia_row_current, inst_ia_col_current, inst_ia_row_start, inst_ia_col_start, \
                inst_ia_row_end, inst_ia_col_end, inst_ia_row_size, inst_ia_col_size, inst_oa_size, inst_shift_width, inst_buffer_mode, inst_ia_mem_addr_0, inst_ia_mem_dir_0, \
                inst_ia_mem_buffer_0, inst_ia_mem_addr_1, inst_ia_mem_dir_1, inst_ia_mem_buffer_1, inst_oa_mem_addr, inst_oa_mem_dir, inst_oa_mem_buffer, inst_sparse_fc_clean, \
                inst_sparse_fc_process, inst_sparse_fc_mov, inst_rram_mode, inst_rram_addr, inst_stall_cycles, inst_conv_clear_finished, inst_conv_clear_addr)

    inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')
    #print(inst_word)

    inst_list[i].append(inst_word)
    inst_mem_cnt[i] = inst_mem_cnt[i] + 1

for i in range(0, num_pe):
    for item in inst_list[i]:
      inst_txt[i].write("%s\n" % item)

for i in range(0, num_pe):
    for item in inst_list[i]:
        inst_mem[i][2].write("%s\n" % item[0:128])
        inst_mem[i][1].write("%s\n" % item[128:256])
        inst_mem[i][0].write("%s\n" % item[256:384])

for i in range(0, num_pe):
    for rest_addr in range(0, 1024-inst_mem_cnt[pe_id]):
        inst_mem[i][0].write('x' * 128 + '\n')
        inst_mem[i][1].write('x' * 128 + '\n')
        inst_mem[i][2].write('x' * 128 + '\n')

for i in range(0, num_pe):
    inst_mem[i][0].close()
    inst_mem[i][1].close()
    inst_mem[i][2].close()

