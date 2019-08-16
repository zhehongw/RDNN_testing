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

def bindigits(n, bits):
    s = bin(int(n) & int("1"*bits, 2))[2:]
    return ("{0:0>%s}" % (bits)).format(s)

def bininst(inst):
    return bindigits(inst.valid, 1) + bindigits(inst.opcode, 3) + bindigits(inst.max_0_avg_1, 1) + bindigits(inst.process_kernel_size, 4) + bindigits(inst.output_kernel_size, 4) + bindigits(inst.stride, 4) + \
            bindigits(inst.ic_size, 12) + bindigits(inst.start_ic, 12) + bindigits(inst.finish_ic, 12) + \
            bindigits(inst.oc_size, 12) + bindigits(inst.start_oc, 12) + bindigits(inst.finish_oc, 12) + \
            bindigits(inst.ia_row_start, 8) + bindigits(inst.ia_col_start, 8) + bindigits(inst.ia_row_end, 8) + \
            bindigits(inst.ia_col_end, 8) + bindigits(inst.ia_row_size, 8) + bindigits(inst.ia_col_size, 8) + \
            bindigits(inst.oa_row_size, 8) +  bindigits(inst.oa_col_size, 8) + bindigits(inst.shift_width, 5) + bindigits(inst.buffer_mode, 1) + \
            bindigits(inst.ia_mem_addr_0, 16) + bindigits(inst.ia_mem_dir_0, 4) + bindigits(inst.ia_mem_buffer_0, 2) + bindigits(inst.ia_mem_addr_1, 9) + bindigits(inst.ia_mem_dir_1, 4) + bindigits(inst.ia_mem_buffer_1, 2) + \
            bindigits(inst.oa_mem_addr, 16) + bindigits(inst.oa_mem_dir, 4) + bindigits(inst.oa_mem_buffer, 2) + \
            bindigits(inst.sparse_fc_clean, 1) + bindigits(inst.sparse_fc_process, 1) + bindigits(inst.sparse_fc_mov, 1) + \
            bindigits(inst.rram_mode, 2) + bindigits(inst.rram_addr, 32) + bindigits(inst.conv_clear_finished, 1)

def makeinst(inst_vec):
    inst = bininst(inst_vec)
    #print 'inst length: ' + str(len(inst))

    inst_word = '{message:>384{fill}}'.format(message=inst, fill='').replace(' ', '0')
    return inst_word

def clear_inst():
    inst_vec = arch.instruction()
    return inst_vec

def add_stall(num_cycles):

    inst_vec = clear_inst()

    inst_vec.valid = 1 
    inst_vec.opcode = 6  
    inst_vec.rram_addr = num_cycles 

    inst_word = makeinst(inst_vec)
    return inst_word

