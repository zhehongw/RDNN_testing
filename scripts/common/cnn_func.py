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
from split_func import *
from writer_func import *
from mem_func import *

numpy.random.seed(9001)

def clear_layer():
    layer = arch.cnn_layer()
    return layer

def gen_layer(layer, rand_input):
    print layer.name
    if(layer.opcode == 'conv'):
        layer.oa_size = (layer.ia_size - layer.process_kernel_size + 1)/layer.stride + layer.output_kernel_size - 1
        #random filters
        layer.w = random_weights(layer.oc_total, layer.ic_total, layer.process_kernel_size)
        if(rand_input):
            #random IAs 
            layer.ia = random_ias(layer.ic_total, layer.ia_size, layer.process_kernel_size)
        else:
            layer.ia = numpy.zeros((layer.ic_total, layer.ia_size, layer.ia_size), dtype=numpy.int) 
        #zero oa 
        layer.oa = numpy.zeros((layer.oc_total, layer.oa_size, layer.oa_size), dtype=numpy.int)
    elif(layer.opcode == 'pool'):
        layer.oa_size = (layer.ia_size - layer.process_kernel_size + 1)/layer.stride + layer.output_kernel_size - 1
        if(rand_input):
            #random IAs 
            layer.ia = random_ias(layer.ic_total, layer.ia_size, layer.process_kernel_size)
        else:
            layer.ia = numpy.zeros((layer.ic_total, layer.ia_size, layer.ia_size), dtype=numpy.int) 
        #zero oa 
        layer.oa = numpy.zeros((layer.oc_total, layer.oa_size, layer.oa_size), dtype=numpy.int)
    elif(layer.opcode == 'add'):
        layer.oa_size = layer.ia_size
        if(rand_input):
            #random IAs 
            layer.ia = random_ias(layer.ic_total, layer.ia_size, layer.process_kernel_size)
            layer.ia_add = random_ias(layer.ic_total, layer.ia_size, layer.process_kernel_size)
        else:
            layer.ia = numpy.zeros((layer.ic_total, layer.ia_size, layer.ia_size), dtype=numpy.int) 
            layer.ia_add = numpy.zeros((layer.ic_total, layer.ia_size, layer.ia_size), dtype=numpy.int) 
        #zero oa 
        layer.oa = numpy.zeros((layer.oc_total, layer.oa_size, layer.oa_size), dtype=numpy.int)
    else:
        print('ERROR: invalid opcode!!!')
    return layer

def random_weights(oc_total, ic_total, kernel_size):
    #random sparse filters
    w = numpy.random.randint(-8, high=16, size=(oc_total, ic_total, kernel_size, kernel_size)) 
    sparse_loc = (numpy.random.randint(-3, high=4, size=(oc_total, ic_total, kernel_size, kernel_size))).clip(min=0)
    sparse_w = numpy.multiply(w, sparse_loc)
    print("density: " + str(float(numpy.count_nonzero(sparse_w))/float(ic_total*oc_total*kernel_size*kernel_size)))
    return sparse_w

def random_ias(ic_total, ia_size, kernel_size):
    #random dense ias
    ia = numpy.random.randint(-16, high=16, size=(ic_total, ia_size, ia_size))
    ##zero padding
    #for ic_cnt in range (0, ic_total):
    #    for row in range (0, ia_size):
    #        for col in range (0, ia_size):
    #            if(row < (kernel_size-1)/2 or col < (kernel_size-1)/2 or row >= ia_size - (kernel_size-1)/2 or col >= ia_size - (kernel_size-1)/2):
    #                ia[ic_cnt][row][col] = 0 
    return ia 

def conv_oa(ias, weights, shift):
    oc = weights.shape[0]
    ic = ias.shape[0]
    ia_size = ias.shape[1]
    pad_size = (weights.shape[2] - 1)/2
    #ia_pad = numpy.zeros((ic, ia_size+pad_size*2, ia_size+pad_size*2), dtype=numpy.int) 
    #ia_pad[:,pad_size:ia_size+pad_size,pad_size:ia_size+pad_size] = ias
    oa_raw = numpy.zeros((oc, ia_size, ia_size), dtype=numpy.int) 
    for oc_cnt in range (0, oc):
        for ic_cnt in range (0, ic):
            oa_raw[oc_cnt] = numpy.add(oa_raw[oc_cnt], convolveim(ias[ic_cnt], weights[oc_cnt][ic_cnt], mode='constant'))

    oa = numpy.right_shift(oa_raw, shift)
    return oa, oa_raw

