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

def flatten_weight(w_block):
    print w_block.shape
    oc = w_block.shape[0]
    ic = w_block.shape[1]
    kernel_size = w_block.shape[2]
    weight_list = []
    runlength_list = []
    abs_loc_list = [] 
    for oc_cnt_base in range (0, oc/arch.pe_oc): 
        for ic_cnt_base in range (0 , ic/arch.pe_ic): 
            for row in range (0, kernel_size):
                for col in range (0, kernel_size):
                    runlength = 0
                    for oc_cnt in range (0, arch.pe_oc): 
                        for ic_cnt in range (0, arch.pe_ic): 
                            #sparse_w_pe[pe_id][oc_cnt][ic_cnt][row][col] = w_block[oc_cnt_base*arch.pe_oc+oc_cnt+int(pe_id/4)*oc][ic_cnt_base*arch.pe_ic+ic_cnt+int(pe_id%4)*ic][row][col]
                            if(w_block[oc_cnt_base*arch.pe_oc+oc_cnt][ic_cnt_base*arch.pe_ic+ic_cnt][row][col] == 0):
                                if(runlength == 32 or (oc_cnt == arch.pe_oc-1 and ic_cnt == arch.pe_ic-1)):
                                    weight_list.append(0)
                                    runlength_list.append(runlength)
                                    abs_loc_list.append([oc_cnt_base, ic_cnt_base, row, col])
                                    runlength = 1
                                else:
                                    runlength = runlength + 1
                            else:
                                weight_list.append(w_block[oc_cnt_base*arch.pe_oc+oc_cnt][ic_cnt_base*arch.pe_ic+ic_cnt][row][col])
                                runlength_list.append(runlength)
                                abs_loc_list.append([oc_cnt_base, ic_cnt_base, row, col])
                                runlength = 1

    return weight_list, runlength_list, abs_loc_list 

def build_huffman_tables(weight_list, runlength_list, name):
    weights_htree = HuffmanCoding(weight_list)
    weight_list_coded = weights_htree.compress()
    weight_list_decoded = weights_htree.decompress(weight_list_coded)
    weight_codes = weights_htree.get_codes()
    weight_table = weights_htree.get_code_table()
    runlength_htree = HuffmanCoding(runlength_list)
    runlength_list_coded = runlength_htree.compress()
    runlength_list_decoded = runlength_htree.decompress(runlength_list_coded)
    runlength_codes = runlength_htree.get_codes()
    runlength_table= runlength_htree.get_code_table()

    #write huffman table out
    weight_mapping_file = open('../' + name + '_weight_mapping.txt', 'w')
    weight_table_file = open('../' + name + '_weight_table.txt', 'w')
    weight_raw_file = open('../' + name + '_weight_list_raw.txt', 'w')
    weight_coded_file = open('../' + name + '_weight_list_coded.txt', 'w')
    runlength_mapping_file = open('../' + name + '_runlength_mapping.txt', 'w')
    runlength_table_file = open('../' + name + '_runlength_table.txt', 'w')
    runlength_raw_file = open('../' + name + '_runlength_list_raw.txt', 'w')
    runlength_coded_file = open('../' + name + '_runlength_list_coded.txt', 'w')
    for item in weight_list:
      weight_raw_file.write("%s\n" % item)
    for item in weight_list_coded:
      weight_coded_file.write("%s\n" % item)
    for item in runlength_list:
      runlength_raw_file.write("%s\n" % item)
    for item in runlength_list_coded:
      runlength_coded_file.write("%s\n" % item)
    for item in weight_codes:
        weight_mapping_file.write(str(item) + ' ' + str(weight_codes[item]) + '\n')
    for subtree in weight_table:
        for item in subtree:
            if(item ==''):
                weight_table_file.write('00000000000000' + '\n')
            else:
                weight_table_file.write(item + '\n')
    for item in runlength_codes:
        runlength_mapping_file.write(str(item) + ' ' + str(runlength_codes[item]) + '\n')
    for subtree in runlength_table:
        for item in subtree:
            if(item ==''):
                runlength_table_file.write('00000000000000' + '\n')
            else:
                runlength_table_file.write(item + '\n')

    return weight_list_coded, runlength_list_coded 