def mov_gtl_coalescing(ias, weights, pe_id, pe_oc_max=128, pe_ic_max=128, pe_row_max=4, pe_col_max=4, ia_row_block=0, ia_col_block=0, ia_pad=1, oa_pad=1, pe_oc_start=0, pe_ic_start=0):

    inst_vec = clear_inst()

    #mov a 8x8 block at ic base and oc base
    inst_vec.valid = 1 
    inst_vec.opcode = 2 
    inst_vec.process_kernel_size = ia_pad
    inst_vec.output_kernel_size = ia_pad

    #set ic
    inst_vec.ic_size = pe_ic_max 
    inst_vec.start_ic = pe_ic_start 
    inst_vec.finish_ic = pe_ic_start + pe_ic_max

    #set oc 
    inst_vec.oc_size = pe_ic_max
    inst_vec.start_oc = pe_oc_start
    inst_vec.finish_oc = pe_oc_start + pe_ic_max

    #set ia
    inst_vec.ia_row_size = ias.shape[1]
    inst_vec.ia_col_size = ias.shape[2]
    if(ia_row_block == 0):
        inst_vec.ia_row_start = arch.pe_mult * ia_row_block 
        inst_vec.process_kernel_size = ia_pad 
        inst_vec.ia_row_end = arch.pe_mult * ia_row_block + arch.pe_mult + ia_pad
    elif(ia_row_block == pe_row_max-1): 
        inst_vec.ia_row_start = arch.pe_mult * ia_row_block - ia_pad 
        inst_vec.process_kernel_size = 0 
        inst_vec.ia_row_end = arch.pe_mult * ia_row_block + arch.pe_mult
    else:
        inst_vec.ia_row_start = arch.pe_mult * ia_row_block - ia_pad 
        inst_vec.process_kernel_size = 0 
        inst_vec.ia_row_end = arch.pe_mult * ia_row_block + arch.pe_mult + ia_pad

    if(ia_col_block == 0):
        inst_vec.ia_col_start = arch.pe_mult * ia_col_block 
        inst_vec.output_kernel_size = ia_pad 
        inst_vec.ia_col_end = arch.pe_mult * ia_col_block + arch.pe_mult + ia_pad
    elif(ia_col_block == pe_col_max-1): 
        inst_vec.ia_col_start = arch.pe_mult * ia_col_block - ia_pad 
        inst_vec.output_kernel_size = 0 
        inst_vec.ia_col_end = arch.pe_mult * ia_col_block + arch.pe_mult
    else:
        inst_vec.ia_col_start = arch.pe_mult * ia_col_block - ia_pad 
        inst_vec.output_kernel_size = 0 
        inst_vec.ia_col_end = arch.pe_mult * ia_col_block + arch.pe_mult + ia_pad

    #set oa
    inst_vec.oa_row_size = arch.pe_mult + ia_pad * 2 
    inst_vec.oa_col_size = arch.pe_mult + ia_pad * 2 

    #from shared global
    inst_vec.ia_mem_addr_0 = 0
    inst_vec.ia_mem_dir_0 = 8 
    inst_vec.ia_mem_buffer_0 = 0
    #to local bank 0
    inst_vec.oa_mem_addr = 0
    inst_vec.oa_mem_dir = 15
    inst_vec.oa_mem_buffer = 0 

    inst_word = makeinst(inst_vec)
    #print 'pe: ' + str(pe_id) + ' ic: ' + str(pe_ic_start) + ' oc: ' + str(pe_oc_start) + ' inst: ' + inst_word

    #mov is blocking, have to append a stall cycle for all pes
    row_idx = math.floor(pe_id / arch.num_pe_col)
    for col_idx in range(0, arch.num_pe_col):
        i = int(row_idx * arch.num_pe_col + col_idx)
        if(i == pe_id):
            arch.inst_list[i].append(inst_word)
            arch.inst_mem_cnt[i] += 1
        else:
            arch.inst_list[i].append(add_stall((arch.pe_mult + ia_pad * ia_pad) * (pe_ic_max/arch.pe_ic) * 6 + 64))
            arch.inst_mem_cnt[i] += 1

