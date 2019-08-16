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

#def split_ias_image_mixed(ic_total, ia_size, kernel_size):
#    if(kernel_size == 7 or kernel_size == 5):
#        max_pe_ic = 64
#    else:
#        max_pe_ic = 128
#
#    if(ic_total < max_pe_ic):
#        #split image directly
#
#    else:
#
#        if(ia_size - kernel_size + 1 == 8):
#            #split channel directly
#
#        else:
#            #split image first
#
#            #then split channel 
#
#    return ia_blocks

def get_split_pe_ic_blocks(ias, weights):
    if(math.ceil(float(ias.shape[2]) / float(arch.pe_mult)) > 1 or math.ceil(float(ias.shape[1]) / float(arch.pe_mult)) > 1 or math.ceil(float(weights.shape[0]) / float(arch.max_pe_oc)) > 1):
        return False, math.ceil(float(ias.shape[0]) / float(arch.max_pe_ic))
    else:
        return True, math.ceil(float(ias.shape[0]) / float(arch.max_pe_ic))

def get_split_pe_oc_blocks(ias, weights):
    if(math.ceil(float(ias.shape[2]) / float(arch.pe_mult)) > 1 or math.ceil(float(ias.shape[1]) / float(arch.pe_mult)) > 1 or math.ceil(float(ias.shape[0]) / float(arch.max_pe_ic)) > 1):
        return False, math.ceil(float(weights.shape[0]) / float(arch.max_pe_oc))
    else:
        return True, math.ceil(float(weights.shape[0]) / float(arch.max_pe_oc))

def get_split_pe_ia_blocks(ias, weights):
    if(math.ceil(float(weights.shape[0]) / float(arch.max_pe_oc)) or math.ceil(float(ias.shape[0]) / float(arch.max_pe_ic)) > 1):
        return False, math.ceil(float(ias.shape[2]) / float(arch.pe_mult)) * math.ceil(float(ias.shape[1]) / float(arch.pe_mult))
    else:
        return True, math.ceil(float(ias.shape[2]) / float(arch.pe_mult)) * math.ceil(float(ias.shape[1]) / float(arch.pe_mult)) 

def get_split_pe_method(ias, weights):
    ia_succeed, ia_pes = get_split_pe_ia_blocks(ias, weights) 
    oc_succeed, oc_pes = get_split_pe_oc_blocks(ias, weights)
    ic_succeed, ic_pes = get_split_pe_ic_blocks(ias, weights)
    print 'ia_success: ' + str(ia_succeed) + ' ia blocks: ' + str(ia_pes)
    print 'oc_success: ' + str(oc_succeed) + ' oc blocks: ' + str(oc_pes)
    print 'ic_success: ' + str(ic_succeed) + ' ic blocks: ' + str(ic_pes)
    return not ia_succeed, not oc_succeed, not ic_succeed, (not ia_succeed) * ia_pes * (not oc_succeed) * oc_pes * (not ic_succeed) * ic_pes

def split_ias(ias, weights, oc_block, ic_block):
    #duplicate ic blocks across pes
    num_oc_blocks = max(weights.shape[0]/oc_block, 1)
    num_ic_blocks = ias.shape[0]/ic_block
    ia_blocks = []
    for oc_cnt in range(0, num_oc_blocks):
        for ic_cnt in range(0, num_ic_blocks):
            ia_block = ias[ic_cnt*ic_block:ic_cnt*ic_block+ic_block,:,:] 
            ia_blocks.append(ia_block)
    return ia_blocks

def split_weights(ias, weights, oc_block, ic_block):
    num_oc_blocks = weights.shape[0]/oc_block
    num_ic_blocks = weights.shape[1]/ic_block
    w_blocks = []
    if(num_ic_blocks == 1 and num_oc_blocks == 1):
        for i in range(0, arch.num_pe):
            w_blocks.append(weights)
    else:
        for oc_cnt in range(0, num_oc_blocks):
            for ic_cnt in range(0, num_ic_blocks):
                w_block = weights[oc_cnt*oc_block:oc_cnt*oc_block+oc_block,ic_cnt*ic_block:ic_cnt*ic_block+ic_block,:,:] 
                w_blocks.append(w_block)
    return w_blocks

def split_ias_by_image(ic_total, ia_size, kernel_size):
    row_blocks = (ia_size - (kernel_size - 1)/2)/arch.pe_mult
    col_blocks = (ia_size - (kernel_size - 1)/2)/arch.pe_mult
    halo = (kernel_size - 1)/2

    num_image_blocks = row_blocks * col_blocks
    ia_blocks = []
    for row in range(0, row_blocks):
        for col in range(0, col_blocks):
            ia_block = ia[:,row*arch.pe_mult+halo:row*arch.pe_mult+halo+arch.pe_mult,row*arch.pe_mult+halo:row*arch.pe_mult+halo+arch.pe_mult] 
            ia_blocks.append(ia_block)
    return ia_blocks