#def compress_weight(weight_list, runlength_list, pe_id):
#    weights_htree = HuffmanCoding(weight_list, weight_codes)
#    weight_list_coded = weights_htree.compress()
#    weight_list_decoded = weights_htree.decompress(weight_list_coded)
#    weight_codes = weights_htree.get_codes()
#    weight_table = weights_htree.get_code_table()
#    runlength_htree = HuffmanCoding(runlength_list)
#    runlength_list_coded = runlength_htree.compress()
#    runlength_list_decoded = runlength_htree.decompress(runlength_list_coded)
#    runlength_codes = runlength_htree.get_codes()
#    runlength_table= runlength_htree.get_code_table()
#
#    #write huffman table out
#    weight_mapping_file = open('../pe_' + str(pe_id) + '_weight_mapping.txt', 'w')
#    weight_table_file = open('../pe_' + str(pe_id) + '_weight_table.txt', 'w')
#    weight_raw_file = open('../pe_' + str(pe_id) + '_weight_list_raw.txt', 'w')
#    weight_coded_file = open('../pe_' + str(pe_id) + '_weight_list_coded.txt', 'w')
#    runlength_mapping_file = open('../pe_' + str(pe_id) + '_runlength_mapping.txt', 'w')
#    runlength_table_file = open('../pe_' + str(pe_id) + '_runlength_table.txt', 'w')
#    runlength_raw_file = open('../pe_' + str(pe_id) + '_runlength_list_raw.txt', 'w')
#    runlength_coded_file = open('../pe_' + str(pe_id) + '_runlength_list_coded.txt', 'w')
#    for item in weight_list:
#      weight_raw_file.write("%s\n" % item)
#    for item in weight_list_coded:
#      weight_coded_file.write("%s\n" % item)
#    for item in runlength_list:
#      runlength_raw_file.write("%s\n" % item)
#    for item in runlength_list_coded:
#      runlength_coded_file.write("%s\n" % item)
#    for item in weight_codes:
#        weight_mapping_file.write(str(item) + ' ' + str(weight_codes[item]) + '\n')
#    for subtree in weight_table:
#        for item in subtree:
#            if(item ==''):
#                weight_table_file.write('00000000000000' + '\n')
#            else:
#                weight_table_file.write(item + '\n')
#    for item in runlength_codes:
#        runlength_mapping_file.write(str(item) + ' ' + str(runlength_codes[item]) + '\n')
#    for subtree in runlength_table:
#        for item in subtree:
#            if(item ==''):
#                runlength_table_file.write('00000000000000' + '\n')
#            else:
#                runlength_table_file.write(item + '\n')
#
#    return weight_list_coded, runlength_list_coded 