def mov_gtl_blocking(ias, weights, pe_id, pe_oc_max=128, pe_ic_max=128, pe_row_max=4, pe_col_max=4, ia_row_block=0, ia_col_block=0, ia_pad=1, oa_pad=1, pe_oc_start=0, pe_ic_start=0, ia_mem_addr=0, oa_mem_buf=0, blocking=0):

    inst_vec = clear_inst()

    #mov a 8x8 block at ic base and oc base
    inst_vec.valid = 1 
    inst_vec.opcode = 2 
    inst_vec.process_kernel_size = ia_pad
    inst_vec.output_kernel_size = ia_pad

    #set ic
    inst_vec.ic_size = ias.shape[0] 
    inst_vec.start_ic = pe_ic_start 
    inst_vec.finish_ic = pe_ic_start + pe_ic_max

    #set oc 
    inst_vec.oc_size = pe_ic_max
    inst_vec.start_oc = pe_oc_start
    inst_vec.finish_oc = pe_oc_start + pe_ic_max

    #set ia
    inst_vec.ia_row_size = ias.shape[1]
    inst_vec.ia_col_size = ias.shape[2]
    if(ia_row_block == 0):
        inst_vec.ia_row_start = arch.pe_mult * ia_row_block 
        inst_vec.process_kernel_size = ia_pad 
        inst_vec.ia_row_end = arch.pe_mult * ia_row_block + arch.pe_mult + ia_pad
    elif(ia_row_block == pe_row_max-1): 
        inst_vec.ia_row_start = arch.pe_mult * ia_row_block - ia_pad 
        inst_vec.process_kernel_size = 0 
        inst_vec.ia_row_end = arch.pe_mult * ia_row_block + arch.pe_mult
    else:
        inst_vec.ia_row_start = arch.pe_mult * ia_row_block - ia_pad 
        inst_vec.process_kernel_size = 0 
        inst_vec.ia_row_end = arch.pe_mult * ia_row_block + arch.pe_mult + ia_pad

    if(ia_col_block == 0):
        inst_vec.ia_col_start = arch.pe_mult * ia_col_block 
        inst_vec.output_kernel_size = ia_pad 
        inst_vec.ia_col_end = arch.pe_mult * ia_col_block + arch.pe_mult + ia_pad
    elif(ia_col_block == pe_col_max-1): 
        inst_vec.ia_col_start = arch.pe_mult * ia_col_block - ia_pad 
        inst_vec.output_kernel_size = 0 
        inst_vec.ia_col_end = arch.pe_mult * ia_col_block + arch.pe_mult
    else:
        inst_vec.ia_col_start = arch.pe_mult * ia_col_block - ia_pad 
        inst_vec.output_kernel_size = 0 
        inst_vec.ia_col_end = arch.pe_mult * ia_col_block + arch.pe_mult + ia_pad

    #set oa
    inst_vec.oa_row_size = arch.pe_mult + ia_pad * 2 
    inst_vec.oa_col_size = arch.pe_mult + ia_pad * 2 

    #from shared global
    inst_vec.ia_mem_addr_0 = ia_mem_addr 
    inst_vec.ia_mem_dir_0 = 8 
    inst_vec.ia_mem_buffer_0 = 0
    #to local bank 
    inst_vec.oa_mem_addr = 0
    inst_vec.oa_mem_dir = 15
    inst_vec.oa_mem_buffer = oa_mem_buf 

    inst_word = makeinst(inst_vec)
    #print 'pe: ' + str(pe_id) + ' ic: ' + str(pe_ic_start) + ' oc: ' + str(pe_oc_start) + ' inst: ' + inst_word

    if(blocking == 0):
        #mov is blocking, have to append a stall cycle for all pes
        for i in range(0, arch.num_pe):
            if(i == pe_id):
                arch.inst_list[i].append(inst_word)
                arch.inst_mem_cnt[i] += 1
            else:
                arch.inst_list[i].append(add_stall((arch.pe_mult + ia_pad * ia_pad) * (pe_ic_max/arch.pe_ic) * 12 + 32))
                arch.inst_mem_cnt[i] += 1
    elif(blocking == 1):
        #mov is blocking, have to append a stall cycle for all pes in a col
        row_idx = math.floor(pe_id / arch.num_pe_col)
        for col_idx in range(0, arch.num_pe_col):
            i = int(row_idx * arch.num_pe_col + col_idx)
            if(i == pe_id):
                arch.inst_list[i].append(inst_word)
                arch.inst_mem_cnt[i] += 1
            else:
                arch.inst_list[i].append(add_stall((arch.pe_mult + ia_pad * ia_pad) * (pe_ic_max/arch.pe_ic) * 12 + 32))
                arch.inst_mem_cnt[i] += 1
    elif(blocking == 2):
        #mov is blocking, have to append a stall cycle for all pes
        for i in range(pe_id, arch.num_pe):
            if(i == pe_id):
                arch.inst_list[i].append(inst_word)
                arch.inst_mem_cnt[i] += 1
            else:
                arch.inst_list[i].append(add_stall((arch.pe_mult + ia_pad * ia_pad) * (pe_ic_max/arch.pe_ic) * 12 + 32))
                arch.inst_mem_cnt[i] += 1

def mov_ltg_blocking(ias, weights, pe_id, stride=1, pe_row_max=4, pe_col_max=4, ia_row_block=0, ia_col_block=0, ia_row_size=0, ia_col_size=0, ia_pad=0, oa_pad=0, pe_ic_size=0, pe_oc_start=0, ia_mem_buffer=0, oa_mem_buffer=0, oa_mem_addr=0):

    inst_vec = clear_inst()

    #mov
    inst_vec.valid = 1 
    inst_vec.opcode = 2 
    inst_vec.conv_clear_finished = 1

    #inst_vec.process_kernel_size = ia_pad 
    #inst_vec.output_kernel_size = oa_pad 

    #ic
    inst_vec.ic_size = pe_ic_size 
    inst_vec.start_ic = pe_oc_start 
    inst_vec.finish_ic = pe_ic_size + pe_oc_start
    inst_vec.oc_size = weights.shape[0] 

    #set ia
    inst_vec.ia_row_size = ia_row_size 
    inst_vec.ia_col_size = ia_col_size 

    #set oa
    inst_vec.oa_row_size = ias.shape[1]/stride
    inst_vec.oa_col_size = ias.shape[2]/stride
    inst_vec.ia_row_start = ia_row_size * ia_row_block 
    inst_vec.ia_row_end = ia_row_size * ia_row_block + ia_row_size 
    inst_vec.ia_col_start = ia_col_size * ia_col_block 
    inst_vec.ia_col_end = ia_col_size * ia_col_block + ia_col_size

    #from local bank
    inst_vec.ia_mem_addr_0 = 0
    inst_vec.ia_mem_dir_0 = 15
    inst_vec.ia_mem_buffer_0 = ia_mem_buffer 
    #from shared global
    inst_vec.oa_mem_addr = oa_mem_addr 
    inst_vec.oa_mem_dir = 8 
    inst_vec.oa_mem_buffer = oa_mem_buffer

    inst_word = makeinst(inst_vec)
    #mov is blocking, have to append a stall cycle for all pes
    for i in range(0, arch.num_pe):
        if(i == pe_id):
            arch.inst_list[i].append(inst_word)
            arch.inst_mem_cnt[i] += 1
        else:
            #arch.inst_list[i].append(add_stall(10))
            arch.inst_list[i].append(add_stall(arch.pe_mult * (pe_ic_size/arch.pe_ic) * 6 + 64))
            arch.inst_mem_cnt[i] += 1