def pool_oa_max(ias, shift, kernel_size):
    ic = ias.shape[0]
    ia_size = ias.shape[1]
    pad_size = (kernel_size - 1)/2
    oa_raw = numpy.zeros((ic, ia_size, ia_size), dtype=numpy.int) 
    for ic_cnt in range (0, ic):
        for row_cnt in range (0, ia_size):
            for col_cnt in range (0, ia_size):
                block = ias[ic_cnt, \
                        max(0,(row_cnt-pad_size)):min(row_cnt+pad_size+1,ia_size), \
                        max(0,(col_cnt-pad_size)):min(col_cnt+pad_size+1,ia_size)]
                if(block.shape[0] < kernel_size or block.shape[1] < kernel_size):
                    oa_raw[ic_cnt][row_cnt][col_cnt] = max(numpy.amax(block),0)
                else:
                    oa_raw[ic_cnt][row_cnt][col_cnt] = numpy.amax(block)

    oa = numpy.right_shift(oa_raw, shift)
    return oa, oa_raw

def pool_oa_avg(ias, shift, kernel_size):
    ic = ias.shape[0]
    ia_size = ias.shape[1]
    oa_raw = numpy.zeros((ic, ia_size, ia_size), dtype=numpy.int) 
    for ic_cnt in range (0, ic):
        for row_cnt in range (0, ia_size):
            for col_cnt in range (0, ia_size):
                block = ias[ic_cnt, \
                        max(0,row_cnt):min(row_cnt+kernel_size,ia_size), \
                        max(0,col_cnt):min(col_cnt+kernel_size,ia_size)]
                oa_raw[ic_cnt][row_cnt][col_cnt] = numpy.sum(block)

    oa = numpy.right_shift(oa_raw, shift)
    return oa, oa_raw

def add_oa(ias, ias_add, shift):
    ic = ias.shape[0]
    ia_size = ias.shape[1]
    oa_raw = numpy.zeros((ic, ia_size, ia_size), dtype=numpy.int) 
    oa_raw = numpy.add(ias, ias_add)
    oa = numpy.right_shift(oa_raw, shift)
    return oa, oa_raw

def merge_oa(oas, ic_total, pe_ic_max, oc_total, pe_oc_max):
    levels = math.log(ic_total/pe_ic_max, 2)
    chunks = oc_total/pe_oc_max

    oa = numpy.zeros((oas[0].shape[0]*chunks,oas[0].shape[1],oas[0].shape[2]), dtype=numpy.int)

    if(levels == 0):
        oa = oas[0]

    oas_L1 = []
    if(levels >= 1):
        #level 1
        for block_id in range (0, 8):
            oas_L1.append(numpy.right_shift( oas[block_id*2] + oas[block_id*2+1], 1))
        if(levels == 1):        
            for oc_chunk in range (0, chunks):
                oa[oc_chunk*oas[0].shape[0]:(oc_chunk+1)*oas[0].shape[0],:,:] = copy.deepcopy(oas_L1[oc_chunk])

    oas_L2 = []
    if(levels >= 2):
        #level 2
        for block_id in range (0, 4):
            oas_L2.append(numpy.right_shift( oas_L1[block_id*2] + oas_L1[block_id*2+1], 1))
        if(levels == 2):        
            for oc_chunk in range (0, chunks):
                oa[oc_chunk*oas[0].shape[0]:(oc_chunk+1)*oas[0].shape[0],:,:] = copy.deepcopy(oas_L2[oc_chunk])


    oas_L3 = []
    if(levels >= 3):
        #level 3
        for block_id in range (0, 2):
            oas_L3.append(numpy.right_shift( oas_L2[block_id*2] + oas_L2[block_id*2+1], 1))
        if(levels == 3):        
            for oc_chunk in range (0, chunks):
                oa[oc_chunk*oas[0].shape[0]:(oc_chunk+1)*oas[0].shape[0],:,:] = copy.deepcopy(oas_L3[oc_chunk])

    oas_L4 = []
    if(levels >= 4):
        #level 4
        for block_id in range (0, 1):
            oas_L4.append(numpy.right_shift( oas_L3[block_id*2] + oas_L3[block_id*2+1], 1))
        if(levels == 4):        
            for oc_chunk in range (0, chunks):
                oa[oc_chunk*oas[0].shape[0]:(oc_chunk+1)*oas[0].shape[0],:,:] = copy.deepcopy(oas_L3[oc_chunk])

    return oa 