def compress_weight(weight_list, runlength_list, pe_id):
    weights_htree = HuffmanCoding(weight_list)
    weight_list_coded = weights_htree.compress()
    weight_list_decoded = weights_htree.decompress(weight_list_coded)
    weight_codes = weights_htree.get_codes()
    weight_table = weights_htree.get_code_table()
    runlength_htree = HuffmanCoding(runlength_list)
    runlength_list_coded = runlength_htree.compress()
    runlength_list_decoded = runlength_htree.decompress(runlength_list_coded)
    runlength_codes = runlength_htree.get_codes()
    runlength_table= runlength_htree.get_code_table()

    #write huffman table out
    weight_mapping_file = open('../pe_' + str(pe_id) + '_weight_mapping.txt', 'w')
    weight_table_file = open('../pe_' + str(pe_id) + '_weight_table.txt', 'w')
    weight_raw_file = open('../pe_' + str(pe_id) + '_weight_list_raw.txt', 'w')
    weight_coded_file = open('../pe_' + str(pe_id) + '_weight_list_coded.txt', 'w')
    runlength_mapping_file = open('../pe_' + str(pe_id) + '_runlength_mapping.txt', 'w')
    runlength_table_file = open('../pe_' + str(pe_id) + '_runlength_table.txt', 'w')
    runlength_raw_file = open('../pe_' + str(pe_id) + '_runlength_list_raw.txt', 'w')
    runlength_coded_file = open('../pe_' + str(pe_id) + '_runlength_list_coded.txt', 'w')
    for item in weight_list:
      weight_raw_file.write("%s\n" % item)
    for item in weight_list_coded:
      weight_coded_file.write("%s\n" % item)
    for item in runlength_list:
      runlength_raw_file.write("%s\n" % item)
    for item in runlength_list_coded:
      runlength_coded_file.write("%s\n" % item)
    for item in weight_codes:
        weight_mapping_file.write(str(item) + ' ' + str(weight_codes[item]) + '\n')
    for subtree in weight_table:
        for item in subtree:
            if(item ==''):
                weight_table_file.write('00000000000000' + '\n')
            else:
                weight_table_file.write(item + '\n')
    for item in runlength_codes:
        runlength_mapping_file.write(str(item) + ' ' + str(runlength_codes[item]) + '\n')
    for subtree in runlength_table:
        for item in subtree:
            if(item ==''):
                runlength_table_file.write('00000000000000' + '\n')
            else:
                runlength_table_file.write(item + '\n')

    return weight_list_coded, runlength_list_coded 

def build_rram_mem(weight_list_coded, runlength_list_coded, abs_loc_list, pe_id):
    i = 0
    last_abs_loc = [0, 0, 0, -1]
    RRAM_word = ''
    RRAM_word_list = []
    RRAM_word_list_full = []
    #make RRAM words
    while(i < len(weight_list_coded)):
        if(abs_loc_list[i] != last_abs_loc and len(RRAM_word) == 0):
            RRAM_word = str(bindigits(abs_loc_list[i][0], 10)) + str(bindigits(abs_loc_list[i][1], 10)) + str(bindigits(abs_loc_list[i][2], 4)) + str(bindigits(abs_loc_list[i][3], 4)) + '1'
            last_abs_loc = abs_loc_list[i]
        elif(abs_loc_list[i] == last_abs_loc and len(RRAM_word) == 0):
            RRAM_word = '0'
        elif(abs_loc_list[i] != last_abs_loc and len(RRAM_word) != 0):
            #print (RRAM_word)
            RRAM_word = '{message:>96{fill}}'.format(message=RRAM_word, fill='').replace(' ', '0')
            RRAM_word_list.append(RRAM_word)
            #print (RRAM_word + ' padded')
            RRAM_word = ''
        else:
            if(len(RRAM_word) + len(weight_list_coded[i]) + len(runlength_list_coded[i]) <= 96):
                RRAM_word = runlength_list_coded[i][::-1] + weight_list_coded[i][::-1] + RRAM_word
                last_abs_loc = abs_loc_list[i]
                i = i + 1
                if(len(RRAM_word) == 96):
                    RRAM_word_list.append(RRAM_word)
                    RRAM_word = ''
                elif(i == len(weight_list_coded)):
                    RRAM_word = '{message:>96{fill}}'.format(message=RRAM_word, fill='').replace(' ', '0')
                    RRAM_word_list.append(RRAM_word)
                    RRAM_word = ''
            else:
                RRAM_word = (str(runlength_list_coded[i])[::-1] + str(weight_list_coded[i])[::-1])[len(str(weight_list_coded[i]) + str(runlength_list_coded[i]))-(96-len(RRAM_word)):] + RRAM_word
                RRAM_word_list.append(RRAM_word)
                RRAM_word = ''
        
    #RRAM_file = open('RRAM.txt', 'w+')
    for item in RRAM_word_list:
        #RRAM_file[pe_id].write("%s\n" % item)
        if(arch.rram_mode == 1):
            RRAM_word_list_full.append( '0'*64 + str(item[64:96]))
            RRAM_word_list_full.append( '0'*64 + str(item[32:64]))
            RRAM_word_list_full.append( '0'*64 + str(item[0:32]))
        elif(arch.rram_mode == 2):
            RRAM_word_list_full.append( '0'*32 + str(item[32:96]))
            RRAM_word_list_full.append( '0'*64 + str(item[0:32]))
        elif(arch.rram_mode == 3):
            RRAM_word_list_full.append( str(item))

    if((len(RRAM_word_list_full) % arch.rram_banks) != 0):
        if(arch.rram_mode == 1):
            RRAM_word_list.append('0' * 96)
            RRAM_word_list_full.append('0' * 96)
            RRAM_word_list_full.append('0' * 96)
            RRAM_word_list_full.append('0' * 96)
        elif(arch.rram_mode == 2):
            if((len(RRAM_word_list_full) % arch.rram_banks) == 2):
                RRAM_word_list.append('0' * 96)
                RRAM_word_list.append('0' * 96)
                RRAM_word_list_full.append('0' * 96)
                RRAM_word_list_full.append('0' * 96)
                RRAM_word_list_full.append('0' * 96)
                RRAM_word_list_full.append('0' * 96)
            else:
                RRAM_word_list.append('0' * 96)
                RRAM_word_list_full.append('0' * 96)
                RRAM_word_list_full.append('0' * 96)
        elif(arch.rram_mode == 3):
            append_word = arch.rram_banks -(len(RRAM_word_list_full) % arch.rram_banks)
            for i in range(0, append_word):
                RRAM_word_list.append('0' * 96)
                RRAM_word_list_full.append('0' * 96)

    return RRAM_word_list, RRAM_word_list_full