def conv_non_blocking(pe_id, pe_oc_max=128, pe_ic_max=128, ia_pad=1, oa_pad=0, stride=1, shift=0, src_buf=0, dst_buf=1, relu=0, rram_addr=0):

    inst_vec = clear_inst()

    #conv
    inst_vec.valid = 1 
    inst_vec.opcode = 0 
    inst_vec.max_0_avg_1 = relu 
    inst_vec.process_kernel_size = ia_pad * 2 + 1
    inst_vec.output_kernel_size = oa_pad * 2 + 1 
    inst_vec.stride = stride 
    inst_vec.ic_size = pe_ic_max
    inst_vec.finish_ic = pe_ic_max 
    inst_vec.oc_size = pe_oc_max 
    inst_vec.finish_oc = pe_oc_max 
    inst_vec.ia_col_size = arch.pe_mult + ia_pad * 2
    inst_vec.ia_row_size = arch.pe_mult + ia_pad * 2
    inst_vec.oa_row_size = arch.pe_mult/stride + oa_pad * 2
    inst_vec.oa_col_size = arch.pe_mult/stride + oa_pad * 2
    inst_vec.shift_width = shift # total 9 = conv 7 + add 2 
    #input is @ buffer 0
    inst_vec.ia_mem_addr_0 = 0
    inst_vec.ia_mem_dir_0 = 15 #local 
    inst_vec.ia_mem_buffer_0 = src_buf
    #input is @ buffer 1
    inst_vec.oa_mem_addr = 0
    inst_vec.oa_mem_dir = 15 #local
    inst_vec.oa_mem_buffer = dst_buf
    inst_vec.rram_addr = rram_addr

    inst_word = makeinst(inst_vec) 
    arch.inst_list[pe_id].append(inst_word)
    arch.inst_mem_cnt[pe_id] += 1

def pool_non_blocking(pe_id, pe_oc_max=128, pe_ic_max=128, process_kernel_size=3, ia_pad=1, oa_pad=0, stride=1, shift=0, src_buf=0, dst_buf=1, max_0_avg_1=0, relu=0):

    inst_vec = clear_inst()

    #conv
    inst_vec.valid = 1 
    inst_vec.opcode = 1 
    inst_vec.max_0_avg_1 = max_0_avg_1 
    inst_vec.process_kernel_size = process_kernel_size
    inst_vec.output_kernel_size = oa_pad * 2 + 1 
    inst_vec.stride = stride 
    inst_vec.sparse_fc_clean = relu 
    inst_vec.ic_size = pe_ic_max
    inst_vec.finish_ic = pe_ic_max 
    inst_vec.oc_size = pe_oc_max 
    inst_vec.finish_oc = pe_oc_max 
    inst_vec.ia_col_size = arch.pe_mult + ia_pad * 2
    inst_vec.ia_row_size = arch.pe_mult + ia_pad * 2
    inst_vec.oa_row_size = arch.pe_mult/stride + oa_pad * 2
    inst_vec.oa_col_size = arch.pe_mult/stride + oa_pad * 2
    inst_vec.shift_width = shift # total 9 = conv 7 + add 2 
    #input is @ buffer 0
    inst_vec.ia_mem_addr_0 = 0
    inst_vec.ia_mem_dir_0 = 15 #local 
    inst_vec.ia_mem_buffer_0 = src_buf
    #input is @ buffer 1
    inst_vec.oa_mem_addr = 0
    inst_vec.oa_mem_dir = 15 #local
    inst_vec.oa_mem_buffer = dst_buf

    inst_word = makeinst(inst_vec) 
    arch.inst_list[pe_id].append(inst_word)
    arch.inst_mem_cnt[pe_id] += 1