def merge_oa_all(oas):
    if(len(oas) != 16):
        print ("ERROR: cannot merge")
        return

    oas_L1 = []
    #level 1
    for block_id in range (0, 8):
        oas_L1.append(numpy.right_shift( oas[block_id*2] + oas[block_id*2+1], 1))

    oas_L2 = []
    #level 2
    for block_id in range (0, 4):
        oas_L2.append(numpy.right_shift( oas_L1[block_id*2] + oas_L1[block_id*2+1], 1))

    oas_L3 = []
    #level 3
    for block_id in range (0, 2):
        oas_L3.append(numpy.right_shift( oas_L2[block_id*2] + oas_L2[block_id*2+1], 1))

    oas_L4 = []
    #level 4
    for block_id in range (0, 1):
        oas_L4.append(numpy.right_shift( oas_L3[block_id*2] + oas_L3[block_id*2+1], 1))

    return oas_L4[0]

def concat_oa(oas):
    if(len(oas) != 16):
        print ("ERROR: cannot merge")
        return

    oa = numpy.zeros((oas[0].shape[0]*16,oas[0].shape[1],oas[0].shape[2]), dtype=numpy.int)

    for oc_id in range (0, 16):
        oa[block_id*oas[0].shape[0]+oas[0].shape[0]:block_id*oas[0].shape[0],:,:] = copy.deepcopy(oas[block_id])

    return oa

def subsample_pad_oa(oa, stride, relu):
    print oa.shape
    oa_sub = numpy.zeros((oa.shape[0],oa.shape[1]/stride,oa.shape[2]/stride), dtype=numpy.int)
    if(stride == 1 or stride == 2 or stride == 4 or stride == 8):
        for oc_cnt in range (0, oa_sub.shape[0]):
            for row in range (0, oa_sub.shape[1]):
                for col in range (0, oa_sub.shape[2]):
                    if(relu == 0 or oa[oc_cnt][stride*row][stride*col] > 0):
                        oa_sub[oc_cnt][row][col] = oa[oc_cnt][stride*row][stride*col]

    else:
        print ("ERROR: cannot subsample")
    return oa_sub

def gen_conv_input_ia_split(layer, shared_src_buf, shared_dst_buf, RRAM_words, RRAM_words_full, running_pe):
    if(layer.opcode != 'conv'):
        print ('ERROR: invalid layer type')
        return

    #must satify for ia split only
    if(layer.pe_ic_max != layer.ic_total or layer.pe_oc_max != layer.oc_total):
        print ('ERROR: invalid split type')
        return

    ####################partition and compute###########################
    split_ia, split_oc, split_ic, num_blocks = get_split_pe_method(layer.ia, layer.w)
    print 'split_ia: ' + str(split_ia) + ' split_oc: ' + str(split_oc) + ' split_ic: ' + str(split_ic) + ' total_block: ' + str(num_blocks)

    #split IA/weights by channel
    ia_blocks = split_ias(layer.ia, layer.w, layer.pe_oc_max, layer.pe_ic_max)
    w_blocks = split_weights(layer.ia, layer.w, layer.pe_oc_max, layer.pe_ic_max)

    oa_blocks = []
    oa_blocks_raw = []
    #compute ground truth oa for each ic block 
    for i in range(0, len(ia_blocks)):
        oa_ic_block, oa_ic_block_raw = conv_oa(ia_blocks[i], w_blocks[i], layer.right_shift)
        oa_blocks.append(oa_ic_block)
        oa_blocks_raw.append(oa_ic_block_raw)

    #compute ground truth oa
    oa = merge_oa(oa_blocks, layer.ic_total, layer.pe_ic_max, layer.oc_total, layer.pe_oc_max)

    #compute ground truth oa with stride
    layer.oa = copy.deepcopy(subsample_pad_oa(oa, layer.stride, layer.relu))

    #write IA out
    ia_word_list = build_share_mem([layer.ia], [shared_src_buf])
    write_share_mem(ia_word_list, layer.name + '_ia')

    #write compressed weights out
    for i in range(0, len(w_blocks)):
        pe_id = i%running_pe
        weight_list, runlength_list, abs_loc_list = flatten_weight(w_blocks[i])
        weight_list_coded, runlength_list_coded = compress_weight(weight_list, runlength_list, pe_id)
        RRAM_word_list, RRAM_word_list_full = build_rram_mem(weight_list_coded, runlength_list_coded, abs_loc_list, pe_id)
        
        RRAM_words[pe_id] = RRAM_words[pe_id] + RRAM_word_list
        RRAM_words_full[pe_id] = RRAM_words_full[pe_id] + RRAM_word_list_full

    #write OA out
    oa_word_list = build_share_mem([layer.oa], [shared_dst_buf])
    write_share_mem(oa_word_list, layer.name + '_oa')

    write_ref_weights(layer.w, layer.name)
    write_ref_ias(layer.ia, layer.name)
    write_ref_oas(layer.oa, layer.name)

    ##debug outputs
    #write_ref_ias_partial(ia_blocks, layer.name)
    #write_ref_weights_partial(w_blocks, layer.name)
    #write_ref_oas_partial(oa_blocks, layer.name)

