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
    s = bin(n & int("1"*bits, 2))[2:]
    return ("{0:0>%s}" % (bits)).format(s)

def fill_rram_mem():
    for pe_id in range(0, arch.num_pe):
        for i in range(0, arch.rram_banks):
            for rest_addr in range(0, 32768-arch.rram_cnt[pe_id][i]):
                arch.rram_mem[pe_id][i].write('x' * 96 + '\n')
    for pe_id in range(0, arch.num_pe):
        arch.RRAM_file[pe_id].close()
        for i in range(0, arch.rram_banks):
            arch.rram_mem[pe_id][i].close()

    return 

def write_rram_mem(RRAM_words, RRAM_words_full):
    for pe_id in range(0, arch.num_pe):
        for item in RRAM_words_full[pe_id]:
            arch.RRAM_file[pe_id].write("%s\n" % item)

        i = 0
        for item in RRAM_words_full[pe_id]:
            arch.rram_mem[pe_id][i%arch.rram_banks].write(item + '\n') 
            arch.rram_cnt[pe_id][i%arch.rram_banks] = arch.rram_cnt[pe_id][i%arch.rram_banks] + 1
            i += 1

    fill_rram_mem()

    return

def write_share_mem(ia_words, name):
    #IA/OA GLOBAL SRAM
    shared_mem=[]
    for i in range(0, 4):
        shared_mem.append([])
        for j in range(0, 2):
            shared_mem[i].append(open('../data/' + name + '_shared_' + str(i) + '_' + str(j) + '.mem','w+'))

    #print ia_words[0]
    #print ia_words[16384]
    for i in range(0, len(ia_words)):
        #oa_mem_all[pe_id].write("%s\n" % item)
        shared_mem[i/8192][1].write(ia_words[i][0:128] + '\n') 
        shared_mem[i/8192][0].write(ia_words[i][128:256] + '\n') 
    for i in range(0, 4):
        for j in range(0, 2):
            shared_mem[i][j].close()

    return

def write_inst_mem():
    for i in range(0, arch.num_pe):
        for item in arch.inst_list[i]:
          arch.inst_txt[i].write("%s\n" % item)

    for i in range(0, arch.num_pe):
        word_cnt = 0
        for item in arch.inst_list[i]:
            arch.inst_mem[i][word_cnt/512][2].write("%s\n" % item[0:128])
            arch.inst_mem[i][word_cnt/512][1].write("%s\n" % item[128:256])
            arch.inst_mem[i][word_cnt/512][0].write("%s\n" % item[256:384])
            word_cnt += 1

    for i in range(0, arch.num_pe):
        for rest_addr in range(arch.inst_mem_cnt[i], 1024):
            arch.inst_mem[i][rest_addr/512][2].write('x' * 128 + '\n')
            arch.inst_mem[i][rest_addr/512][1].write('x' * 128 + '\n')
            arch.inst_mem[i][rest_addr/512][0].write('x' * 128 + '\n')

    for i in range(0, arch.num_pe):
        for j in range(0, 2):
            arch.inst_mem[i][j][2].close()
            arch.inst_mem[i][j][1].close()
            arch.inst_mem[i][j][0].close()

def write_ref_weights(sparse_w, name):
    weight_golden = open('../' + name + '_weight.txt','w+') 
    oc_total = sparse_w.shape[0]
    ic_total = sparse_w.shape[1]
    kernel_size = sparse_w.shape[2]
    for oc_cnt in range (0, oc_total):
        for ic_cnt in range (0, ic_total):
            weight_golden.write('w channel: [' + str(oc_cnt) + ', ' + str(ic_cnt) + ']\n')
            for row in range (0, kernel_size):
                for col in range (0, kernel_size):
                    weight_golden.write(str(format(sparse_w[oc_cnt][ic_cnt][row][col], '4d')) + '\t')
                weight_golden.write('\n')
    weight_golden.close()

def write_ref_ias(ia, name):
    ia_golden = open('../' + name + '_ia.txt','w+') 
    ic_total = ia.shape[0]
    ia_size = ia.shape[1]
    for ic_cnt in range (0, ic_total):
        ia_golden.write('ia channel: [' + str(ic_cnt) + ']\n')
        for row in range (0, ia_size):
            for col in range (0, ia_size):
                ia_golden.write(str(format(ia[ic_cnt][row][col], '4d')) + '\t')
            ia_golden.write('\n')
    ia_golden.close()

def write_ref_oas(oa, name):
    oa_golden = open('../' + name + '_oa.txt','w+') 
    oc_total = oa.shape[0]
    oa_size = oa.shape[1]
    for oc_cnt in range (0, oc_total):
        oa_golden.write('oa channel: [' + str(oc_cnt) + ']\n')
        for row in range (0, oa_size):
            for col in range (0, oa_size):
                oa_golden.write(str(format(oa[oc_cnt][row][col], '4d')) + '\t')
            oa_golden.write('\n')
    oa_golden.close()

def write_ref_ias_partial(ia_blocks, name):
    ia_partial_golden=[]
    num_pe = len(ia_blocks)
    ic = ia_blocks[0].shape[0]
    ia_size = ia_blocks[0].shape[1]
    for i in range(0, num_pe):
        ia_partial_golden.append(open('../debug/' + name + '_pe_' + str(i) + '_ia.txt','w+'))
        for ic_cnt in range (0, ic):
            ia_partial_golden[i].write('ia channel: [' + str(ic_cnt) + ']\n')
            for row in range (0, ia_size):
                for col in range (0, ia_size):
                    ia_partial_golden[i].write(str(format(ia_blocks[i][ic_cnt][row][col], '4d')) + '\t')
                ia_partial_golden[i].write('\n')
        ia_partial_golden[i].close()

def write_ref_weights_partial(w_blocks, name):
    w_partial_golden=[]
    num_pe = len(w_blocks)
    oc = w_blocks[0].shape[0]
    ic = w_blocks[0].shape[1]
    kernel_size = w_blocks[0].shape[2]
    for i in range(0, num_pe):
        w_partial_golden.append(open('../debug/' + name + '_pe_' + str(i) + '_weights.txt','w+'))
        for oc_cnt in range (0, oc):
            for ic_cnt in range (0, ic):
                w_partial_golden[i].write('w channel: [' + str(oc_cnt) + ', ' + str(ic_cnt) + ']\n')
                for row in range (0, kernel_size):
                    for col in range (0, kernel_size):
                        w_partial_golden[i].write(str(format(w_blocks[i][oc_cnt][ic_cnt][row][col], '4d')) + '\t')
                    w_partial_golden[i].write('\n')
        w_partial_golden[i].close()

def write_ref_oas_partial(oa_blocks, name):
    oa_partial_golden=[]
    num_pe = len(oa_blocks)
    oc = oa_blocks[0].shape[0]
    oa_size = oa_blocks[0].shape[1]
    for i in range(0, num_pe):
        oa_partial_golden.append(open('../debug/' + name + '_pe_' + str(i) + '_oa.txt','w+'))
        oa_partial_golden[i].write('oa shape: ' + str(oa_blocks[i].shape[0]) + ' x ' + str(oa_blocks[i].shape[1]) + ' x ' + str(oa_blocks[i].shape[2]) + ']\n')
        for oc_cnt in range (0, oc):
            oa_partial_golden[i].write('oa channel: [' + str(oc_cnt) + ']\n')
            for row in range (0, oa_size):
                for col in range (0, oa_size):
                    oa_partial_golden[i].write(str(format(oa_blocks[i][oc_cnt][row][col], '4d')) + '\t')
                oa_partial_golden[i].write('\n')
        oa_partial_golden[i].close()