def add_non_blocking(pe_master, pe_slave, pe_ic_max=128, ia_row_size=arch.pe_mult, ia_col_size=arch.pe_mult, ia_pad=0, oa_pad=0, shift=0, m_src_buf=0, m_dst_buf=1, s_src_buf=0, relu=0):

    inst_vec = clear_inst()

    #add
    inst_vec.valid = 1 
    inst_vec.opcode = 3  
    inst_vec.max_0_avg_1 = relu 
    inst_vec.process_kernel_size = ia_pad * 2 + 1 
    inst_vec.output_kernel_size = oa_pad * 2 + 1
    inst_vec.ic_size = pe_ic_max 
    inst_vec.oc_size = pe_ic_max 
    inst_vec.ia_row_size = ia_row_size + ia_pad * 2 
    inst_vec.ia_col_size = ia_col_size + ia_pad * 2 
    inst_vec.oa_row_size = ia_row_size + oa_pad * 2
    inst_vec.oa_col_size = ia_col_size + oa_pad * 2
    inst_vec.shift_width = shift # total 8 = conv 6 + add 1 + add 1 
    #master src
    inst_vec.ia_mem_dir_0 = 15 
    inst_vec.ia_mem_buffer_0 = m_src_buf 
    inst_vec.ia_mem_addr_0 = 0
    #slave src
    inst_vec.ia_mem_dir_1 = arch.get_neighbor_dir(pe_master, pe_slave) 
    inst_vec.ia_mem_buffer_1 = s_src_buf
    inst_vec.ia_mem_addr_1 = 0

    inst_vec.oa_mem_dir = 15 #local
    inst_vec.oa_mem_buffer = m_dst_buf
    inst_vec.oa_mem_addr = 0

    inst_word = makeinst(inst_vec)

    arch.inst_list[pe_master].append(inst_word)
    arch.inst_mem_cnt[pe_master] += 1

def add_row_non_blocking(pe_ic_max=128, ia_row_size=arch.pe_mult, ia_col_size=arch.pe_mult, ia_pad=0, oa_pad=0, shift=0, m_src_buf=0, m_dst_buf=1, s_src_buf=0, relu=0):

    #add 8x8 on 8 pes concurrently 
    for pe_id in range(0, arch.num_pe):
        if(pe_id == 1 or pe_id == 5 or pe_id == 9 or pe_id == 13):
            add_non_blocking(pe_id, pe_id-1, pe_ic_max, ia_row_size, ia_col_size, \
                            ia_pad=0, oa_pad=0, shift=1, m_src_buf=1, m_dst_buf=0, s_src_buf=1, relu=0)
        elif(pe_id == 2 or pe_id == 6 or pe_id == 10 or pe_id == 14):
            add_non_blocking(pe_id, pe_id+1, pe_ic_max, ia_row_size, ia_col_size, \
                            ia_pad=0, oa_pad=0, shift=1, m_src_buf=1, m_dst_buf=0, s_src_buf=1, relu=0)

    #add 8x8 on 4 pes concurrently 
    for pe_id in range(0, arch.num_pe):
        if(pe_id == 1 or pe_id == 5 or pe_id == 9 or pe_id == 13):
            add_non_blocking(pe_id, pe_id+1, pe_ic_max, ia_row_size, ia_col_size, \
                            ia_pad=0, oa_pad=0, shift=1, m_src_buf=0, m_dst_buf=1, s_src_buf=0, relu=relu)

def add_all_non_blocking(pe_ic_max=128, ia_row_size=arch.pe_mult, ia_col_size=arch.pe_mult, ia_pad=0, oa_pad=0, shift=0, m_src_buf=0, m_dst_buf=1, s_src_buf=0):

    add_row_non_blocking(pe_ic_max, ia_row_size, ia_col_size, ia_pad=0, oa_pad=0, shift=0, m_src_buf=0, m_dst_buf=1, s_src_buf=0)

    #add 8x8 on 2 pes concurrently 
    for pe_id in range(0, arch.num_pe):
        if(pe_id == 5):
            add_non_blocking(pe_id, pe_id-4, pe_ic_max, ia_row_size, ia_col_size, \
                            ia_pad=0, oa_pad=0, shift=1, m_src_buf=1, m_dst_buf=0, s_src_buf=1)
        elif(pe_id == 9):
            add_non_blocking(pe_id, pe_id+4, pe_ic_max, ia_row_size, ia_col_size, \
                            ia_pad=0, oa_pad=0, shift=1, m_src_buf=1, m_dst_buf=0, s_src_buf=1)

    #add 8x8 on 1 pes finally 
    for pe_id in range(0, arch.num_pe):
        if(pe_id == 5):
            add_non_blocking(pe_id, pe_id+4, pe_ic_max, ia_row_size, ia_col_size, \
                            ia_pad=0, oa_pad=0, shift=1, m_src_buf=0, m_dst_buf=1, s_src_buf=0)