def gen_pool_input_ia_split(layer, shared_src_buf, shared_dst_buf):
    if(layer.opcode != 'pool'):
        print ('ERROR: invalid layer type')
        return

    #must satify for ia split only
    if(layer.pe_ic_max != layer.ic_total or layer.pe_oc_max != layer.oc_total):
        print ('ERROR: invalid split type')
        return

    ####################partition and compute###########################
    split_ia, split_oc, split_ic, num_blocks = get_split_pe_method(layer.ia, layer.w)
    print 'split_ia: ' + str(split_ia) + ' split_oc: ' + str(split_oc) + ' split_ic: ' + str(split_ic) + ' total_block: ' + str(num_blocks)

    #split IA/weights by channel
    ia_blocks = split_ias(layer.ia, layer.w, layer.pe_oc_max, layer.pe_ic_max)

    oa_blocks = []
    oa_blocks_raw = []
    #compute ground truth oa for each ic block 
    for i in range(0, len(ia_blocks)):
        if(layer.max_0_avg_1 == 0):
            oa_ic_block, oa_ic_block_raw = pool_oa_max(ia_blocks[i], layer.right_shift, layer.process_kernel_size)
        else:
            oa_ic_block, oa_ic_block_raw = pool_oa_avg(ia_blocks[i], layer.right_shift, layer.process_kernel_size)
        oa_blocks.append(oa_ic_block)
        oa_blocks_raw.append(oa_ic_block_raw)
        print oa_ic_block.shape

    #compute ground truth oa
    oa = merge_oa(oa_blocks, layer.ic_total, layer.pe_ic_max, layer.oc_total, layer.pe_oc_max)

    #compute ground truth oa with stride
    layer.oa = copy.deepcopy(subsample_pad_oa(oa, layer.stride, layer.relu))

    #write IA out
    ia_word_list = build_share_mem([layer.ia], [shared_src_buf])
    write_share_mem(ia_word_list, layer.name + '_ia')

    #write OA out
    oa_word_list = build_share_mem([layer.oa], [shared_dst_buf])
    write_share_mem(oa_word_list, layer.name + '_oa')

    write_ref_ias(layer.ia, layer.name)
    write_ref_oas(layer.oa, layer.name)

    ##debug outputs
    #write_ref_ias_partial(ia_blocks, layer.name)
    #write_ref_oas_partial(oa_blocks, layer.name)