#def build_share_mem(ia, output_kernel_size):
#    ia_words = []
#    for i in range(0, 8192*2):
#        ia_words.append('x'*256)
#
#    print ia.shape
#    print len(ia_words)
#    ic_total = ia.shape[0]
#    ia_size = ia.shape[1]
#    half_window = (output_kernel_size - 1)/2
#    ia_word_total = ''
#    cnt = 0
#    addr = 0
#    for total_ic_cnt in range(0, ic_total/arch.pe_ic):
#        for row in range (half_window, ia_size-half_window):
#            for col in range (half_window, ia_size-half_window):
#                for ic_cnt in range (0, arch.pe_ic):
#                    ia_word_total = str(bindigits(ia[total_ic_cnt*arch.pe_ic+ic_cnt][row][col], 8)) + str(ia_word_total)
#                    cnt = cnt + 1
#                    if(cnt == arch.pe_ic * arch.pe_mult): #16 pixels in a memory word
#                        #print 'ic: ' + str(total_ic_cnt*arch.pe_ic+ic_cnt) + ' row: ' + str(row) + ' col: ' + str(col) + ' addr: ' + str(addr)
#                        ia_words[addr] = ia_word_total
#                        ia_word_total = ''
#                        cnt = 0
#                        addr += 1
#
#    return ia_words

def build_share_mem(ia_list, idx_list):
    ia_words = []
    for i in range(0, 8192*4):
        ia_words.append('x'*256)

    for i in range(0, len(ia_list)):
        ia = ia_list[i]
        idx = idx_list[i]
        ic_total = ia.shape[0]
        ia_size = ia.shape[1]
        ia_word_total = ''
        cnt = 0
        addr = idx * 8192 
        for total_ic_cnt in range(0, ic_total/arch.pe_ic):
            for row in range (0, ia_size):
                for col in range (0, ia_size):
                    for ic_cnt in range (0, arch.pe_ic):
                        ia_word_total = str(bindigits(ia[total_ic_cnt*arch.pe_ic+ic_cnt][row][col], 8)) + str(ia_word_total)
                        cnt = cnt + 1
                        if(cnt == arch.pe_ic * arch.pe_mult): #16 pixels in a memory word
                            #print 'ic: ' + str(total_ic_cnt*arch.pe_ic+ic_cnt) + ' row: ' + str(row) + ' col: ' + str(col) + ' addr: ' + str(addr)
                            ia_words[addr] = ia_word_total
                            ia_word_total = ''
                            cnt = 0
                            addr += 1

    return ia_words