def sync_blocking():
    inst_vec = clear_inst()
    #sync
    for i in range(0, arch.num_pe):
        inst_vec.valid = 1 
        inst_vec.opcode = 6  
        inst_vec.sparse_fc_process = 1

        inst_word = makeinst(inst_vec)

        arch.inst_list[i].append(inst_word)
        arch.inst_mem_cnt[i] += 1

def gen_conv_inst_ia_split(layer, src_addr, dst_addr, RRAM_offset, RRAM_words, running_pe):
    if(layer.opcode != 'conv'):
        print ('invalid layer type')
        return

    #must satify for ia split only
    if(layer.pe_ic_max != layer.ic_total or layer.pe_oc_max != layer.oc_total):
        print ('invalid split type')
        return

    inst_begin_list = []
    for pe_id in range(0, arch.num_pe):
        inst_begin_list.append(len(arch.inst_list[pe_id]))

    pe_row_max = int(math.ceil(float(layer.ia_size)/float(arch.pe_mult)))
    pe_col_max = int(math.ceil(float(layer.ia_size)/float(arch.pe_mult)))
    ia_pad = (layer.process_kernel_size - 1)/2
    oa_pad = (layer.output_kernel_size - 1)/2

    #only work because of 4x4
    #compute all ic & oc for a same block first
    for row_cnt in range (0, pe_row_max):
        for col_cnt in range(0, pe_col_max):
            
            #run full sequence on one block before moving to another block
            pe_id = (col_cnt + row_cnt * pe_col_max)%running_pe
            #mov 8x8 blocks to a pe
            mov_gtl_blocking(layer.ia, layer.w, pe_id, layer.pe_oc_max, layer.pe_ic_max, \
                            pe_row_max, pe_col_max, row_cnt, col_cnt, \
                            ia_pad, oa_pad, 0, 0, src_addr, 0, 2)

            #conv 8x8 on each pe concurrently 
            conv_non_blocking(pe_id, layer.pe_oc_max, layer.pe_ic_max, \
                            ia_pad, oa_pad, layer.stride, layer.right_shift, src_buf=0, dst_buf=1, relu=0, rram_addr=RRAM_offset+len(RRAM_words[pe_id])/arch.rram_banks)
                
            #mov 8x8 block back to global
            mov_ltg_blocking(layer.ia, layer.w, pe_id, layer.stride, pe_row_max, pe_col_max, \
                            row_cnt, col_cnt, arch.pe_mult/layer.stride, arch.pe_mult/layer.stride, ia_pad=0, oa_pad=0, \
                            pe_ic_size=layer.oc_total, pe_oc_start=0, ia_mem_buffer=1, oa_mem_buffer=1, oa_mem_addr=dst_addr)

            #sync for next processing
            if(pe_id == running_pe-1):
            #if(pe_id == arch.num_pe-1):
                sync_blocking()

    inst_end_list = []
    for pe_id in range(0, arch.num_pe):
        inst_end_list.append(len(arch.inst_list[pe_id]))

    return inst_begin_list, inst_end_list