def gen_add_input_ia_split(layer, shared_src_buf1, shared_src_buf2, shared_dst_buf):
    if(layer.opcode != 'add'):
        print ('ERROR: invalid layer type')
        return

    #must satify for ia split only
    if(layer.pe_ic_max != layer.ic_total or layer.pe_oc_max != layer.oc_total):
        print ('ERROR: invalid split type')
        return

    ####################partition and compute###########################
    split_ia, split_oc, split_ic, num_blocks = get_split_pe_method(layer.ia, layer.w)
    print 'split_ia: ' + str(split_ia) + ' split_oc: ' + str(split_oc) + ' split_ic: ' + str(split_ic) + ' total_block: ' + str(num_blocks)

    #split IA/weights by channel
    ia_blocks = split_ias(layer.ia, layer.w, layer.pe_oc_max, layer.pe_ic_max)
    ia_blocks_add = split_ias(layer.ia_add, layer.w, layer.pe_oc_max, layer.pe_ic_max)

    oa_blocks = []
    oa_blocks_raw = []
    #compute ground truth oa for each ic block 
    for i in range(0, len(ia_blocks)):
        oa_ic_block, oa_ic_block_raw = add_oa(ia_blocks[i], ia_blocks_add[i], layer.right_shift)
        oa_blocks.append(oa_ic_block)
        oa_blocks_raw.append(oa_ic_block_raw)

    #compute ground truth oa
    oa = merge_oa(oa_blocks, layer.ic_total, layer.pe_ic_max, layer.oc_total, layer.pe_oc_max)

    #compute ground truth oa with stride
    layer.oa = copy.deepcopy(subsample_pad_oa(oa, layer.stride, layer.relu))

    #write IA out
    ia_word_list = build_share_mem([layer.ia, layer.ia_add], [shared_src_buf1, shared_src_buf2])
    write_share_mem(ia_word_list, layer.name + '_ia')

    #write OA out
    oa_word_list = build_share_mem([layer.oa], [shared_dst_buf])
    write_share_mem(oa_word_list, layer.name + '_oa')

    write_ref_ias(layer.ia, layer.name + '_in0')
    write_ref_ias(layer.ia_add, layer.name + '_in1')
    write_ref_oas(layer.oa, layer.name)

    ##debug outputs
    #write_ref_ias_partial(ia_blocks, layer.name)
    #write_ref_oas_partial(oa_blocks, layer.name)

def gen_conv_input_mixed_split(layer, shared_src_buf, shared_dst_buf, RRAM_words, RRAM_words_full):
    if(layer.opcode != 'conv'):
        print ('ERROR: invalid layer type')
        return

    ####################partition and compute###########################
    split_ia, split_oc, split_ic, num_blocks = get_split_pe_method(layer.ia, layer.w)
    print 'split_ia: ' + str(split_ia) + ' split_oc: ' + str(split_oc) + ' split_ic: ' + str(split_ic) + ' total_block: ' + str(num_blocks)

    #split IA/weights by channel
    ia_blocks = split_ias(layer.ia, layer.w, layer.pe_oc_max, layer.pe_ic_max)
    w_blocks = split_weights(layer.ia, layer.w, layer.pe_oc_max, layer.pe_ic_max)

    oa_blocks = []
    oa_blocks_raw = []
    #compute ground truth oa for each ic block 
    for i in range(0, len(ia_blocks)):
        oa_ic_block, oa_ic_block_raw = conv_oa(ia_blocks[i], w_blocks[i], layer.right_shift-2)
        oa_blocks.append(oa_ic_block)
        oa_blocks_raw.append(oa_ic_block_raw)

    #compute ground truth oa
    oa = merge_oa(oa_blocks, layer.ic_total, layer.pe_ic_max, layer.oc_total, layer.pe_oc_max)

    #compute ground truth oa with stride
    layer.oa = copy.deepcopy(subsample_pad_oa(oa, layer.stride, layer.relu))

    #write IA out
    ia_word_list = build_share_mem([layer.ia], [shared_src_buf])
    write_share_mem(ia_word_list, layer.name + '_ia')

    #write compressed weights out
    for i in range(0, len(w_blocks)):
        pe_id = i%16
        weight_list, runlength_list, abs_loc_list = flatten_weight(w_blocks[i])
        weight_list_coded, runlength_list_coded = compress_weight(weight_list, runlength_list, pe_id)
        RRAM_word_list, RRAM_word_list_full = build_rram_mem(weight_list_coded, runlength_list_coded, abs_loc_list, pe_id)
        
        RRAM_words[pe_id] = RRAM_words[pe_id] + RRAM_word_list
        RRAM_words_full[pe_id] = RRAM_words_full[pe_id] + RRAM_word_list_full

    #write OA out
    oa_word_list = build_share_mem([layer.oa], [shared_dst_buf])
    write_share_mem(oa_word_list, layer.name + '_oa')

    write_ref_weights(layer.w, layer.name)
    write_ref_ias(layer.ia, layer.name)
    write_ref_oas(layer.oa, layer.name)

    ##debug outputs
    write_ref_ias_partial(ia_blocks, layer.name)
    write_ref_weights_partial(w_blocks, layer.name)
    write_ref_oas_partial(oa_blocks, layer.name)