def gen_pool_inst_ia_split(layer, src_addr, dst_addr):
    if(layer.opcode != 'pool'):
        print ('invalid layer type')
        return

    #must satify for ia split only
    if(layer.pe_ic_max != layer.ic_total or layer.pe_oc_max != layer.oc_total):
        print ('invalid split type')
        return

    inst_begin_list = []
    for pe_id in range(0, arch.num_pe):
        inst_begin_list.append(len(arch.inst_list[pe_id]))

    pe_row_max = int(math.ceil(float(layer.ia_size)/float(arch.pe_mult)))
    pe_col_max = int(math.ceil(float(layer.ia_size)/float(arch.pe_mult)))
    if(layer.max_0_avg_1 == 0):
        ia_pad = (layer.process_kernel_size - 1)/2
        oa_pad = (layer.output_kernel_size - 1)/2
    else:
        ia_pad = 0 
        oa_pad = (layer.output_kernel_size - 1)/2

    #only work because of 4x4
    #compute all ic & oc for a same block first
    for row_cnt in range (0, pe_row_max):
        for col_cnt in range(0, pe_col_max):
            
            #run full sequence on one block before moving to another block
            pe_id = (col_cnt + row_cnt * pe_col_max)%arch.num_pe
            #mov 8x8 blocks to a pe
            mov_gtl_blocking(layer.ia, layer.w, pe_id, layer.pe_oc_max, layer.pe_ic_max, \
                            pe_row_max, pe_col_max, row_cnt, col_cnt, \
                            ia_pad, oa_pad, 0, 0, src_addr, 0, 2)

            #conv 8x8 on each pe concurrently 
            pool_non_blocking(pe_id, layer.pe_oc_max, layer.pe_ic_max, layer.process_kernel_size, \
                            ia_pad, oa_pad, layer.stride, layer.right_shift, src_buf=0, dst_buf=1, max_0_avg_1=layer.max_0_avg_1, relu=layer.relu)
                
            #mov 8x8 block back to global
            mov_ltg_blocking(layer.ia, layer.w, pe_id, layer.stride, pe_row_max, pe_col_max, \
                            row_cnt, col_cnt, arch.pe_mult/layer.stride, arch.pe_mult/layer.stride, ia_pad=0, oa_pad=0, \
                            pe_ic_size=layer.oc_total, pe_oc_start=0, ia_mem_buffer=1, oa_mem_buffer=1, oa_mem_addr=dst_addr)

            #sync for next processing
            if(pe_id == arch.num_pe-1):
                sync_blocking()

    #finish, sync all pe
    if((pe_row_max * pe_col_max)%arch.num_pe != 0):
        sync_blocking()

    inst_end_list = []
    for pe_id in range(0, arch.num_pe):
        inst_end_list.append(len(arch.inst_list[pe_id]))

    return inst_begin_list, inst_end_list

def gen_add_inst_ia_split(layer, src_addr1, src_addr2, dst_addr):
    if(layer.opcode != 'add'):
        print ('invalid layer type')
        return

    #must satify for ia split only
    if(layer.pe_ic_max != layer.ic_total or layer.pe_oc_max != layer.oc_total):
        print ('invalid split type')
        return

    inst_begin_list = []
    for pe_id in range(0, arch.num_pe):
        inst_begin_list.append(len(arch.inst_list[pe_id]))

    pe_row_max = int(math.ceil(float(layer.ia_size)/float(arch.pe_mult)))
    pe_col_max = int(math.ceil(float(layer.ia_size)/float(arch.pe_mult)))
    ia_pad = (layer.process_kernel_size - 1)/2
    oa_pad = (layer.output_kernel_size - 1)/2

    #only work because of 4x4
    #compute all ic & oc for a same block first
    for row_cnt in range (0, pe_row_max):
        for col_cnt in range(0, pe_col_max):
            
            #run full sequence on one block before moving to another block
            pe_id = (col_cnt + row_cnt * pe_col_max)%(arch.num_pe/2)
            #mov 8x8 blocks to a pe
            mov_gtl_blocking(layer.ia, layer.w, 2*pe_id, layer.pe_oc_max, layer.pe_ic_max, \
                            pe_row_max, pe_col_max, row_cnt, col_cnt, \
                            ia_pad, oa_pad, 0, 0, src_addr1, 0, 2)
                            
            mov_gtl_blocking(layer.ia_add, layer.w, 2*pe_id+1, layer.pe_oc_max, layer.pe_ic_max, \
                            pe_row_max, pe_col_max, row_cnt, col_cnt, \
                            ia_pad, oa_pad, 0, 0, src_addr2, 0, 2)

            #sync for processing
            if(pe_id == arch.num_pe/2-1):
                sync_blocking()

                #add 8x8 on each pe concurrently 
                for i in range(0, arch.num_pe/2): 
                    add_non_blocking(2*i, 2*i+1, \
                                    layer.pe_ic_max, min(layer.ia_size, arch.pe_mult), min(layer.ia_size, arch.pe_mult), \
                                    ia_pad=ia_pad, oa_pad=oa_pad, shift=1, m_src_buf=0, m_dst_buf=1, s_src_buf=0, relu=0)

                    #mov 8x8 block back to global
                    mov_ltg_blocking(layer.ia, layer.w, 2*i, layer.stride, pe_row_max, pe_col_max, \
                                    i/pe_col_max, i%pe_col_max, arch.pe_mult/layer.stride, arch.pe_mult/layer.stride, ia_pad=0, oa_pad=0, \
                                    pe_ic_size=layer.oc_total, pe_oc_start=0, ia_mem_buffer=1, oa_mem_buffer=1, oa_mem_addr=dst_addr)

    if((pe_row_max * pe_col_max) % (arch.num_pe/2) != 0):
        sync_blocking()
        #add 8x8 on each pe concurrently 
        for i in range(0, (pe_row_max * pe_col_max) % (arch.num_pe/2)): 
            #add 8x8 on each pe concurrently 
            add_non_blocking(2*i, 2*i+1, \
                            layer.pe_ic_max, min(layer.ia_size, arch.pe_mult), min(layer.ia_size, arch.pe_mult), \
                            ia_pad=ia_pad, oa_pad=oa_pad, shift=1, m_src_buf=0, m_dst_buf=1, s_src_buf=0, relu=0)

            #mov 8x8 block back to global
            mov_ltg_blocking(layer.ia, layer.w, 2*i, layer.stride, pe_row_max, pe_col_max, \
                            i/pe_col_max, i%pe_col_max, arch.pe_mult/layer.stride, arch.pe_mult/layer.stride, ia_pad=0, oa_pad=0, \
                            pe_ic_size=layer.oc_total, pe_oc_start=0, ia_mem_buffer=1, oa_mem_buffer=1, oa_mem_addr=dst_addr)

    #finish, sync all pe
    if((pe_row_max * pe_col_max)%(arch.num_pe/2) != 0):
        sync_blocking()

    inst_end_list = []
    for pe_id in range(0, arch.num_pe):
        inst_end_list.append(len(arch.inst_list[pe_id]))

    return inst_begin_list, inst_end_list

def gen_conv_inst_mixed_split(layer, src_addr, dst_addr, RRAM_words):
    if(layer.opcode != 'conv'):
        print ('invalid layer type')
        return

    inst_begin_list = []
    for pe_id in range(0, arch.num_pe):
        inst_begin_list.append(len(arch.inst_list[pe_id]))

    pe_row_max = int(math.ceil(float(layer.ia_size)/float(arch.pe_mult)))
    pe_col_max = int(math.ceil(float(layer.ia_size)/float(arch.pe_mult)))
    ia_pad = (layer.process_kernel_size - 1)/2
    oa_pad = (layer.output_kernel_size - 1)/2

    #only work because of 4x4
    #compute all ic & oc for a same block first
    for row_cnt in range (0, pe_row_max):
        for col_cnt in range(0, pe_col_max):
            
            #run full sequence on one block before moving to another block
            #mov 8x8 blocks to each pe
            for pe_id in range(0, arch.num_pe):
                oc_cnt = math.ceil(float(pe_id)/4.0)
                ic_cnt = pe_id%4
                pe_oc_start = oc_cnt * layer.pe_oc_max
                pe_ic_start = ic_cnt * layer.pe_ic_max

                #mov 8x8 blocks to a pe
                mov_gtl_blocking(layer.ia, layer.w, pe_id, layer.pe_oc_max, layer.pe_ic_max, \
                                pe_row_max, pe_col_max, row_cnt, col_cnt, \
                                ia_pad, oa_pad, pe_oc_start, pe_ic_start, src_addr, 0, 1)

            #conv 8x8 on each pe concurrently 
            for pe_id in range(0, arch.num_pe):
                conv_non_blocking(pe_id, layer.pe_oc_max, layer.pe_ic_max, \
                                ia_pad, oa_pad, layer.stride, layer.right_shift-2, src_buf=0, dst_buf=1, relu=0, rram_addr=len(RRAM_words[pe_id])/arch.rram_banks)
                
            #sync for next processing
            sync_blocking()

            #merge conv outputs
            add_row_non_blocking(layer.pe_ic_max, arch.pe_mult/layer.stride, arch.pe_mult/layer.stride, ia_pad=0, oa_pad=0, shift=0, m_src_buf=0, m_dst_buf=1, s_src_buf=0, relu=layer.relu)

            #mov 8x8 block back to global
            for i in range(0, 4):
                mov_ltg_blocking(layer.ia, layer.w, arch.pe_row_master[i], layer.stride, pe_row_max, pe_col_max, \
                                row_cnt, col_cnt, arch.pe_mult/layer.stride, arch.pe_mult/layer.stride, ia_pad=0, oa_pad=0, \
                                pe_ic_size=layer.pe_oc_max, pe_oc_start=i*layer.pe_oc_max, ia_mem_buffer=1, oa_mem_buffer=1, oa_mem_addr=dst_addr)

            #sync for next processing
            sync_blocking()

    inst_end_list = []
    for pe_id in range(0, arch.num_pe):
        inst_end_list.append(len(arch.inst_list[pe_id]))

    return inst_begin_list, inst_end_list



